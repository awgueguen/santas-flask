from datetime import datetime
from flask import Flask, jsonify, g, abort, request
from methods import *

app = Flask(__name__)
DATABASE = 'app.db'

templates = {
    'categories': ['name'],
    'toys': ['name', 'description', 'price', 'category'],
    'elves': {'first_name', 'last_name', 'login', 'password', 'illegal'},
    'wishes': ['child_name', 'toy']
}

toy_validator = sorted(templates['toys'])
# elf_validator = sorted(templates['elves'])
wishes_validator = sorted(templates['wishes'])
# TODO: remove all sorted from the code


# categories ---------------------------------------------------------------- #

@app.route('/categories', methods=['GET', 'POST'])
def index_categories():
    table, db, mycursor = get_db(request.path)
    data = request.form

    if request.method == 'POST':
        checkExistingValue((data.get('name')), 'name', table, mycursor, 422)
        return postItem(data, table, mycursor, db)
    else:
        return jsonify(fetchOutput(mycursor, table))


@app.route('/categories/<cat_id>', methods=['GET', 'PUT', 'DELETE'])
def show_categories(cat_id):
    cat_id = int(cat_id)
    table, db, mycursor = get_db(request.path)
    data = request.form

    checkExistingValue(cat_id, 'id', table, mycursor, 404)

    if request.method == 'DELETE':
        return deleteItem(mycursor, cat_id, table, db)
    elif request.method == 'PUT':
        return updateItem(data, cat_id, table, mycursor, db)
    else:
        return jsonify(fetchOutput(mycursor, table, cat_id))


# toys ---------------------------------------------------------------------- #

@app.route('/toys', methods=['GET', 'POST'])
def index_toys():
    table, db, mycursor = get_db(request.path)
    table = 'toys'
    data = {i: convert(j) for i, j in request.form.items()}
    data_check = sorted(list(data.keys()))

    if request.method != 'POST':
        return jsonify(fetchOutput(mycursor, table, dm=True))
    if (data_check == toy_validator and checkExistingValue(
            data['category'], 'name', 'categories', mycursor)):
        checkExistingValue(data['name'], 'name', table, mycursor, 422)
        return postItem(data, table, mycursor, db, 'categories')
    else:
        abort(422)


@app.route('/toys/<toy_id>', methods=['GET', 'PUT', 'DELETE'])
def show_toys(toy_id):
    toy_id = int(toy_id)
    table, db, mycursor = get_db(request.path)
    data = {convert(i): convert(j, i) for i, j in request.form.items()}

    checkExistingValue(toy_id, 'id', table, mycursor, 404)

    if request.method == 'DELETE':
        return deleteItem(mycursor, toy_id, table, db)
    elif request.method == 'PUT':
        return updateItem(data, toy_id, table, mycursor, db)
    else:
        return jsonify(fetchOutput(mycursor, table, toy_id, dm=True))


@app.route('/categories/<name>/toys')
def toys_per_categories(name):
    mycursor = get_db(only_cursor=True)
    checkExistingValue(name, 'name', 'categories', mycursor, 404)

    return jsonify(fetchOutput(mycursor, 'toys', name, 'categories', 'name'))

# elves --------------------------------------------------------------------- #


@app.route('/elves', methods=['GET', 'POST'])
def index_elves():
    table, db, mycursor = get_db(request.path)
    data = {i: convert(j, i) for i, j in request.form.items()}
    data['illegal'] = 'true' if data.get('illegal') else 'false'

    if request.method != 'POST':
        return jsonify(fetchOutput(mycursor, table))
    if set(data.keys()) == templates[table]:
        checkExistingValue(data['login'], 'login', table, mycursor, 422)
        postItem(data, table, mycursor, db)
        return fetchOutput(mycursor, table, mycursor.lastrowid, dm=True)
    else:
        abort(422)


@app.route('/elves/<elf_id>', methods=['GET', 'PUT', 'DELETE'])
def show_elves(elf_id):
    elf_id = int(elf_id)
    table, db, mycursor = get_db(request.path)
    data = {i: convert(j, i) for i, j in request.form.items()}
    checkExistingValue(elf_id, 'id', table, mycursor, 404)

    if request.method == 'DELETE':
        return deleteItem(mycursor, elf_id, table, db)
    elif request.method == 'PUT':
        updateItem(data, elf_id, table, mycursor, db)
        return fetchOutput(mycursor, table, elf_id, dm=True)

    if fetchOutput(mycursor, table, elf_id, dm=True).get('illegal'):
        abort(404)
    else:
        return jsonify(fetchOutput(mycursor, table, elf_id))

# wishes -------------------------------------------------------------------- #


@app.route('/wishes', methods=['GET', 'POST'])
def show_wishes():
    table, db, mycursor = get_db(request.path)
    data = request.form
    data_check = sorted(list(data.keys()))

    if request.method != 'POST':
        return jsonify(fetchOutput(mycursor, table))
    if (data_check == wishes_validator and checkExistingValue(
            data['toy'], 'name', 'toys', mycursor)):
        postItem(data, table, mycursor, db, 'toys')
        scheduleMaster(mycursor, db, mycursor.lastrowid)
        return jsonify(fetchOutput(mycursor, table, mycursor.lastrowid))
    else:
        abort(422)

# schedules ----------------------------------------------------------------- #


@app.route('/schedules')
def show_schedules():
    table, db, mycursor = get_db(request.path)
    table = 'schedules'
    args = {i: convert(j, i) for i, j in request.args.items()}

    if checkCredentials(mycursor, args.get('login'), args.get('password')):
        return jsonify(
            fetchOutput(mycursor, table, args['login'], 'elves', 'login'))
    else:
        return jsonify({'error': 'The resource could not be found.'})


@app.route('/schedules/<wish_id>/done', methods=['PUT'])
def get_done(wish_id):
    wish_id = int(wish_id)
    table, db, mycursor = get_db(request.path)
    data = {'done': 'true', 'done_at': datetime.now()}

    checkExistingValue(wish_id, 'id', table, mycursor, 404)
    return updateItem(data, wish_id, table, mycursor, db)


if __name__ == '__main__':
    app.run(debug=True)
