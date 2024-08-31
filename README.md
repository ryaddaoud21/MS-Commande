# MS-Commande


# Microservice Client

## Description

Le microservice `Client` est responsable de la gestion des informations des clients. Il permet de créer, lire, mettre à jour et supprimer des clients dans la base de données.

## Installation

### Prérequis

- Python 3.9+
- MySQL
- `pip` pour installer les dépendances

### Étapes d'installation

1. Clonez le dépôt :
   ```bash
   git clone https://github.com/votre-utilisateur/MS-Client.git
   cd MS-Client
   ```

2. Créez un environnement virtuel et activez-le :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows: venv\Scripts\activate
   ```

3. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

4. Configurez la base de données MySQL :
   - Créez une base de données nommée `client_db`.
   - Mettez à jour les paramètres de connexion à la base de données dans `client_api.py` si nécessaire.

5. Exécutez les migrations de la base de données (si applicable) :
   ```bash
   flask db upgrade
   ```

## Utilisation

### Lancer l'application

```bash
python API/client_api.py
```

L'application sera disponible à l'adresse `http://127.0.0.1:5000/`.

### Endpoints

- **POST** `/login` : Authentification et génération de token.
- **GET** `/customers` : Récupère la liste de tous les clients.
- **GET** `/customers/<id>` : Récupère les détails d'un client spécifique.
- **POST** `/customers` : Crée un nouveau client (réservé aux administrateurs).
- **PUT** `/customers/<id>` : Met à jour les informations d'un client (réservé aux administrateurs).
- **DELETE** `/customers/<id>` : Supprime un client (réservé aux administrateurs).

### Tests

Pour exécuter les tests unitaires :

```bash
python -m unittest discover -s TEST
```

## CI/CD

Le pipeline CI/CD est configuré avec GitHub Actions. Les tests sont exécutés automatiquement à chaque commit ou pull request. Si les tests échouent, une nouvelle branche est créée pour corriger les erreurs.

## Contribuer

Les contributions sont les bienvenues. Veuillez soumettre une pull request ou signaler un problème via GitHub.

## License

