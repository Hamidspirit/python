import sqlite3
from models import DB_NAME

def add_user(username, email , hp) -> None:
    """Add username and hashed password to database"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            cursor.execute("INSERT INTO users (username ,email, hashed_password) VALUES (?, ?, ?)", (username, email, hp))

            conn.commit()
    except Exception as e:
        print(f"[Exception]: {e}")

def user_exists(username) -> bool:
    """Check if a username already exists in database and return boolean"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT 1 FROM users WHERE username = ? LIMIT 1", (username,))

            result = cursor.fetchone() 
            return result is not None
    except Exception as e:
        print(f"[Exception] : {e}")
        return False

def get_user(username) -> tuple:
    """Retrieve user data example : (1, 'alice', 'alice@example.com')"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, email FROM users WHERE username = ? LIMIT 1", (username,))
            result = cursor.fetchone()

            if not result:
                return "User not found"
            return result
        
    except Exception as e:
        print(f"[Exception]: {e}")

def get_hashed_pass(username):
    """Retrieve password from database"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT hashed_password FROM users WHERE username = ?", (username,))

            result = cursor.fetchone()[0]

            return result
    except Exception as e:
        print(f"[Exception]: {e}")

def add_recipe_to_db(user_id, title, content,shared: int, tags: list):
    try:
        shared = 1 if shared == 1 else 0
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()

            cursor.execute("INSERT INTO recipes (title, content, shared, user_id) VALUES (?, ?, ?, ?)",
                            (title, content, shared, user_id))

            recipe_id = cursor.lastrowid
            if tags:
                cursor.executemany("INSERT INTO tags (name , recipe) VALUES (?, ?)", [(tag, recipe_id) for tag in tags])

            conn.commit()

    except Exception as e:
        print(f"[Exception]: {e}")

def get_recipes_db(username):
    """Rrturn all of users recipes"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        user_id = get_user(username)[0]
        cursor.execute("SELECT * FROM recipes WHERE user_id = ? ", (user_id,))

        result = cursor.fetchall()
        # get column names from cursor.description
        columns = [desc[0] for desc in cursor.description]
        # convert result to dict
        recipes = dict(zip(columns, row) for row in result)
        
        return recipes

def get_recipe_by_id_db(recipe_id, username):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        user_id = get_user(username)[0]

        cursor.execute("SELECT * FROM recipes WHERE recipe_id = ? AND user_id = ?", (recipe_id, user_id))
        result = cursor.fetchone()

        columns = [des[0] for des in cursor.description] # get column names
        recipe = dict(zip(columns, result)) # convert to dict

        return recipe

def get_public_recipe_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM recipes WHERE shared = 1")
        result = cursor.fetchall()
        
        if not result:
            return None

        columns = [desc[0] for desc in cursor.description]
        recipes = dict(zip(columns, row) for row in result)

        return recipes