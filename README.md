
# MS-Commande

## Microservice Commande

### Description

Le microservice `Commande` gère la gestion des commandes. Il permet de créer, lire, mettre à jour et supprimer des commandes dans une base de données MySQL. De plus, il expose des métriques pour la surveillance via Prometheus et Grafana.

### Architectu
![Ajouter un sous-titre (2)](https://github.com/user-attachments/assets/854a8ecb-6195-4a31-8cf7-aaa1630bb0f1)
re

Le microservice `MS-Commande` fait partie d'une architecture microservices plus large, qui comprend également :

- **MS-Client** : Microservice pour la gestion des clients.
- **MS-Produit** : Microservice pour la gestion des produits.
- **RabbitMQ** : Service de messagerie pour la communication entre les microservices.
- **Prometheus** : Outil de surveillance pour collecter les métriques des microservices.
- **Grafana** : Plateforme d'analyse et de visualisation des métriques Prometheus.
- **MySQL** : Base de données pour les microservices `Client`, `Produit` et `Commande`.

### Prérequis

Avant de commencer, assurez-vous que vous avez installé les éléments suivants :

- **Docker** : Utilisé pour exécuter les conteneurs.
- **Docker Compose** : Utilisé pour orchestrer plusieurs conteneurs Docker.
- **Prometheus** : Utilisé pour surveiller les performances des microservices.
- **Grafana** : Utilisé pour visualiser les métriques collectées par Prometheus.
- **Git** : Pour cloner les dépôts de microservices.

### Installation et Démarrage avec Docker Compose

1. **Clonez le dépôt du microservice Commande :**

   ```bash
   git clone https://github.com/ryaddaoud21/MS-Commande.git
   cd MS-Commande
   ```

2. **Récupérer le fichier `docker-compose.yml` pour l'architecture complète :**
   Clonez le dépôt du microservice : https://github.com/ryaddaoud21/microservices-deployment
   Ce fichier orchestrera tous les services nécessaires, y compris Prometheus, Grafana, RabbitMQ, MySQL et les microservices.

   ```bash
   docker-compose up -d
   ```

3. **Vérifiez que les services sont bien démarrés :**

   ```bash
   docker-compose ps
   ```

4. **Tester le microservice :**

   Pour exécuter les tests unitaires dans ce projet, utilisez la commande suivante :

   ```bash
   python -m unittest discover -s TEST | pytest
   ```

### Endpoints

- **POST** `/login` : Authentification et génération de token.
- **GET** `/orders` : Récupère la liste de toutes les commandes.
- **GET** `/orders/<id>` : Récupère les détails d'une commande spécifique.
- **POST** `/orders` : Crée une nouvelle commande (réservé aux administrateurs).
- **PUT** `/orders/<id>` : Met à jour les informations d'une commande (réservé aux administrateurs).
- **DELETE** `/orders/<id>` : Supprime une commande (réservé aux administrateurs).

### Surveillance et Visualisation

- **Prometheus** collecte les métriques du microservice.
- **Grafana** visualise ces métriques pour surveiller la performance et les ressources du microservice.

### Arborescence du projet

```
MS-Commande/
├── .github/                # Configurations spécifiques à GitHub
├── .idea/                  # Configurations IDE
├── API/
│   ├── __pycache__/        # Fichiers Python compilés
│   ├── services/
│   │   ├── pika_config.py  # Configuration de la connexion RabbitMQ
│   │   ├── rabbit__mq.py   # Service RabbitMQ pour la gestion des commandes
│   ├── commandes.py        # Endpoints de l'API pour la gestion des commandes
│   ├── config.py           # Configuration de Flask et du service
│   ├── models.py           # Modèles de base de données liés aux commandes
├── TEST/
│   ├── __pycache__/        # Fichiers Python compilés pour les tests
│   ├── __init__.py         # Initialisation de la suite de tests
│   ├── test_commandes.py   # Tests pour les fonctionnalités liées aux commandes
│   ├── test_auth.py   
│   ├── test_config.py  
├── .gitignore              # Fichiers et répertoires à ignorer dans le contrôle de version
├── Dockerfile              # Configuration Docker pour la conteneurisation du service
├── README.md               # Documentation du service MS-Commande
├── commande_api.py         # Point d'entrée pour exécuter l'application Flask
├── requirements.txt        # Dépendances Python pour le projet
```

### Ports

- **Client-Service** : `5001`
- **Produit-Service** : `5002`
- **Commande-Service** : `5003`
- **Prometheus** : `9090`
- **Grafana** : `3000`
- **RabbitMQ** : `5672` (AMQP) / `15672` (management)
  
