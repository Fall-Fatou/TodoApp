import pymongo
from datetime import datetime
from bson import ObjectId
from flask import Flask, render_template, request, url_for, redirect, session
import bcrypt
# from todo.todo import todo_bp

app = Flask(__name__)
app.secret_key = "testing"
# app.register_blueprint(todo_bp, url_prefix='/todolist')

# mongodb configuration - Remote database

client = pymongo.MongoClient("mongodb+srv://72046:zTOtdyBLxI544XEt@cluster0.dk1cjbn.mongodb.net/?retryWrites=true&w=majority")

# database:
db = client.flask_db
# collections:
todos = db.todos
records = db.register
"""
Define a route to handle requests to the homepage
"""
@app.route("/", methods=['post', 'get'])
def index():
    # initialize a message variable
    message = ''
    # check if user is logged in
    if "email" not in session:
        # redirect user to login page if not logged in
        return redirect(url_for("login"))
    # Fetch todos from the database and sort by degree
    todos = db.todos.find().sort('degree', 1)

    # Render the template and pass the todos and current UTC datetime to the template
    return render_template('todolist.html', todos=todos, utc_dt=datetime.utcnow())

"""
Define a route to handle requests to the registration page
"""
@app.route("/register/", methods=['post', 'get'])
def register():
    message = '' # initialize a message variable
    if "email" in session: # check if user is already logged in
        return redirect(url_for("logged_in")) # redirect user to logged in page if already logged in
    if request.method == "POST":  # check if form has been submitted
        # Fetch user inputs from the form
        user = request.form.get("fullname")
        email = request.form.get("email")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        # Check if user or email already exists in the database
        user_found = records.find_one({"name": user})
        email_found = records.find_one({"email": email})

        if user_found:  # check if user already exists
            message = 'There already is a user by that name'
            return render_template('register.html', message=message)

        if email_found:  # check if email already exists
            message = 'This email already exists in database'
            return render_template('register.html', message=message)

        if password1 != password2:  # check if password matches
            message = 'Passwords should match!'
            return render_template('register.html', message=message)
        else:
            # Hash the password using bcrypt and insert the user's data into the database
            hashed = bcrypt.hashpw(password2.encode('utf-8'), bcrypt.gensalt())
            user_input = {'name': user, 'email': email, 'password': hashed}
            records.insert_one(user_input)

            # Fetch the user's data from the database and render the logged in page
            user_data = records.find_one({"email": email})
            new_email = user_data['email']
            return render_template('logged_in.html', email=new_email)

    # Render the registration template
    return render_template('register.html')


"""
Route for the About page
"""
@app.route('/about/')
def about():
    # Initialize message variable
    message = ''
    # Check if user is logged in
    if "email" not in session:
        # If not, redirect to login page
        return redirect(url_for("login"))

    # If user is logged in, render the About page
    return render_template('about.html')

"""
Route for the Login page
"""
@app.route("/login/", methods=["POST", "GET"])
def login():
    # Initialize message variable
    message = 'Please login to your account'
    # Check if user is already logged in
    if "email" in session:
        # If yes, redirect to the logged in page
        return redirect(url_for("logged_in"))

    # If user is not logged in, check if login form is submitted
    if request.method == "POST":
        # Get email and password from login form
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if email exists in the database
        email_found = records.find_one({"email": email})
        if email_found:
            # If email exists, get email and password from the database
            email_val = email_found['email']
            passwordcheck = email_found['password']

            # Check if password is correct
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                # If password is correct, log the user in and redirect to the logged in page
                session["email"] = email_val
                return redirect(url_for('logged_in'))
            else:
                # If password is incorrect, show error message and render login page
                if "email" in session:
                    return redirect(url_for("logged_in"))
                message = 'Wrong password'
                return render_template('login.html', message=message)
        else:
            # If email is not found in the database, show error message and render login page
            message = 'Email not found'
            return render_template('login.html', message=message)
    # If login form is not submitted, render the login page with message variable
    return render_template('login.html', message=message)


"""
Route for the logged in page
"""
@app.route('/logged_in/')
def logged_in():
    # Check if user is logged in
    if "email" in session:
        # If yes, get email from session and render the logged in page
        email = session["email"]
        return render_template('logged_in.html', email=email)
    else:
        # If user is not logged in, redirect to the login page
        return redirect(url_for("login"))


"""
Logout Route
"""
@app.route("/logout/", methods=["POST", "GET"])
def logout():
    # Check if user is logged in
    if "email" in session:
        # Remove user's email from the session
        session.pop("email", None)
        # Render the sign out page
        return render_template("sign_out.html")
    else:
        # If user is not logged in, redirect to the index page
        return render_template('index.html')

"""
To-Do List Route
"""
@app.route('/todolist/', methods=('GET', 'POST'))
def todolist():
    message = ''
    # Check if user is logged in
    if "email" not in session:
        # If user is not logged in, redirect to the login page
        return redirect(url_for("login"))
    # Handle form submission
    if request.method == 'POST':
        # Get form data
        content = request.form['content']
        due_date = request.form['due_date']
        degree = request.form['degree']
        # Insert new to-do item into the database
        todos.insert_one({'content': content, 'due_date': due_date, 'degree': degree, 'completed': False,
                          'created_at': datetime.utcnow()})
        # Redirect to the to-do list page
        return redirect(url_for('todolist'))

    # Retrieve all to-do items from the database and sort them by degree and creation date
    all_todos = todos.find().sort([('degree', pymongo.ASCENDING), ('created_at', pymongo.DESCENDING)])
    # Render the to-do list page with the retrieved items
    return render_template('todolist.html', todos=all_todos)

"""
Complete To-Do Route
"""
@app.post('/<id>/complete_todo')
def complete_todo(id):
    # Update the completed field of the specified to-do item in the database
    todos.update_one({'_id': ObjectId(id)}, {'$set': {'completed': True}})
    # Redirect to the to-do list page
    return redirect(url_for('todolist'))

"""
Delete To-Do Route
"""
@app.post('/<id>/delete')
def delete(id):
    # Delete the specified to-do item from the database
    todos.delete_one({"_id": ObjectId(id)})
    # Redirect to the to-do list page
    return redirect(url_for('todolist'))

if __name__ == '__main__':
    app.run()