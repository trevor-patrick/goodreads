import os
import sys
import csv
import math

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('postgres://olxpdkjidxzijo:6c0ff6d277bd117d6e615144dab8b3fe26e190e0788c30c9aa4c6de74076af2d@ec2-54-235-242-63.compute-1.amazonaws.com:5432/d25m2jqruo7e1o')
db = scoped_session(sessionmaker(bind=engine))

if __name__ == '__main__':
    loadingBar = [' '] * 50
    percentage = 0
    frac = 0
    # ingore first line of books.csv, as it is just the header
    with open('books.csv') as csv_file:
            count = 1

            csv_reader =  csv.reader(csv_file, delimiter=',')
            row_count = sum(1 for i in csv_reader) # count number of rows, used for loading bar
            span = math.floor(row_count/100)

            csv_file.seek(0) # reset pointer to first row
            next(csv_reader)
            for row in csv_reader:
                # make sure book doesn't already exist in DB
                check = db.execute("SELECT * FROM books where isbn = :isbn",
                    {"isbn": row[0]}).fetchone()
                if check is None:
                    db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                        {"isbn": row[0], "title": row[1], "author": row[2], "year": row[3]})
                    db.flush()

                frac = count/row_count
                sys.stdout.write('\r[{:>5.1%}]'.format(frac))
                sys.stdout.flush()

                count += 1

            db.commit()
            print("\nDone")
