import json
import threading

from flask import Blueprint, jsonify, request
from API.models import db, Commande
from API.auth import token_required, admin_required
from API.services.pika_config import get_rabbitmq_connection
from API.services.rabbit__mq import publish_message  # RabbitMQ pour la publication des messages
from datetime import datetime
from flask import Flask, jsonify, request, make_response
from prometheus_client import Counter, Summary, generate_latest
from prometheus_client.core import CollectorRegistry
from prometheus_client import CONTENT_TYPE_LATEST
from functools import wraps
import time


# Création du blueprint pour les commandes
commandes_blueprint = Blueprint('commandes', __name__)

# Configuration des métriques Prometheus
REQUEST_COUNTER = Counter('commande_requests_total', 'Total number of requests for commandes')
REQUEST_LATENCY = Summary('commande_processing_seconds', 'Time spent processing commande requests')

# Endpoint pour exporter les métriques Prometheus
@commandes_blueprint.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


# A global variable to store notifications
orders_deleted_notifications = []

# Route to get all notifications
@commandes_blueprint.route('/notifications', methods=['GET'])
def get_notifications():
    return jsonify(orders_deleted_notifications), 200


# Consommateur RabbitMQ pour la suppression des commandes d'un client
def consume_client_deletion_notifications(app):
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange='client_deletion_exchange', exchange_type='fanout')

    result = channel.queue_declare(queue='client_deletion_queue', durable=True)  # Modifier la queue pour être durable
    queue_name = result.method.queue

    channel.queue_bind(exchange='client_deletion_exchange', queue=queue_name)

    def callback(ch, method, properties, body):
        with app.app_context():  # Activer le contexte de l'application Flask
            try:
                message = json.loads(body)
                client_id = message.get('client_id')
                if client_id:
                    # Supprimer toutes les commandes associées au client supprimé
                    Commande.query.filter_by(client_id=client_id).delete()
                    db.session.commit()
                    print(f"Deleted all orders for client_id {client_id}")
                    formatted_message = f"Received order notification for client: {message}"

                    # Store the formatted notification
                    orders_deleted_notifications.append(formatted_message)
            except Exception as e:
                print(f"Error processing client deletion: {str(e)}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()




def start_rabbitmq_consumers(app):
    threading.Thread(target=consume_client_deletion_notifications, args=(app,), daemon=True).start()

# Décorateur pour le suivi des métriques
def track_metrics(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        REQUEST_COUNTER.inc()  # Incrément du compteur de requêtes
        with REQUEST_LATENCY.time():  # Mesure du temps de traitement
            return f(*args, **kwargs)
    return decorated_function

# Endpoint pour récupérer toutes les commandes (GET)
@commandes_blueprint.route('/orders', methods=['GET'])
@token_required
@track_metrics
def get_orders():
    commandes = Commande.query.all()
    return jsonify([{
        "id": c.id,
        "client_id": c.client_id,
        "produit_id": c.produit_id,
        "date_commande": c.date_commande.strftime('%Y-%m-%d'),
        "statut": c.statut,
        "montant_total": str(c.montant_total)  # Conversion du montant total en string
    } for c in commandes]), 200

# Endpoint pour récupérer une commande spécifique par ID (GET)

@commandes_blueprint.route('/orders/<int:id>', methods=['GET'])
@token_required
@track_metrics

def get_order(id):
    commande = Commande.query.get(id)
    if commande:
        return jsonify({
            "id": commande.id,
            "client_id": commande.client_id,
            "produit_id": commande.produit_id,
            "date_commande": commande.date_commande.strftime('%Y-%m-%d'),
            "statut": commande.statut,
            "montant_total": str(commande.montant_total)
        }), 200
    return jsonify({'message': 'Order not found'}), 404

# Endpoint pour créer une nouvelle commande (POST)
@commandes_blueprint.route('/orders', methods=['POST'])
@token_required
@admin_required
@track_metrics
def create_order():
    data = request.json
    new_order = Commande(
        client_id=data['client_id'],
        produit_id=data['produit_id'],  # Assurez-vous que l'ID du produit est fourni dans la requête
        date_commande=datetime.today(),
        statut=data.get('statut', 'En cours'),
        montant_total=data['montant_total']
    )
    db.session.add(new_order)
    db.session.commit()

    # Publier un message à RabbitMQ pour notifier la création de la commande
    order_message = {
        "order_id": new_order.id,
        "client_id": new_order.client_id,
        "produit_id": new_order.produit_id,  # Inclure le produit_id dans le message
        "montant_total": str(new_order.montant_total)  # Convertir Decimal en string
    }
    publish_message('order_notifications', order_message)

    # Publier un message spécifique pour la mise à jour du stock
    stock_update_message = {
        "produit_id": new_order.produit_id,
        "quantite": 1  # Par exemple, on retire 1 du stock pour chaque commande
    }
    publish_message('stock_update', stock_update_message)

    return jsonify({"id": new_order.id, "client_id": new_order.client_id, "produit_id": new_order.produit_id,
                    "montant_total": str(new_order.montant_total)}), 201


# Endpoint pour mettre à jour une commande par ID (PUT)
@commandes_blueprint.route('/orders/<int:id>', methods=['PUT'])
@token_required
@admin_required
@track_metrics

def update_order(id):
    order = Commande.query.get(id)
    if not order:
        return jsonify({'message': 'Order not found'}), 404

    data = request.json
    order.statut = data.get('statut', order.statut)
    order.montant_total = data.get('montant_total', order.montant_total)
    db.session.commit()

    # Publier un message à RabbitMQ pour notifier la mise à jour de la commande
    '''update_message = {
        "order_id": order.id,
        "statut": order.statut,
        "montant_total": str(order.montant_total)
    }
    publish_message('order_update', update_message)'''

    return jsonify({
        "id": order.id,
        "client_id": order.client_id,
        "produit_id": order.produit_id,
        "date_commande": order.date_commande.strftime('%Y-%m-%d'),
        "statut": order.statut,
        "montant_total": str(order.montant_total)
    }), 200

# Endpoint pour supprimer une commande par ID (DELETE)
@commandes_blueprint.route('/orders/<int:id>', methods=['DELETE'])
@token_required
@admin_required
@track_metrics
def delete_order(id):
    commande = Commande.query.get(id)
    if not commande:
        return jsonify({'message': 'Order not found'}), 404

    db.session.delete(commande)
    db.session.commit()

    """# Publier un message à RabbitMQ pour notifier la suppression de la commande
    delete_message = {
        "order_id": commande.id,
        "client_id": commande.client_id,
        "produit_id": commande.produit_id
    }
    publish_message('order_delete', delete_message)"""

    return jsonify({'message': 'Order deleted successfully'}), 200
