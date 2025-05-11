from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
import os

auth_bp = Blueprint('auth', __name__)

# Temporary user database (for demo purposes)
USERS = {
    "wizbotuser": "12345"  # username: password
}

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username in USERS:
        return jsonify({"error": "Username already exists."}), 400

    USERS[username] = password
    return jsonify({"message": "User created successfully."}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if USERS.get(username) != password:
        return jsonify({"error": "Invalid username or password."}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)
