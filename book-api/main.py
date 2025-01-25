from flask import Flask, jsonify, request, make_response
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, get_jwt, 
    set_access_cookies, set_refresh_cookies
    )
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta, datetime
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['JWT_SECRET_KEY'] = 'super_secret' # Silly key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

# Database initialization
db = SQLAlchemy(app)

# JWT initialization
jwt = JWTManager(app)

# User model for sqlalchemy 
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    
    books = db.relationship('Books', back_populates='user')

    def __repr__(self):
        return f"<user {self.username}>"

# Book model for sqlalchemy
class Books(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(100), nullable=False)

    username = db.Column(db.String(80), db.ForeignKey("user.username"), nullable=False)

    user = db.relationship('User', back_populates='books', foreign_keys=username)

# This creates data.db and User table
with app.app_context():
    db.create_all()

# Only uncomment this if you have a client to store the cokkies otherwise api will fail
# @app.after_request
# @jwt_required(refresh=True)
# def refresh_jwt_token(response):
#     """Assign new token when expiration date is close and user makes a request"""
#     try:
#         expiration_time = get_jwt()["exp"]
#         target_timestamp = datetime.timestamp(datetime.now() + timedelta(hours=1))

#         if expiration_time < target_timestamp:
#             acces_token = create_access_token(identity=get_jwt_identity, expires_delta=timedelta(hours=5))
#             set_access_cookies(response, acces_token)

#     except (RuntimeError, KeyError):
#         return response
#     except Exception as e:
#         print(f"ERROR : {e}")
#         return response
    

@app.route('/')
def test():
    return jsonify("test: test")


@app.route('/register', methods=["POST"])
def register():
    data = request.get_json()
    username = data["username"]
    password = data["password"]
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()) # haspw function returns pybytes


    # Create the token 
    access_token = create_access_token(identity=username, expires_delta=timedelta(hours=3)) 
    refresh_token = create_refresh_token(identity=username)

    response = make_response(jsonify({"msg": "register seccessfully", "access_token": access_token}))

    # Create user and add to session 
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)

    response.headers['Authorization'] = f"Bearer {access_token}"

    return response, 201

# This route is goona handle request from frontend other than website e.g(mobile, api, ...)
@app.route('/refresh', methods=["POST"])
@jwt_required(refresh=True)
def refersh():
    """This route returns a new token if user has a referesh token"""
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity, expires_delta=timedelta(hours=5))
    return jsonify(access_token=access_token)

@app.route('/add_book', methods=["POST"])
@jwt_required()
def add_book():
    data = request.get_json()
    username = get_jwt_identity()
    
    author = data["author"]
    title = data["title"]

    if not data or not data.get("author") or not data.get("title"):
        return jsonify({"msg": "missing required field"}), 400
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"msg": "error user not found"}), 404
    
    new_book = Books(
        author=author,
        title=title,
        username=username
    )

    db.session.add(new_book)
    db.session.commit()

    return jsonify({"msg": "book added successfully", "book": {"id": new_book.id, "author": new_book.author, "title": new_book.title}}), 201

@app.route('/get_book')
@jwt_required()
def get_book():
    data = request.get_json()
    title = data.get("title")
    author = data.get("author")
    username = get_jwt_identity()

    # This was before making search flexible
    # if not data or not title:
    #     return jsonify({"msg": "misisng fileds data"}), 400
    
    # Make base query , only this users book
    query = Books.query.filter_by(username=username)

    # Search specific book based on title
    if title: 
        query = query.filter(Books.title.ilike(f"%{title}%"))

    # Search based on authors works
    if author:
        query = query.filter(Books.author.ilike(f"%{author}%"))

    # Execute
    books = query.all()

    if not books :
        return jsonify({"msg": "book not found based on title and author"}), 404
    
    # Fromating into list of dict
    books_data = [{
    "id": book.id,
    "title": book.title,
    "author": book.author,
    } for book in books]

    return jsonify(books_data), 200

@app.route('/delete', methods=["DELETE"])
@jwt_required()
def delete_book():
    data = request.get_json()
    title = data.get("title")
    username = get_jwt_identity()

    if not title:
        return jsonify({"msg": "missing required field"}), 400
    
    book = Books.query.filter_by(username=username)
    book = Books.query.filter(Books.title.ilike(f"%{title}%")).first()

    db.session.delete(book)
    db.session.commit()

    return jsonify({"msg": "book deleted"})


@app.route('/update/<int:book_id>', methods=["PUT"])
@jwt_required()
def update(book_id):
    data = request.get_json()
    if not data.get('title') or not data.get('author'):
        return jsonify({'message': 'Title and author are required'}), 400

    book = Books.query.get(book_id)

    if not book:
        return jsonify({"msg": "book not found"}), 404
    
    if 'title' in data:
        book.title = data["title"]

    if 'author' in data:
        book.author = data["author"]

    db.session.commit()

    return jsonify({
        "msg": "Book updated successfully",
        "book": {
            "title": book.title,
            "author": book.author,
            "book_id": book.id
        }
    }), 200



@app.route('/user', methods=["GET"])
@jwt_required()
def get_user():
    """Check if user exists"""
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()

    
    if user:
        return jsonify({'msg': 'User found', 'name': user})
    else:
        return jsonify({"Error": "user does not exist"}), 404


if __name__ == "__main__":
    app.run(debug=True)
