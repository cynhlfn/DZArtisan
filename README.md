# 🛠️ DZ Artisan

> Plateforme de mise en relation entre artisans qualifiés et clients en Algérie.

🌐 **Site en ligne :** [https://onecs-project.onrender.com/fr](https://onecs-project.onrender.com/fr)

---

## 📌 Présentation

**DZ Artisan** est une application web qui facilite la recherche et la mise en contact avec des artisans professionnels en Algérie (menuisiers, électriciens, maçons, peintres, plombiers, etc.).

Le projet a été développé dans le cadre d'un projet académique (GL & BDD), avec une architecture full-stack Django, un système de messagerie en temps réel, et un déploiement containerisé via Docker.

---

## ✨ Fonctionnalités clés

-  **Recherche d'artisans** par catégorie (menuisier, plombier, électricien…) et par localisation
-  **Filtres avancés** pour affiner les résultats selon le métier, les évaluations ou la disponibilité
-  **Profils artisans** détaillés avec description, expérience et spécialités
-  **Système d'évaluations et d'avis** clients pour choisir en toute confiance
-  **Messagerie intégrée en temps réel** (chat) entre clients et artisans
-  **Authentification** — inscription et connexion sécurisées (clients & artisans)
-  **Interface multilingue** (Français / Arabe)
-  **Design responsive** adapté mobile et desktop
-  **Déploiement Docker** avec `docker-compose`

---

## 🧰 Stack technique

| Couche | Technologie |
|---|---|
| Backend | Python · Django |
| Temps réel | Django Channels (WebSocket) |
| Base de données | PostgreSQL . Neon|
| Containerisation | Docker · Docker Compose |
| Tests | Pytest . Postman |
| Déploiement | Render |

---

## 🚀 Installation & lancement local

### Prérequis

- [Docker](https://www.docker.com/) & Docker Compose installés
- Git

### Étapes

```bash
# 1. Cloner le dépôt
git clone https://github.com/cynhlfn/DZArtisan.git
cd DZArtisan

# 2. Lancer les conteneurs
docker-compose up --build

# 3. Appliquer les migrations
docker-compose exec web python manage.py migrate

# 4. Créer un superutilisateur (optionnel)
docker-compose exec web python manage.py createsuperuser
```

L'application est accessible sur **http://localhost:8000**

---

## 👥 Contributeurs

Ce projet a été réalisé en équipe dans le cadre d'un projet universitaire.

---

## 📄 Licence

Ce projet est à usage académique.
