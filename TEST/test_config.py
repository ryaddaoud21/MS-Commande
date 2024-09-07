import pytest
from API.config import Config

def test_config():
    assert Config.SQLALCHEMY_TRACK_MODIFICATIONS == False
    assert 'mysql' in Config.SQLALCHEMY_DATABASE_URI or 'sqlite' in Config.SQLALCHEMY_DATABASE_URI
