from flask import Flask, jsonify, request, make_response
from functools import wraps
import secrets
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime  # Utilisez `date` pour obtenir la date actuelle
from API.rabbit__mq import *  # Import absolu
from API.pika_config import get_rabbitmq_connection


# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration de la base de données MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/commande_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialisation de SQLAlchemy
db = SQLAlchemy(app)

# Modèle de la base de données pour les commandes
class Commande(db.Model):
    __tablename__ = 'commandes'  # Nom de la table dans MySQL

    id = db.Column('CommandeID', db.Integer, primary_key=True)
    client_id = db.Column('ClientID', db.Integer, nullable=False)
    date_commande = db.Column('DateCommande', db.Date, nullable=False)
    statut = db.Column('Statut', db.String(100), default='En cours')
    montant_total = db.Column('MontantTotal', db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'<Commande {self.id} pour Client {self.client_id}>'

# Simulated token storage (In a real application, use a database or other secure storage)
valid_tokens = {}

# Function to generate a secure token
def generate_token():
    return secrets.token_urlsafe(32)

# Decorator to require a valid token
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

# Decorator to require admin role
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.role != "admin":
            return make_response(jsonify({"error": "Forbidden"}), 403)
        return f(*args, **kwargs)
    return decorated_function

# Endpoint to login and generate a token
@app.route('/login', methods=['POST'])
def login():
    if not request.json or not 'username' in request.json or not 'password' in request.json:
        return jsonify({"msg": "Username and password required"}), 400

    username = request.json['username']
    password = request.json['password']

    # Simple user validation (hardcoded users)
    users = {
        "admin": {"password": "password", "role": "admin"},
        "user1": {"password": "userpass", "role": "user"},
    }

    if username in users and users[username]['password'] == password:
        token = generate_token()
        valid_tokens[username] = {"token": token, "role": users[username]['role']}
        return jsonify({"token": token}), 200

    return jsonify({"msg": "Invalid credentials"}), 401

# Endpoint to logout and invalidate the token
@app.route('/logout', methods=['POST'])
@token_required
def logout():
    token = request.headers.get('Authorization').split('Bearer ')[1]
    user = next((u for u, t in valid_tokens.items() if t["token"] == token), None)
    if user:
        del valid_tokens[user]
        return jsonify({"msg": "Successfully logged out"}), 200
    return make_response(jsonify({"error": "Unauthorized"}), 401)

# Endpoint to get all orders
@app.route('/orders', methods=['GET'])
@token_required
def get_orders():
    commandes = Commande.query.all()
    return jsonify([{
        "id": c.id,
        "client_id": c.client_id,
        "date_commande": c.date_commande.strftime('%Y-%m-%d'),
        "statut": c.statut,
        "montant_total": str(c.montant_total)  # Convertir Decimal en string
    } for c in commandes])

@app.route('/orders/<int:id>', methods=['GET'])
@token_required
def get_order(id):
    commande = Commande.query.get(id)
    if commande:
        return jsonify({
            "id": commande.id,
            "client_id": commande.client_id,
            "date_commande": commande.date_commande.strftime('%Y-%m-%d'),
            "statut": commande.statut,
            "montant_total": str(commande.montant_total)  # Convertir Decimal en string
        })
    return jsonify({'message': 'Order not found'}), 404

@app.route('/orders', methods=['POST'])
@token_required
@admin_required

def create_order():
    data = request.json
    new_order = Commande(
        client_id=data['client_id'],
        date_commande=datetime.today(),
        statut=data.get('statut', 'En cours'),
        montant_total=data['montant_total']
    )
    db.session.add(new_order)
    db.session.commit()

    # Publier un message à RabbitMQ pour notifier la création de commande
    order_message = {
        "order_id": new_order.id,
        "client_id": new_order.client_id,
        "montant_total": str(new_order.montant_total)  # Convertir Decimal en string
    }
    publish_message('order_notifications', order_message)
    return jsonify({"id": new_order.id, "client_id": new_order.client_id, "montant_total": str(new_order.montant_total)}), 201


# Endpoint to update an order (admin only)
@app.route('/orders/<int:id>', methods=['PUT'])
@token_required
@admin_required
def update_order(id):
    order = Commande.query.get(id)
    if order:
        data = request.json
        order.statut = data.get('statut', order.statut)
        order.montant_total = data.get('montant_total', order.montant_total)
        db.session.commit()
        return jsonify({
            "id": order.id,
            "client_id": order.client_id,
            "date_commande": order.date_commande.isoformat(),
            "statut": order.statut,  # Inclure le statut dans la réponse
            "montant_total": str(order.montant_total)
        }), 200
    return jsonify({'message': 'Order not found'}), 404

# Endpoint to delete an order (admin only)
@app.route('/orders/<int:id>', methods=['DELETE'])
@token_required
@admin_required
def delete_order(id):
    commande = Commande.query.get(id)
    if commande:
        db.session.delete(commande)
        db.session.commit()
        return jsonify({'message': 'Order deleted'})
    return jsonify({'message': 'Order not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5003)
