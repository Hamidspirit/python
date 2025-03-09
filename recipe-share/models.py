import sqlite3

DB_NAME = "data.db"

def create_database():
    """Create database if dont exist"""
    with sqlite3.connect(DB_NAME) as con:
        cursor = con.cursor()

        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users(
                             id INTEGER PRIMARY KEY AUTOINCREMENT,
                             username TEXT NOT NULL UNIQUE,
                             email TEXT NOT NULL UNIQUE,
                             hashed_password BLOB NOT NULL, -- bcrypt returns raw binary hence blob 
                             signed_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS recipes(
                             recipe_id INTEGER PRIMARY KEY AUTOINCREMENT,
                             title TEXT NOT NULL,
                             content TEXT NOT NULL,
                             shared INTEGER NOT NULL DEFAULT 1, -- 0 for false and 1 for true
                             user_id INTEGER NOT NULL,
                             FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
                             
            CREATE TABLE IF NOT EXISTS tags(
                             tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                             name TEXT,
                             recipe_id INTEGER NOT NULL, -- recipe id
                             FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE
            );
        """)



if __name__ == "__main__":
    create_database()
    print("Database Created succesfully")