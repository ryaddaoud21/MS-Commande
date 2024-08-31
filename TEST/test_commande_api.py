import unittest
from unittest import mock
from datetime import date
from API.commande_api import app, db, Commande

class CommandeTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        # Setup the in-memory SQLite database for testing
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        db.create_all()

        # Create some test data with correct date object
        self.order1 = Commande(client_id=1, date_commande=date(2023, 8, 31), statut='En cours', montant_total=100.50)
        db.session.add(self.order1)
        db.session.commit()

        # Reload the order to attach it to the current session
        self.order1 = Commande.query.first()

        # Create a token for testing
        response = self.app.post('/login', json={
            'username': 'admin',
            'password': 'password'
        })
        self.auth_token = response.json['token']

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @mock.patch('API.commande_api.publish_message')
    def test_create_order(self, mock_publish_message):
        mock_publish_message.return_value = None  # No operation on message publishing

        response = self.app.post('/orders', json={
            'client_id': 1,
            'date_commande': str(date(2023, 8, 31)),  # Pass the date as a string
            'statut': 'En cours',
            'montant_total': 200.75
        }, headers={'Authorization': f'Bearer {self.auth_token}'})

        self.assertEqual(response.status_code, 201, msg="Expected 201 Created but got {0}".format(response.status_code))
        mock_publish_message.assert_called_once()

    def test_get_all_orders(self):
        response = self.app.get('/orders', headers={'Authorization': f'Bearer {self.auth_token}'})
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['client_id'], 1)

    def test_get_order_by_id(self):
        response = self.app.get(f'/orders/{self.order1.id}', headers={'Authorization': f'Bearer {self.auth_token}'})
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data['client_id'], 1)

    def test_update_order(self):
        response = self.app.put(f'/orders/{self.order1.id}', json={
            'statut': 'Livré',
            'montant_total': 150.75
        }, headers={'Authorization': f'Bearer {self.auth_token}'})
        
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data['statut'], 'Livré')

    def test_delete_order(self):
        response = self.app.delete(f'/orders/{self.order1.id}', headers={'Authorization': f'Bearer {self.auth_token}'})
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertEqual(data['message'], 'Order deleted')

    def test_login_invalid(self):
        response = self.app.post('/login', json={
            'username': 'invalid_user',
            'password': 'invalid_password'
        })
        self.assertEqual(response.status_code, 401)

    def test_login_valid(self):
        response = self.app.post('/login', json={
            'username': 'admin',
            'password': 'password'
        })
        self.assertEqual(response.status_code, 200)
        data = response.json
        self.assertIn('token', data)


if __name__ == '__main__':
    unittest.main()
