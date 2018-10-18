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
            # Alert user that credentials are incorrect
        else:
            row = db.execute("SELECT id FROM accounts WHERE username = :username;", {"username": username}).fetchone()
            session['id'] = row[0]
            print(session['id'])
            return render_template("user_home.html", username = username)
            # somehow sign the user in??


@app.route("/createaccount", methods=['POST', 'GET'])
def create_acct():
    if request.method == "GET":
        return render_template("create_acct.html")

    if request.method == "POST":
        # implement feature to only allow alphanumeric usernames and password,
        # check if username already exists in DB
        username = request.form.get("Username")
        password = sha3.sha3_224(str(request.form.get("Password")).encode('utf-8')).hexdigest()
        check = db.execute("SELECT * FROM accounts WHERE username = :username", {"username": username}).fetchone()
        # print(check)
        if check is None:
            db.execute("INSERT INTO accounts(username, password) VALUES(:username, :password)",
                {"username": username, "password": password})
            db.commit()
            # get the id of the current user logged in
            row = db.execute("SELECT id FROM accounts WHERE username = :username;", {"username": username}).fetchone()
            session['id'] = row[0]
            print(session['id'])
            # print(session["current_userID"])
            return render_template("user_home.html", username = username)
        else:
            return render_template("create_acct.html", username_taken = "Username already taken")
