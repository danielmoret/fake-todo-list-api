"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
import json
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap, is_valid_task
from admin import setup_admin
from models import db, User, Todo

# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False


todo_file_path = os.path.join(os.path.dirname(__file__), 'todos.json')

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object

todo_file_path = os.path.join(os.path.dirname(__file__), 'todos.json')

def save_todos(todos):
    with open(todo_file_path, 'w') as f:
        json.dump(todos, f, indent=4)

def read_todos():
    with open(todo_file_path, 'r') as f:
        return json.load(f)

@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/todos/user', methods=['GET'])
def get_all_users():
    todos = read_todos()
    users = [todo["username"] for todo in todos]
    return jsonify(users), 200


@app.route('/todos/user/<string:username>', methods=['POST'])
def create_user(username=None):
   
   data = request.json
   print(type(data))
   if type(data) == list and len(data) == 0:
        todos = read_todos()
        for todo in todos:
            if todo["username"] == username:
                return jsonify({"msg": f"The user {username} already exists"}), 400
            
        new_user = {"username": username, "todos": [{"label": "sample task", "done": False}]}
        todos.append(new_user)
        save_todos(todos)
        return jsonify([]), 201
   else:
        return jsonify({"message": "You must add an empty array in the body of the request"}), 500


@app.route('/todos/user/<string:username>', methods=['GET'])
def get_all_todo(username=None):
    todos= read_todos()

    user_todos = [todo["todos"] for todo in todos if todo["username"] == username]

    if not user_todos:
        return jsonify({"msg": f"The user {username} doesn't exist"}), 404
    return jsonify(user_todos), 200


@app.route('/todos/user/<string:username>', methods=['PUT'])
def update_task(username=None):
    data = request.json

    if not data or not isinstance(data, list):
        return jsonify({"msg": "You must send a valid JSON array of tasks"}), 400
    
    for task in data:
        if not is_valid_task(task):
            return jsonify({"msg": "Each task must have 'label' (string) and 'done' (boolean) properties"}), 400
    
    todos = read_todos()
    user_todos = [todo for todo in todos if todo["username"] == username]

    if not user_todos:
        return jsonify({"msg": f"The user {username} doesn't exist"}), 404
    
    user_todos[0]["todos"] = data
    save_todos(todos)

    return jsonify({"msg": f"{len(data)} todos have been updated successfully"}),200



@app.route('/todos/user/<string:username>', methods=['DELETE'])
def delete_task(username=None):
    todos = read_todos()
    user_index = [i for i, todo in enumerate(todos) if todo["username"] == username]
   
    if not user_index:
        return jsonify({"msg": f"The user {username} doesn't exist"}), 404

    todos.pop(user_index[0])
    save_todos(todos)

    return jsonify({"msg": f"The user {username} has been deleted successfully"}), 200

    # this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
