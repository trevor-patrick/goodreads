import os
import sys
import sha3
import requests

from flask import Flask, render_template, request, session, jsonify
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

    if request.form.get("isbn") is not "":
        isbn = request.form.get("isbn")
        # --------------search by ISBN--------------
        temp = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn",
                                {"isbn": '%' + isbn + '%'}).fetchall()
        for item in temp:
            if list(item) not in results:
                results.append(list(item))

    if request.form.get("title") is not "":
        title = request.form.get("title")
        # --------------search by title--------------
        temp = db.execute("SELECT * FROM books WHERE title LIKE :title",
                                {"title": '%' + title + '%'}).fetchall()
        for item in temp:
            if list(item) not in results:
                results.append(list(item))

    if request.form.get("author") is not "":
        author = request.form.get("author")
        # --------------search by author--------------
        temp = db.execute("SELECT * FROM books WHERE author LIKE :author",
                                {"author": '%' + author + '%'}).fetchall()
        for item in temp:
            if list(item) not in results:
                results.append(list(item))

    if not results:
        return render_template("user_home.html", message = "No matches", username = session['username'])
    else:
        return render_template("results.html", results = results)


@app.route("/link_results", methods=['POST'])
def link_results():
    form_id = request.form.get("form_id")

    if form_id is "1":
        this_book_info = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                                {"isbn": request.form.get("isbn")}).fetchone()

        reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn",
                                {"isbn": request.form.get("isbn")}).fetchall()

        # print(reviews)
        # print("-----------------------")
        session['current_isbn'] = this_book_info[1]
        # print("Current isbn:")
        # print(session['current_isbn'])

        # get average rating from Goodreads API
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "GUzdXCsWJf04i6FuBd4X9w", "isbns": session['current_isbn']})
        json_res = json.loads(res.text)
        average_rating = json_res['books'][0]['average_rating']

        return render_template("book_details.html", this_book_info=this_book_info, reviews=reviews, average_rating=average_rating)

    if form_id is "2":
        results = []
        author = request.form.get("author")
        # --------------search by author--------------
        temp = db.execute("SELECT * FROM books WHERE author LIKE :author",
                                {"author": '%' + author + '%'}).fetchall()
        for item in temp:
            if list(item) not in results:
                results.append(list(item))
        return render_template("books_by_author.html", author=request.form.get("author"), results=results)


@app.route("/abcdefg", methods=['POST'])
def submit_review():
    new_review_data = [request.form.get("title"), request.form.get("review_text"), request.form.get("stars")]

    db.execute("INSERT INTO reviews (isbn, review, stars, title, username) VALUES (:isbn, :review, :stars, :title, :username)",
        {"isbn": session['current_isbn'], "review": new_review_data[1], "stars": new_review_data[2], "title": new_review_data[0], "username": session['username']})
    db.commit()

    # re-query for current book's reviews
    new_reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn",
                            {"isbn": session['current_isbn']}).fetchall()
    # query for current book info where isbn = session['current_isbn']
    this_book_info = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                            {"isbn": session['current_isbn']}).fetchone()

    return render_template("book_details.html", this_book_info=this_book_info, reviews=new_reviews)


@app.route("/api/<isbn>")
def return_json(isbn):
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "GUzdXCsWJf04i6FuBd4X9w", "isbns": isbn})
    if res.status_code == 404:
        return jsonify({"error":"invalid"}), 422
    
    return jsonify(res.json())
