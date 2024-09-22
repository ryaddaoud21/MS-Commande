import json
from flask import jsonify
from API.commandes import commandes_blueprint
from API.services.pika_config import get_rabbitmq_connection
#TEST : PROBLEME DE Récupération
from API.models import db, Commande
import threading

# A global variable to store notifications
orders_deleted_notifications = []




# Route to get all notifications
@commandes_blueprint.route('/notifications', methods=['GET'])
def get_notifications():
    return jsonify(orders_deleted_notifications), 200

def publish_message(exchange, message):
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange, exchange_type='fanout')

    channel.basic_publish(
        exchange=exchange,
        routing_key='',
        body=json.dumps(message)
    )
    connection.close()




# Consommateur RabbitMQ pour la suppression des commandes d'un client
def consume_client_deletion_notifications(app):
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange='client_deletion_exchange', exchange_type='fanout')

    result = channel.queue_declare(queue='', exclusive=True)  # Utilisation d'une queue exclusive
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
            except Exception as e:
                print(f"Error processing client deletion: {str(e)}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()




def start_rabbitmq_consumers(app):
    threading.Thread(target=consume_client_deletion_notifications, args=(app,), daemon=True).start()