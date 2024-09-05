import pika
import json
from .pika_config import get_rabbitmq_connection
#TEST : PROBLEME DE Récupération

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