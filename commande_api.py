from flask import Flask
from API.models import db
from API.auth import auth_blueprint
from API.commandes import commandes_blueprint
from API.config import Config
from API.services.rabbit__mq import start_rabbitmq_consumers

app = Flask(__name__)
app.config.from_object(Config)

# Initialiser la base de données
db.init_app(app)

# Enregistrer les blueprints
app.register_blueprint(auth_blueprint, url_prefix='/')
app.register_blueprint(commandes_blueprint, url_prefix='/')

if __name__ == '__main__':
    start_rabbitmq_consumers(app)
    app.run(host='0.0.0.0', port=5003)
