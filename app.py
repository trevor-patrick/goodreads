import os
import sys
import sha3

from flask import Flask, render_template, request, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

engine = create_engine('postgres://olxpdkjidxzijo:6c0ff6d277bd117d6e615144dab8b3fe26e190e0788c30c9aa4c6de74076af2d@ec2-54-235-242-63.compute-1.amazonaws.com:5432/d25m2jqruo7e1o')
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=['POST', 'GET'])
def index():
    if request.method == "GET":
        return render_template("index.html")

    if request.method == "POST":
        username = request.form.get("Username")
        hashed_pass = sha3.sha3_224(str(request.form.get("Password")).encode('utf-8')).hexdigest()
        check = db.execute("SELECT * FROM accounts WHERE username = :username AND password = :password", {"username": request.form.get("Username"), "password": hashed_pass}).fetchone()

        if check is None:
            message = "Incorrect username or password"
            return render_template("index.html", result = message)
        else:
            session["username"] = username
            print(session["username"])
            return render_template("user_home.html", username = username)


@app.route("/createaccount", methods=['POST', 'GET'])
def create_acct():
    if request.method == "GET":
        return render_template("create_acct.html")

    if request.method == "POST":
        # check if username already exists in DB
        username = request.form.get("Username")
        password = sha3.sha3_224(str(request.form.get("Password")).encode('utf-8')).hexdigest()
        check = db.execute("SELECT * FROM accounts WHERE username = :username", {"username": username}).fetchone()

        if check is None:
            db.execute("INSERT INTO accounts(username, password) VALUES(:username, :password)",
                {"username": username, "password": password})
            db.commit()

            # get the username of the current user logged in
            session["username"] = username

            return render_template("user_home.html", username = username)
        else:
            return render_template("create_acct.html", username_taken = "Username already taken")


@app.route("/search", methods=['POST'])
def search():
    results = []

    if request.form.get("title") is not None:
        title = request.form.get("title")
    if request.form.get("author") is not None:
        author = request.form.get("author")
    if request.form.get("isbn") is not None:
        isbn = request.form.get("isbn")


    # --------------search by ISBN--------------
    temp = db.execute("SELECT * FROM books where isbn = :isbn",
                        {"isbn": isbn}).fetchall()
    for item in temp:
        if list(item) not in results:
            results.append(list(item))


    # --------------search by title--------------
    temp = db.execute("SELECT * FROM books where title = :title",
                        {"title": title}).fetchall()
    for item in temp:
        if list(item) not in results:
            results.append(list(item))


    # --------------search by author--------------
    temp = db.execute("SELECT * FROM books where author = :author",
                        {"author": author}).fetchall()
    for item in temp:
        if list(item) not in results:
            results.append(list(item))


    if not results:
        return render_template("user_home.html", message = "No matches", username = session['username'])
    else:
        return render_template("results.html", results = session["username"])
