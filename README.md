# Genshin Tools

Projet Django pour suivre ta progression Genshin Impact : personnages obtenus, recommandations de builds, suivi des talents et synthèse des matériaux.

## Configuration rapide
1. Installe les dépendances (Django, requests) :
   ```bash
   pip install -r requirements.txt
   ```
2. Applique les migrations :
   ```bash
   python manage.py migrate
   ```
3. Charge quelques données d'exemple :
   ```bash
   python manage.py load_sample_data
   ```
4. Lance le serveur de développement :
   ```bash
   python manage.py runserver
   ```

## Fonctionnalités
- **Suivi des personnages obtenus** : niveaux, ascensions, constellations, arme et set d'artéfacts planifiés.
- **Recommandations** : armes, sets d'artéfacts et ordre de montée des aptitudes par personnage.
- **Synthèse matériaux** : besoins cumulés pour tous les personnages obtenus comparés à ton inventaire.
- **Suivi des talents** : niveaux cibles ou aptitudes à ignorer.
- **Intégration API** : module `roster/services/api_client.py` prêt à consommer une API communautaire pour importer personnages et matériaux.

## Modèle de données
Les modèles principaux vivent dans `roster/models.py` et couvrent personnages, armes, artéfacts, matériaux, besoins par personnage, progression possédée et suivi des talents.

## Import depuis une API
Utilise `GenshinApiClient` (`roster/services/api_client.py`) comme base : il expose `fetch_characters()` et `fetch_materials()` à adapter selon l'API choisie. Les données peuvent ensuite être enregistrées via les modèles correspondants.
