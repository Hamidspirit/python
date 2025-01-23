from flask import Flask, session, jsonify, redirect, request, url_for
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'
app.config['JWT_SECRET_KEY'] = 'super_secret' # Silly key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['JWT_TOKEN_LOCATION'] = ['headers']

# Database initialization
db = SQLAlchemy(app)

# JWT initialization
jwt = JWTManager(app)

# User model for sqlalchemy 
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f"<user {self.username}>"


# This creates data.db and User table
with app.app_context():
    db.create_all()

@app.route('/')
def test():
    return jsonify("test: test")


@app.route('/register', methods=["POST"])
def register():
    data = request.get_json()
    username = data["username"]
    password = data["password"]
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()) # haspw function returns pybytes

    # Create expiration date for token
    now = datetime.now(timezone.utc)
    expiration_date = datetime.timestamp(now + timedelta(hours=3))

    # Create the token 
    access_token = create_access_token(identity=username, expires_delta=expiration_date) 

    if username != "alo" or password != "1234":
        return jsonify({"message": "unvalid username"}), 401

    # Create user and add to session 
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "user added successfully", "access_token":access_token}), 201


@app.route('/user', methods=["GET"])
@jwt_required()
def get_user():
    """Check if user exists"""
    username = get_jwt_identity()
    user = User.query.filter_by(username=username).first()

    
    if user:
        return jsonify({'message': 'User found', 'name': user})
    else:
        return jsonify({"Error": "user does not exist"}), 404


if __name__ == "__main__":
    app.run(debug=True)
