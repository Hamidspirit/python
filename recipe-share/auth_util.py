from functools import wraps
from flask import request, jsonify
import bcrypt
import datetime
import jwt

from data_util import get_user, get_hashed_pass

JWT_SECRET_KEY = "super_secret_key_for_my_TOKENS"

def hash_pass(password) -> str:
    """Return a raw binary hash of password"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(password, username) -> bool:
    hashed_password = get_hashed_pass(username)

    if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
        return True
    return False


def generate_jwt(username):
    """Generate and return a token"""
    payload = {
        'username': username,
        'expiration': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
    return token


def token_required(f):
    """Add token authentication required to endpoints"""
    @wraps(f)
    def decorator(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(" ")[1] # Expects Bearer <Token>
            except IndexError:
                return jsonify({"msg": "Invalid Token format"}), 401
            
        if not token:
            token = request.cookies.get('access_token')

        if not token:
            return jsonify({"msg": "Token is missing"}), 401
        
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
            current_user = get_user(payload["username"])
            if not current_user:
                return jsonify({"msg": "User not found"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"msg":"Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"msg": "Invalid token"}), 401
        
        return f(current_user, *args, **kwargs)
    return decorator

def get_token_payload():
    token = None
    auth_header = request.headers.get('Authorization')
    if auth_header:
        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            return jsonify({"msg": "Invalid token format"}), 401
        
    if not token:
        token = request.cookies.get('access_token')
    
    if not token:
        return jsonify({"msg": "Token is missing"}), 401
    
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    return payload