import os
import sys

from flask import Flask, render_template, request
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

engine = create_engine('postgres://olxpdkjidxzijo:6c0ff6d277bd117d6e615144dab8b3fe26e190e0788c30c9aa4c6de74076af2d@ec2-54-235-242-63.compute-1.amazonaws.com:5432/d25m2jqruo7e1o')
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/createaccount", methods=['POST', 'GET'])
def create_acct():
    if request.method == "GET":
        return render_template("create_acct.html")

    if request.method == "POST":
        db.execute("INSERT INTO accounts(username, password) VALUES(:username, :password)",
            {"username": request.form.get("Username"), "password": request.form.get("Password")})
        db.commit()
        return render_template("create_acct.html")
