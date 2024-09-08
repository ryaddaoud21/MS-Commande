from flask import Blueprint, jsonify, request
from API.models import db, Commande
from API.auth import token_required, admin_required
from API.services.rabbit__mq import publish_message  # RabbitMQ pour la publication des messages
from datetime import datetime

# Création du blueprint pour les commandes
commandes_blueprint = Blueprint('commandes', __name__)

# Endpoint pour récupérer toutes les commandes (GET)
@commandes_blueprint.route('/orders', methods=['GET'])
@token_required
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
