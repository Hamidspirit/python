from flask import Flask, jsonify, request, make_response, redirect

from data_util import (
    add_user, user_exists, get_user, 
    add_recipe_to_db, get_recipes_db, 
    get_recipe_by_id_db, get_public_recipe_db
    )
from auth_util import hash_pass, generate_jwt, token_required, verify_password, get_token_payload

app = Flask(__name__)
app.config["SECRET_KEY"] = "super_secret_session_here"

@app.route("/")
def indext():
    return jsonify({"msg": "Test route"})

@app.route("/register", methods=["POST"])
def register():
    data = request.json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify({"msg": "Missing fields"}), 400
    
    if user_exists():
        return jsonify({"msg": "User already exists"}), 400
    
    hashed_password = hash_pass(password)

    add_user(username=username, email=email, hp=hashed_password)

    token = generate_jwt(username)
    response = make_response(jsonify({"msg": "User registerd successfully", "token": token}))
    response.set_cookie('access_token', token, httponly=True, secure=True, samesite=True)

    return response, 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json()
    username = data.get('username')
    password = data.get('password')

    user = get_user(username)
    if not user:
        return jsonify({"msg": "Invalid credential"}), 401

    if not verify_password(password, user):
        return jsonify({"msg": "Invalid credential"}), 401
    
    token = generate_jwt(username)
    response = make_response(jsonify({"msg":"User Loged in successfully", "token": token}))
    response.set_cookie('access_token', token ,httponly=True, secure=True, samesite=True)

    return response, 201

@app.route("/recipe", methods=["POST"])
@token_required
def add_recipe():
    data = request.json()
    payload = get_token_payload()
    username = payload["username"]
    user_id = data.get("user_id")
    title = data.get("title")
    content = data.get("content")
    tags = data.get("tags")
    shared = data.get("shared")

    if not title and content:
        return jsonify({"msg": "Title or Content is missing"}), 400
    
    if not shared:
        return jsonify({"msg": "shared field missing"}), 400
    
    if not user_id:
        user_id = get_user(username)[0]
    
    add_recipe_to_db(user_id, title, content, shared, tags)
    return jsonify({"msg": "Recipe added successfully"}), 201

@app.route("/recipe", methods=["GET"])
@token_required
def get_all_recipe():
    username = get_token_payload()["username"]
    recipes = get_recipes_db(username)
    if not recipes:
        return jsonify({"msg": "No recipes found"}), 404
    return jsonify(recipes), 200

@app.route("/recipe/<recipe_id>")
@token_required
def get_recipe_by_id(recipe_id):
    username = get_token_payload()["username"]
    recipe = get_recipe_by_id_db(int(recipe_id), username)
    if not recipe:
        return jsonify({"msg": f"No recipe found with id: {recipe_id}"}), 404
    
    return jsonify(recipe), 200

@app.route("/public_recipes", methods=["GET"])
def get_public_recipes():
    recipes = get_public_recipe_db()
    if not recipes:
        return jsonify({"msg": "No public recipes"}), 200
    return jsonify(recipes), 200

if __name__ == "__main__":
    print("=========================")
    print("Server is running.")
    app.run(debug=True)