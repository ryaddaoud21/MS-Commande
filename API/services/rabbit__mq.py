import json
from API.services.pika_config import get_rabbitmq_connection
#TEST : PROBLEME DE Récupération
from API.models import db, Commande
import threading

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


def delete_orders_for_client(ch, method, properties, body):
    data = json.loads(body)
    client_id = data.get('client_id')

    if client_id:
        # Supprimer toutes les commandes associées à ce client
        Commande.query.filter_by(client_id=client_id).delete()
        db.session.commit()
        print(f"Deleted all orders for client_id {client_id}")

    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_consuming():
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    # Déclarer l'exchange et la queue pour les suppressions de clients
    channel.exchange_declare(exchange='client_deletion_exchange', exchange_type='fanout')
    channel.queue_declare(queue='client_deletion_queue', durable=True)
    channel.queue_bind(exchange='client_deletion_exchange', queue='client_deletion_queue')

    # Consommer les messages
    channel.basic_consume(queue='client_deletion_queue', on_message_callback=delete_orders_for_client)

    print('Waiting for messages to delete orders for deleted clients...')
    channel.start_consuming()


def start_rabbitmq_consumers(app):
    threading.Thread(target=start_consuming, args=(app,), daemon=True).start()