from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Commande(db.Model):
    __tablename__ = 'commandes'  # Nom de la table dans MySQL

    id = db.Column('CommandeID', db.Integer, primary_key=True)
    client_id = db.Column('ClientID', db.Integer, nullable=False)
    produit_id = db.Column('ProduitID', db.Integer, nullable=False)
    date_commande = db.Column('DateCommande', db.Date, nullable=False)
    statut = db.Column('Statut', db.String(100), default='En cours')
    quantite = db.Column('Quantite', db.Integer, nullable=False, default=1)
    montant_total = db.Column('MontantTotal', db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'<Commande {self.id} pour Client {self.client_id}>'
