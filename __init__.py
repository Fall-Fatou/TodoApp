'''from flask import Flask

app = Flask(__name__)

from .todo import todo


# Registering blueprints
app.register_blueprint(todo.todo_bp, url_prefix='/todolist')
'''