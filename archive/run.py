from datetime import datetime
from flask import Flask, json, jsonify, g, abort, request
import sqlite3
import hashlib
import random
import time

app = Flask(__name__)
DATABASE = 'app.db'


# fonctions ----------------------------------------------------------------- #

def get_db(only_cursor=False):
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    mycursor = db.cursor()
    return mycursor if only_cursor else (db, mycursor)


def fetchOutput(mycursor, table,
                id=None, table_b=None, match_id=None, dm=False):
    columns = tables[table]
    rule = join_rules[table]
    id_type = 'id' if isinstance(id, int) else match_id
    id_ref = table[0] if table_b is None else table_b[0]

    if id:
        sql_request = '''SELECT {} FROM {} WHERE {}.{} = ?'''.format(
                    ', '.join(columns), rule, id_ref, id_type,)
        mycursor.execute(sql_request, (id, ))
    else:
        sql_request = '''SELECT {} FROM {}'''.format(
                    ', '.join(columns), rule,)
        mycursor.execute(sql_request)

    if isinstance(id, int):
        request_toy = mycursor.fetchone()
        output = {mycursor.description[i][0]:
                  convert(request_toy[i], mycursor.description[i][0],
                          dm, True)
                  for i in range(len(mycursor.description))}
        if table == 'elves' and dm is False:
            del output['illegal']
    else:
        output = [{mycursor.description[i][0]:
                   convert(j[i], mycursor.description[i][0], dm, True)
                   for i in range(len(mycursor.description))}
                  for j in mycursor.fetchall()]
        if table == 'elves' and dm is False:
            for i in output:
                del i['illegal']

    return output


def checkExistingValue(value, column, table, mycursor, error=None):
    sql_request = f'SELECT {column} FROM {table}'
    mycursor.execute(sql_request)
    list_of_values = [i[0] for i in mycursor]
    if value in list_of_values and error == 422:
        print(f'>>> "{value}" already exists in {table}')
        abort(422)
    elif value not in list_of_values and error == 404:
        print('>>> missing value')
        abort(404)
    else:
        return value in list_of_values


def checkExistingColumn(column_name, table, mycursor):
    sql_request = f'SELECT * FROM {table}'
    mycursor.execute(sql_request)
    list_of_columns = [mycursor.description[i][0]
                       for i in range(len(mycursor.description))]
    if column_name not in list_of_columns:
        abort(422)


def deleteItem(mycursor, id, table, db):
    sql_request = f'DELETE FROM {table} WHERE id = ?'
    output = fetchOutput(mycursor, table, id)
    mycursor.execute(sql_request, (id, ))
    db.commit()
    return output


def postItem(values, table, mycursor, db, fk=None):
    columns = templates[table]
    n_values = '?' if len(columns) == 1 else list('?' * len(columns))
    if fk:
        sql_request = 'INSERT INTO {} ({}_id) VALUES ({}, ({}))'.format(
            table, ', '.join(columns), ', '.join(n_values[1:]),
            f'SELECT id FROM {fk} WHERE name = ?')
    else:
        sql_request = 'INSERT INTO {} ({}) VALUES ({})'.format(
            table, ', '.join(columns), ', '.join(n_values))
    mycursor.execute(sql_request, tuple(values.values()))
    db.commit()
    return mycursor.lastrowid


def updateItem(data, id, table, mycursor, db):
    for i, j in data.items():
        checkExistingColumn(i, table, mycursor)
        sql_request = f'UPDATE {table} SET {i} = ? WHERE id = ?'
        mycursor.execute(sql_request, (j, id, ))
    db.commit()


def scheduleMaster(mycursor, db, last_id):
    elves_quantity = mycursor.execute(
        'SELECT id FROM elves ORDER BY id DESC LIMIT 1').fetchone()[0]
    elf_id = random.randrange(1, elves_quantity + 1)
    sql_request = '''INSERT INTO schedules (done, done_at, elf_id, wish_id)
                    VALUES (?, ?, ?, ?)'''
    values = ('false', None, elf_id, last_id,)
    mycursor.execute(sql_request, values)
    db.commit()


def checkCredentials(mycursor, username, pswd):
    elves_credentials = mycursor.execute(
        'SELECT login, password FROM elves').fetchall()
    elves_dict = {elves_credentials[i][0]: elves_credentials[i][1]
                  for i in range(len(elves_credentials))}
    if username not in elves_dict.keys():
        abort(404)
    return elves_dict[username] == pswd


def convert(value, optional_value=None, dm=False, func=False):
    mycursor = get_db(True)
    value = str(value)
    if optional_value == 'price' and dm is True:
        return int(value)  # int(int(value) * 1.1)
    elif optional_value == 'password' and func is False:
        return hashlib.md5(value.encode('utf-8')).hexdigest()
    elif optional_value == 'category' and func is False:
        return mycursor.execute('SELECT id from categories WHERE name = ?',
                                (value,)).fetchone()[0]
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
toy_validator = sorted(templates['toys'])
elf_validator = sorted(templates['elves'])
wishes_validator = sorted(templates['wishes'])


# categories ---------------------------------------------------------------- #

@app.route('/categories', methods=['GET', 'POST'])
def index_categories():
    db, mycursor = get_db()
    table = 'categories'
    data = request.form.to_dict()

    if request.method == 'POST':
        if 'name' in data:
            checkExistingValue((data['name']), 'name', table, mycursor, 422)
            item = postItem(data, table, mycursor, db)
            return jsonify(fetchOutput(mycursor, table, item))
        else:
            abort(422)
    else:
        return jsonify(fetchOutput(mycursor, table))


@app.route('/categories/<cat_id>', methods=['GET', 'PUT', 'DELETE'])
def show_categories(cat_id):
    db, mycursor = get_db()
    table = 'categories'
    data = request.form.to_dict()
    cat_id = int(cat_id)
    checkExistingValue(cat_id, 'id', table, mycursor, 404)

    if request.method == 'DELETE':
        item = deleteItem(mycursor, cat_id, table, db)
        return jsonify(item)
    elif request.method == 'PUT':
        updateItem(data, cat_id, table, mycursor, db)
    return jsonify(fetchOutput(mycursor, table, cat_id))


# toys ---------------------------------------------------------------------- #

@app.route('/toys', methods=['GET', 'POST'])
def index_toys():
    db, mycursor = get_db()
    table = 'toys'
    data = {i: convert(j) for i, j in request.form.to_dict().items()}

    if request.method == 'POST':
        if sorted([i for i in data.keys()]) == toy_validator and\
                checkExistingValue(data['category'], 'name',
                                   'categories', mycursor):
            checkExistingValue(data['name'], 'name', table, mycursor, 422)
            item = postItem(data, table, mycursor, db, 'categories')
            return jsonify(fetchOutput(mycursor, table, item))
        else:
            abort(422)
    else:
        return jsonify(fetchOutput(mycursor, table, dm=True))


@app.route('/toys/<toy_id>', methods=['GET', 'PUT', 'DELETE'])
def show_toys(toy_id):
    db, mycursor = get_db()
    table = 'toys'
    data = {convert(i): convert(j, i) for i, j
            in request.form.to_dict().items()}
    toy_id = int(toy_id)
    checkExistingValue(toy_id, 'id', table, mycursor, 404)

    if request.method == 'DELETE':
        item = deleteItem(mycursor, toy_id, table, db)
        return jsonify(item)
    elif request.method == 'PUT':
        updateItem(data, toy_id, table, mycursor, db)
        return jsonify(fetchOutput(mycursor, table, toy_id))
    return jsonify(fetchOutput(mycursor, table, toy_id, dm=True))


@app.route('/categories/<name>/toys')
def toys_per_categories(name):
    mycursor = get_db(True)
    checkExistingValue(name, 'name', 'categories', mycursor, 404)

    return jsonify(fetchOutput(mycursor, 'toys', name, 'categories', 'name'))

# elves --------------------------------------------------------------------- #


@app.route('/elves', methods=['GET', 'POST'])
def index_elves():
    db, mycursor = get_db()
    table = 'elves'
    data = {i: convert(j, i) for i, j in request.form.to_dict().items()}
    data['illegal'] = 'true' if data.get('illegal') else 'false'

    if request.method == 'POST':
        if sorted([i for i in data.keys()]) == elf_validator:
            checkExistingValue(data['login'], 'login', table, mycursor, 422)
            item = postItem(data, table, mycursor, db)
            return jsonify(fetchOutput(mycursor, table, item, dm=True))
        else:
            abort(422)
    else:
        return jsonify(fetchOutput(mycursor, table))


@app.route('/elves/<elf_id>', methods=['GET', 'PUT', 'DELETE'])
def show_elves(elf_id):
    db, mycursor = get_db()
    table = 'elves'
    elf_id = int(elf_id)
    data = {i: convert(j, i) for i, j in request.form.to_dict().items()}
    checkExistingValue(elf_id, 'id', table, mycursor, 404)

    if request.method == 'DELETE':
        output = fetchOutput(mycursor, table, elf_id)
        deleteItem(mycursor, elf_id, table, db)
        return jsonify(output)
    elif request.method == 'PUT':
        updateItem(data, elf_id, table, mycursor, db)
        return jsonify(fetchOutput(mycursor, table, elf_id, dm=True))

    if fetchOutput(mycursor, table, elf_id, dm=True).get('illegal'):
        abort(404)
    else:
        return jsonify(fetchOutput(mycursor, table, elf_id))

# wishes -------------------------------------------------------------------- #


@app.route('/wishes', methods=['GET', 'POST'])
def show_wishes():
    db, mycursor = get_db()
    table = 'wishes'
    data = request.form

    if request.method == 'POST':
        if sorted([i for i in data.keys()]) == wishes_validator and\
                checkExistingValue(data['toy'], 'name', 'toys', mycursor):
            item = postItem(data, table, mycursor, db, 'toys')
            scheduleMaster(mycursor, db, item)
            return jsonify(fetchOutput(mycursor, table, item))
        else:
            abort(422)

    return jsonify(fetchOutput(mycursor, table))

# schedules ----------------------------------------------------------------- #


@app.route('/schedules')
def show_schedules():
    mycursor = get_db(True)
    table = 'schedules'
    args = {i: convert(j, i) for i, j in request.args.items()}

    if 'login' in args and 'password' in args:
        if checkCredentials(mycursor, args['login'], args['password']):
            return jsonify(fetchOutput(mycursor, table, args['login'],
                                       'elves', 'login'))
    return jsonify({'error': 'The resource could not be found.'})


@app.route('/schedules/<wish_id>/done', methods=['PUT'])
def get_done(wish_id):
    db, mycursor = get_db()
    table = 'schedules'
    wish_id = int(wish_id)
    data = {'done': 'true', 'done_at': datetime.now()}
    checkExistingValue(wish_id, 'id', table, mycursor, 404)

    updateItem(data, wish_id, table, mycursor, db)
    return jsonify(fetchOutput(mycursor, table, wish_id))


if __name__ == '__main__':
    app.run(debug=True)
