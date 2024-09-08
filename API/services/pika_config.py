import pika
import time

def get_rabbitmq_connection():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host='rabbitmq'))
            return connection
        except pika.exceptions.AMQPConnectionError:
            print("RabbitMQ n'est pas encore disponible. Nouvelle tentative dans 5 secondes...")
            time.sleep(5)