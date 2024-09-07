import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'mysql+pymysql://root@localhost/commande_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
