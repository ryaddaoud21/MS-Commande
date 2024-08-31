import unittest
import json
from datetime import date, datetime
from API.commande_api import app, db, Commande
from unittest import TestCase, mock


class CommandeTestCase(unittest.TestCase):

    def setUp(self):
        # Configure the application for testing
        self.app = app.test_client()
        self.app.testing = True

        # Setup the in-memory database
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        db.create_all()

        # Add a test order with a Python date object
        order = Commande(client_id=1, date_commande=date(2023, 8, 31), statut='En cours', montant_total=100.50)
        db.session.add(order)
        db.session.commit()

        # Reload the order to ensure it's attached to the session
        self.order1 = Commande.query.filter_by(client_id=1).first()

        # Create an admin token
        self.admin_token = self.get_token("admin", "password")

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def get_token(self, username, password):
        response = self.app.post('/login', json={
            'username': username,
            'password': password
        })
        data = json.loads(response.data)
        return data.get('token')

    def test_login_valid(self):
        token = self.get_token("admin", "password")
        self.assertIsNotNone(token)

    def test_login_invalid(self):
        response = self.app.post('/login', json={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 401)

    def test_get_all_orders(self):
        response = self.app.get('/orders', headers={'Authorization': f'Bearer {self.admin_token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['client_id'], 1)

    def test_get_order_by_id(self):
        order = Commande.query.get(self.order1.id)
        response = self.app.get(f'/orders/{order.id}', headers={'Authorization': f'Bearer {self.admin_token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['client_id'], 1)

    @mock.patch('API.commande_api.publish_message')  # Mocking the publish_message function
    def test_create_order(self, mock_publish_message):
        mock_publish_message.return_value = None  # No operation on message publishing

        response = self.app.post('/orders', json={
            'client_id': 1,
            'date_commande': '2023-08-31',
            'statut': 'En cours',
            'montant_total': 200.75
        })

        self.assertEqual(response.status_code, 201, msg="Expected 201 Created but got {0}".format(response.status_code))

        # Check that the publish_message function was called once
        mock_publish_message.assert_called_once()

    def test_update_order(self):
        order = Commande.query.get(self.order1.id)
        response = self.app.put(f'/orders/{order.id}', json={
            'statut': 'Livré'
        }, headers={'Authorization': f'Bearer {self.admin_token}'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('statut', data)  # Ensure 'statut' key is present in the response
        self.assertEqual(data['statut'], 'Livré')

    def test_delete_order(self):
        order = Commande.query.get(self.order1.id)
        response = self.app.delete(f'/orders/{order.id}', headers={'Authorization': f'Bearer {self.admin_token}'})
        self.assertEqual(response.status_code, 200)
        response = self.app.get(f'/orders/{order.id}', headers={'Authorization': f'Bearer {self.admin_token}'})
        self.assertEqual(response.status_code, 404)
        #self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
