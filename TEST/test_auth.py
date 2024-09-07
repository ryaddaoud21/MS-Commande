import pytest
from flask import Flask
from API.auth import auth_blueprint
from API.config import Config


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(auth_blueprint)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_login_success(client):
    response = client.post('/login', json={'username': 'admin', 'password': 'password'})
    assert response.status_code == 200
    assert 'token' in response.json


def test_login_fail(client):
    response = client.post('/login', json={'username': 'admin', 'password': 'wrongpassword'})
    assert response.status_code == 401
    assert response.json['msg'] == 'Invalid credentials'


def test_logout(client):
    login_response = client.post('/login', json={'username': 'admin', 'password': 'password'})
    token = login_response.json['token']
    headers = {'Authorization': f'Bearer {token}'}

    logout_response = client.post('/logout', headers=headers)
    assert logout_response.status_code == 200
    assert logout_response.json['msg'] == 'Successfully logged out'
