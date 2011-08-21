# Reads category/faces files.
# File should be formatted as CSV:
# <name>,<cat1>,<cat2>,...,<catn>

import sys
import os
import sqlite3
import csv
from optparse import OptionParser

DEFAULT_DB_FILE = "faces.db"

# Used if the DB doesn't even exist
def create_db(db):
    print("Creating initial db schema...")
    c = db.cursor()
    c.execute("CREATE TABLE Categories (_id INTEGER PRIMARY KEY, category TEXT, position INTEGER);")
    c.execute("CREATE TABLE Faces (_id INTEGER PRIMARY KEY, drawable TEXT);")
    c.execute("CREATE TABLE FaceCategories (faceId INTEGER, categoryId INTEGER);")
    c.execute("CREATE TABLE android_metadata (locale TEXT DEFAULT 'en_US');")
    c.execute("INSERT INTO android_metadata VALUES('en_US');")
    db.commit()

# Reads a faces/categories file, adds it to the db
def read_file(infile, db):
    c = db.cursor()

    # Read the file
    reader = csv.reader(open(infile, 'rb'))
    data = []
    categories = {}
    for row in reader:
        data.append(row)
        for a in range(1,len(row)):
            category = row[a]
            if category not in categories:
                categories[category] = None

    # Figure out the category ids (if does not exist, prompt user to continue or not)
    for category in categories:
        c.execute("SELECT _id FROM Categories WHERE category=?", (category,))
        row = c.fetchone()
        if row is None:
            print('Category listed that does not yet exist - "%s".  Enter "y" to create, anything else to cancel run.' % category)
            yes_no = raw_input("[y/n]")
            if yes_no == 'y':
                c.execute("INSERT INTO Categories (category) VALUES (?)", (category, ))
                categories[category] = c.lastrowid
                print("IMPORTANT: BE SURE TO ADD A PRIORITY MANUALLY FOR THIS NEW CATEGORY!")
            else:
                sys.exit()
        else:
            categories[category] = row[0]

    # Add the faces to the db
    faces = {}
    for row in data:
        face = row[0]
        c.execute("INSERT INTO Faces (drawable) VALUES (?)", (face,))
        faces[face] = c.lastrowid

    # Link those faces to categories
    for row in data:
        face_id = faces[row[0]]
        for a in range(1, len(row)):
            category_id = categories[row[a]]
            c.execute("INSERT INTO FaceCategories (faceId, categoryId) VALUES (?, ?)", (face_id, category_id))

    # Commit all changes
    db.commit()

if __name__ == "__main__":
    usage = "usage: %prog infile [options]"
    parser = OptionParser(usage=usage)
    parser.add_option('-f', '--file', action="store", help="Target file for database", default=DEFAULT_DB_FILE)
    
    (options, args) = parser.parse_args()
    
    if len(args) != 1:
        parser.print_help()
        sys.exit()

    db_exists = os.path.exists(options.file)
    db = sqlite3.connect(options.file)
    if not db_exists:
        create_db(db)

    data = read_file(args[0], db)
