import sqlite3

DATABASE = 'app.db'
db = sqlite3.connect(DATABASE)

cursor = db.cursor()

# Creation of table "categories".
# If it existed already, we delete the table and create a new one
cursor.execute('DROP TABLE IF EXISTS categories')
cursor.execute("""CREATE TABLE categories (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name VARCHAR(200) NOT NULL)""")

# We seed the table with initial values.
# Here we insert 3 categories: "Videogames", "Boardgames" and "Outdoors"
for name in ["Videogames", "Boardgames", "Outdoor"]:
    cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))

# Creation of table "toys"
cursor.execute("DROP TABLE IF EXISTS toys")
cursor.execute("""CREATE TABLE toys (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                   name VARCHAR(200) NOT NULL,
                                   description VARCHAR(200) NOT NULL,
                                   price INTEGER NOT NULL,
                                   category_id INTEGER,
                                   CONSTRAINT fk_categories
                                     FOREIGN KEY (category_id)
                                     REFERENCES categories(id))""")

# We seed the table with initial values.
# Here 5 toys are inserted into the table "toys"
for data in [
        ("Playstation 4", "Famous video game platform", 499, 1),
        ("Barbie", "Pink doll", 29, None),
        ("Monopoly", "Board game $$$", 59, 2),
        ("Football ball", "A ball to play outside", 25, 3),
        ("Chess", "Board game for smart children", 25, 2),
        ]:
    if data[-1] is None:
        cursor.execute(
            """INSERT INTO toys (name, description, price)
                         VALUES (?, ?, ?)""",
            data[:3],
        )

    else:
        cursor.execute("""INSERT INTO toys
                        (name, description, price, category_id)
                        VALUES (?, ?, ?, ?)""", data)


# Creation of table "elves"
cursor.execute("DROP TABLE IF EXISTS elves")
cursor.execute("""CREATE TABLE elves (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                   first_name VARCHAR(200) NOT NULL,
                                   last_name VARCHAR(200) NOT NULL,
                                   login VARCHAR(200) NOT NULL,
                                   password BLOB NOT NULL,
                                   illegal TEXT)""")

# Creation of table "wishes"
cursor.execute("DROP TABLE IF EXISTS wishes")
cursor.execute("""CREATE TABLE wishes (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                   child_name VARCHAR(200) NOT NULL,
                                   toy_id INTEGER,
                                   CONSTRAINT fk_toy
                                     FOREIGN KEY (toy_id)
                                     REFERENCES toys(id))""")

# Creation of table "schedules"
cursor.execute("DROP TABLE IF EXISTS schedules")
cursor.execute("""CREATE TABLE schedules (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                   done INTEGER,
                                   done_at TEXT,
                                   elf_id INTEGER,
                                   wish_id INTEGER,
                                   CONSTRAINT fk_elf
                                     FOREIGN KEY (elf_id)
                                     REFERENCES elves(id),
                                   CONSTRAINT fk_wish
                                     FOREIGN KEY (wish_id)
                                     REFERENCES wishes(id))""")


# for data in [
#         ("Jean", "Michel", 'Hello', 'password'),
#         ("Paul", "Michel", 'Dodo', 'password'),
#         ("Jean", "Michel", 'Ropo', 'admin'),
#         ]:
#     if data[-1] is None:
#         cursor.execute("""INSERT INTO elves (first_name, last_name, login)
#                          VALUES (?, ?, ?)""", data[0:3])
#     else:
#         cursor.execute("""INSERT INTO elves
#                         (first_name, last_name, login, password)
#                         VALUES (?, ?, ?, ?)""", data)

# We save our changes into the database file
db.commit()

# We close the connection to the database
db.close()
