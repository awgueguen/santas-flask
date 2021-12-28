from flask import Flask, jsonify, g, abort, request
import sqlite3
import hashlib
import random

app = Flask(__name__)
DATABASE = 'app.db'


def get_db(path=None, only_cursor=False):
    """Returns the current table, the db & a cursor

    Args:
        path (var, optional): `request.path`
        only_cursor (bool, optional): `True` if only the cursor is needed
        Defaults to False.

    Returns:
        str: table name, e.g. `'elves'`
        db: current db
        cursor: a cursor
    """
    db = getattr(g, '_database', None)

    # get the table name using the route path
    table = path[1:] if path is not None else ''
    table = table[:table.index('/')] if '/' in table else table

    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    mycursor = db.cursor()
    return mycursor if only_cursor else (table, db, mycursor)


def fetchOutput(mycursor, table,
                id=None, table_b=None, match_id=None, dm=False):
    """Go fetch the needed output, returns a non jsonified result

    Args:
        mycursor (cursor): cursor returned by `get_db()`
        table (str): table name as a string
        id (str or int, optional): define a SQL `WHERE col = ?` condition
        table_b (str, optional): specify the name of a 2nd table to `JOIN`
        match_id (str, optional): use if you need to match with something
        else other than the usual `SQL 'id'`. e.g. `'name'`
        dm (bool, optional): `True` to activate Dirty Money

    Returns:
        list or dict: all the informations of an item/multiple items
    """
    columns = tables[table]
    rule = join_rules[table]
    # define the matching condition
    id_type = 'id' if isinstance(id, int) else match_id
    # define the matching condition table
    id_ref = table[0] if table_b is None else table_b[0]

    if id:
        # generate the sql request according to multiple var
        # first {} for attributes, second for table, last two for condition
        sql_request = '''SELECT {} FROM {} WHERE {}.{} = ?'''.format(
                    ', '.join(columns), rule, id_ref, id_type,)
        mycursor.execute(sql_request, (id, ))
    else:
        sql_request = '''SELECT {} FROM {}'''.format(
                    ', '.join(columns), rule,)
        mycursor.execute(sql_request)

    # execute SQL request, one to ouput a single dict, the second for a list
    if isinstance(id, int):
        request_toy = mycursor.fetchone()
        output = {mycursor.description[i][0]:
                  convert(request_toy[i], mycursor.description[i][0],
                          dm, True)
                  for i in range(len(mycursor.description))}
        # delete the illegal attribute of elves if needed
        if table == 'elves' and dm is False:
            del output['illegal']
    else:
        output = [{mycursor.description[i][0]:
                   convert(j[i], mycursor.description[i][0], dm, True)
                   for i in range(len(mycursor.description))}
                  for j in mycursor.fetchall()]
        # delete the illegal attribute or an entire elf if needed
        if table == 'elves' and dm is False:
            tmp = []
            for i in output:
                if i['illegal'] == 'false':
                    del i['illegal']
                    tmp.append(i)
            output = tmp

    return output


def checkExistingValue(value, column, table, mycursor, error=None):
    """Check if a value exist in certain conditions, can raise
    an error if needed

    Args:
        value (str, int): the checked value
        column (str): column where the value is supposedly stored
        table (str): table where the value is supposedly stored
        mycursor (cursor): cursor returned by `get_db()`
        error (int, optional): the type of error returned. Defaults to None.

    Returns:
        boolean: `True` if exists
    """
    sql_request = f'SELECT {column} FROM {table}'
    mycursor.execute(sql_request)
    list_of_values = [i[0] for i in mycursor]
    # raise errors according to specific situations
    if value in list_of_values and error == 422:
        print(f'>>> "{value}" already exists in {table}')
        abort(422)
    elif value not in list_of_values and error == 404:
        print('>>> missing value')
        abort(404)
    else:
        return value in list_of_values


def checkExistingColumn(column_name, table, mycursor):
    """Check if a attribute exists in the specified table, raise `422`

    Args:
        column_name (str): the value we want to check
        table (str): table where we want to check the attribute
        mycursor (cursor): cursor returned by `get_db()`
    """
    sql_request = f'SELECT * FROM {table}'
    mycursor.execute(sql_request)
    list_of_columns = [mycursor.description[i][0]
                       for i in range(len(mycursor.description))]
    if column_name not in list_of_columns:
        abort(422)


def deleteItem(mycursor, id, table, db):
    """Delete the requested item from the specified table

    Args:[description]
        mycursor (cursor): cursor returned by `get_db()`
        id (int): specify the item's id
        table (str): the item's table
        db (db): db returned by `get_db()`

    Returns:
        dict: return in `JSON` format the deleted item
    """
    sql_request = f'DELETE FROM {table} WHERE id = ?'
    output = fetchOutput(mycursor, table, id)
    mycursor.execute(sql_request, (id, ))
    db.commit()
    return jsonify(output)


def postItem(values, table, mycursor, db, fk=None):
    """Create an item, used with `-X POST`

    Args:
        values (dict): list of all values and their attributes
        table (str): table in which we create the item
        mycursor (cursor): cursor returned by `get_db()`
        db (db): db returned by `get_db()`
        fk (str, optional): specify if there's a foreign key. Defaults to None.

    Returns:
        dic: return in `JSON` format the created item
    """
    columns = templates[table]
    # order value according to template
    values_ordered = {columns[i]: values[columns[i]]
                      for i in range(len(columns))}
    # define number of '?' needed for the SQL execute
    n_values = '?' if len(columns) == 1 else list('?' * len(columns))
    if fk:
        sql_request = 'INSERT INTO {} ({}_id) VALUES ({}, ({}))'.format(
            table, ', '.join(columns), ', '.join(n_values[1:]),
            f'SELECT id FROM {fk} WHERE name = ?')
    else:
        sql_request = 'INSERT INTO {} ({}) VALUES ({})'.format(
            table, ', '.join(columns), ', '.join(n_values))
    mycursor.execute(sql_request, tuple(values_ordered.values()))
    db.commit()
    return jsonify(fetchOutput(mycursor, table, mycursor.lastrowid))


def updateItem(data, id, table, mycursor, db):
    """Update an item, used with `-X PUT`

    Args:
        data (dic): new set of values
        id (int): the item which will be updated
        table (str): the table containing the item
        mycursor (cursor): cursor returned by `get_db()`
        db (db): db returned by `get_db()`

    Returns:
        dict: return in `JSON` format the updated item
    """
    for i, j in data.items():
        # check if the sent attribute exist in the updated item
        checkExistingColumn(i, table, mycursor)
        sql_request = f'UPDATE {table} SET {i} = ? WHERE id = ?'
        mycursor.execute(sql_request, (j, id, ))
    db.commit()
    return jsonify(fetchOutput(mycursor, table, id))


def scheduleMaster(mycursor, db, last_id):
    """Function used to create a schedule entry alongside a wish

    Args:
        mycursor (cursor): cursor returned by `get_db()`
        db (db): db returned by `get_db()`
        last_id (int): last wish id created
    """
    elves_quantity = mycursor.execute(
        'SELECT id FROM elves ORDER BY id DESC LIMIT 1').fetchone()[0]
    elf_id = random.randrange(1, elves_quantity + 1)
    # return the number of elves an pick one using random.randrange
    sql_request = '''INSERT INTO schedules (done, done_at, elf_id, wish_id)
                    VALUES (?, ?, ?, ?)'''
    # set default values
    values = ('false', None, elf_id, last_id,)
    mycursor.execute(sql_request, values)
    db.commit()


def checkCredentials(mycursor, username, pswd):
    """Check if the elf username & password are correct
    otherwise raise a 404 error

    Args:
        mycursor (cursor): cursor returned by `get_db()`
        username (str): elf login
        pswd (str): elf password already hashed

    Returns:
        boolean: `True` if the credentials are correct
    """
    elves_credentials = mycursor.execute(
        'SELECT login, password FROM elves').fetchall()
    # return a dict containing all logins & passwords associated as key/value
    elves_dict = {elves_credentials[i][0]: elves_credentials[i][1]
                  for i in range(len(elves_credentials))}
    if username not in elves_dict.keys():
        abort(404)
    return elves_dict[username] == pswd


def convert(value, optional_value=None, dm=False, func=False):
    """Use this tool to convert a value according to certain rules

    Args:
        value (free): the value to convert
        optional_value (str, optional): second value, often the attribute,
        use to convert the principal value, e.g `password`. Defaults to None.
        dm (bool, optional): `True` to activate Dirty Money. Defaults to False.
        func (bool, optional): `True` for partial conversion, using only the
        value. Defaults to False.

    Returns:
        free: the converted value
    """
    mycursor = get_db(only_cursor=True)
    value = str(value)
    if optional_value == 'price' and dm is True:
        return int(int(value) * 0.9)
    elif optional_value == 'password' and func is False:
        # not used if func True
        # convert str to md5 password
        return hashlib.md5(value.encode('utf-8')).hexdigest()
    elif optional_value == 'category' and func is False:
        # not used if func True
        return mycursor.execute('SELECT id from categories WHERE name = ?',
                                (value,)).fetchone()[0]
    elif optional_value == 'illegal' and value == 'true' and dm is False:
        return 'true'
    elif optional_value == 'illegal' and value == 'false' and dm is False:
        return 'false'
    elif value.isdigit():
        return int(value)
    elif value == 'category':
        return 'category_id'
    elif value == 'false':
        return False
    elif value == 'true':
        return True
    elif value == "None":
        return None
    else:
        return value


templates = {
    'categories': ['name'],
    'toys': ['name', 'description', 'price', 'category'],
    'elves': ['first_name', 'last_name', 'login', 'password', 'illegal'],
    'wishes': ['child_name', 'toy']
}
tables = {
    'toys': ['t.id', 't.name', 't.description', 't.price',
             'c.name as category'],
    'categories': ['c.id', 'c.name'],
    'elves': ['e.id', 'e.first_name', 'e.last_name', 'e.login', 'e.password',
              'e.illegal'],
    'wishes': ['w.id', 'w.child_name', 't.name as toy'],
    'schedules': ['s.id', 's.done', 's.done_at', 'e.login as elf', 's.wish_id']
}
join_rules = {
    'toys': 'toys as t LEFT JOIN categories as c ON t.category_id = c.id',
    'categories': 'categories as c',
    'elves': 'elves as e',
    'wishes': 'wishes as w LEFT JOIN toys as t ON w.toy_id = t.id',
    'schedules': 'schedules as s LEFT JOIN elves as e ON s.elf_id = e.id'
}
