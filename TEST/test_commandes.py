import pytest
from unittest.mock import patch  # Pour simuler RabbitMQ
from flask import Flask
from API.models import db, Commande
from API.commandes import commandes_blueprint
from API.auth import auth_blueprint
from API.config import Config

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Utiliser une base de données en mémoire pour les tests
    app.config['TESTING'] = True

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(commandes_blueprint)
    app.register_blueprint(auth_blueprint)

    yield app

    with app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_token(client):
    # Obtenir un token d'authentification pour l'admin
    response = client.post('/login', json={'username': 'admin', 'password': 'password'})
    return response.json['token']

@pytest.fixture
def user_token(client):
    # Obtenir un token d'authentification pour un utilisateur standard
    response = client.post('/login', json={'username': 'user1', 'password': 'userpass'})
    return response.json['token']

# Mock RabbitMQ publish_message function
@patch('API.commandes.publish_message')
def test_get_orders(mock_publish, client, admin_token):
    headers = {'Authorization': f'Bearer {admin_token}'}
    response = client.get('/orders', headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json, list)

# Mock RabbitMQ publish_message function
@patch('API.commandes.publish_message')
def test_create_order(mock_publish, client, admin_token):
    order_data = {
        "client_id": 1,
        "produit_id": 1,
        "montant_total": "100.00"
    }
    headers = {'Authorization': f'Bearer {admin_token}'}
    response = client.post('/orders', json=order_data, headers=headers)
    assert response.status_code == 201
    assert 'id' in response.json
    assert response.json['client_id'] == 1
    assert response.json['montant_total'] == "100.00"
    mock_publish.assert_called()  # Vérifie que RabbitMQ a bien été simulé

# Mock RabbitMQ publish_message function
@patch('API.commandes.publish_message')
def test_update_order(mock_publish, client, admin_token):
    # Créer une commande d'abord
    order_data = {
        "client_id": 1,
        "produit_id": 1,
        "montant_total": "100.00"
    }
    headers = {'Authorization': f'Bearer {admin_token}'}
    create_response = client.post('/orders', json=order_data, headers=headers)

    updated_data = {
        "statut": "Livré",
        "montant_total": "150.00"
    }

    order_id = create_response.json['id']
    response = client.put(f'/orders/{order_id}', json=updated_data, headers=headers)
    assert response.status_code == 200
    assert response.json['statut'] == "Livré"
    assert response.json['montant_total'] == "150.00"
    mock_publish.assert_called()  # Vérifie que RabbitMQ a bien été simulé

# Mock RabbitMQ publish_message function
@patch('API.commandes.publish_message')
def test_delete_order(mock_publish, client, admin_token):
    # Créer une commande d'abord
    order_data = {
        "client_id": 1,
        "produit_id": 1,
        "montant_total": "100.00"
    }
    headers = {'Authorization': f'Bearer {admin_token}'}
    create_response = client.post('/orders', json=order_data, headers=headers)

    order_id = create_response.json['id']
    delete_response = client.delete(f'/orders/{order_id}', headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json['message'] == 'Order deleted successfully'
    mock_publish.assert_called()  # Vérifie que RabbitMQ a bien été simulé

# Mock RabbitMQ publish_message function
@patch('API.commandes.publish_message')
def test_delete_order_non_admin(mock_publish, client, admin_token, user_token):
    # Créer une commande en tant qu'admin
    order_data = {
        "client_id": 1,
        "produit_id": 1,
        "montant_total": "100.00"
    }
    headers_admin = {'Authorization': f'Bearer {admin_token}'}
    create_response = client.post('/orders', json=order_data, headers=headers_admin)

    # Vérifiez que la commande a été créée avec succès
    assert create_response.status_code == 201
    order_id = create_response.json.get('id', None)

    # S'assurer que l'ID existe
    assert order_id is not None, "Order ID should exist"

    # Tenter de supprimer la commande avec un utilisateur non admin
    headers_user = {'Authorization': f'Bearer {user_token}'}
    delete_response = client.delete(f'/orders/{order_id}', headers=headers_user)

    # Vérifier que l'accès est refusé
    assert delete_response.status_code == 403
    assert delete_response.json['error'] == 'Forbidden'