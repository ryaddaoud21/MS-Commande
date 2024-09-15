from flask import Blueprint, jsonify, request, make_response
import secrets
from functools import wraps

auth_blueprint = Blueprint('auth', __name__)

# Stockage simulé des tokens
valid_tokens = {}

# Fonction pour générer un token sécurisé
def generate_token():
    return secrets.token_urlsafe(32)

import requests


# Décorateur pour exiger un token valide
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return make_response(jsonify({"error": "Unauthorized"}), 401)

        received_token = token.split('Bearer ')[1]
        user = next((u for u, t in valid_tokens.items() if t["token"] == received_token), None)

        if not user:
            return make_response(jsonify({"error": "Unauthorized"}), 401)

        request.user = user
        request.role = valid_tokens[user]['role']

        return f(*args, **kwargs)
    return decorated_function

# Décorateur pour exiger le rôle d'administrateur
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.role != "admin":
            return make_response(jsonify({"error": "Forbidden"}), 403)
        return f(*args, **kwargs)
    return decorated_function

# Endpoint pour se connecter et générer un token
@auth_blueprint.route('/login', methods=['POST'])
def login():
    if not request.json or not 'username' in request.json or not 'password' in request.json:
        return jsonify({"msg": "Username and password required"}), 400

    username = request.json['username']
    password = request.json['password']

    # Validation simple des utilisateurs (utilisateurs codés en dur)
    users = {
        "admin": {"password": "password", "role": "admin"},
        "user1": {"password": "userpass", "role": "user"},
    }

    if username in users and users[username]['password'] == password:
        token = generate_token()
        valid_tokens[username] = {"token": token, "role": users[username]['role']}
        return jsonify({"token": token}), 200

    return jsonify({"msg": "Invalid credentials"}), 401

# Endpoint pour se déconnecter et invalider le token
@auth_blueprint.route('/logout', methods=['POST'])
@token_required
def logout():
    token = request.headers.get('Authorization').split('Bearer ')[1]
    user = next((u for u, t in valid_tokens.items() if t["token"] == token), None)
    if user:
        del valid_tokens[user]
        return jsonify({"msg": "Successfully logged out"}), 200
    return make_response(jsonify({"error": "Unauthorized"}), 401)



@auth_blueprint.route('/', methods=['GET'])
def index():
    return jsonify({"msg": "Welcome to the ORDER's API. The service is up and running!"}), 200