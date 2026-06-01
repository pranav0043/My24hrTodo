import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///data.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

def login_required(f):
    """
    Decorate routes to require login. http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html",message="must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html",message="must provide password")

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return render_template("error.html",message="invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods= ["GET", "POST"])
def register():
    """Register user"""
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm_password = request.form.get("confirmation")

        if not username:
           return render_template("error.html",message="must provide username")
        if not password:
           return render_template("error.html",message="must provide password")

        if password != confirm_password:
            return render_template("error.html",message="Passwords do not match. Please re-enter.")
        else:
            hashed_password = generate_password_hash(password)
            exsisting_user = db.execute(
                "SELECT * FROM users WHERE username = ?", username
            )
            if exsisting_user:
                return render_template("error.html",message=
                    "Username already exists. Please choose a different one."
                )
            else:
                db.execute(
                    "INSERT INTO users (username, hash) VALUES (?, ?)",
                    username,
                    hashed_password,
                )
                return redirect("/login")

    return render_template("register.html")

@app.route("/todo", methods=["GET", "POST"])
def todo():
    if request.method == "POST":
        if "user_id" in session:
            try:
                username = session["user_id"]
                todo = request.form.get("todo")  # Assuming your form field is named "todo"

                if todo:
                    # Insert the new TODO item associated with the logged-in user
                    db.execute("INSERT INTO data (user_id, todo) VALUES (?, ?)", username, todo)
                    flash("Task added successfully!","success")
                    redirect("/todo")

                # Fetch TODO items for the logged-in user from the database after insertion
                todo_items = db.execute("SELECT todo FROM data WHERE user_id = ?", username)
                return render_template("todo.html", todo_items=todo_items)

            except Exception as e:
                return render_template("todo.html", todo_items=[])
    else:
        if "user_id" in session:
            username = session["user_id"]
            # Fetch TODO items for the logged-in user from the database
            todo_items = db.execute("SELECT todo FROM data WHERE user_id = ?", username)
            return render_template("todo.html", todo_items=todo_items)

@app.route('/remove_todo', methods=['POST'])
def remove_todo():
    username = session["user_id"]
    # Remove a specific TODO item for a particular user_id
    db.execute("SELECT todo FROM data WHERE user_id=?",username)
    db.execute("DELETE FROM data WHERE user_id = :user_id ", user_id=username)
    return redirect('/todo')


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

