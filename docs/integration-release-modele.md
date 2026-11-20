# Intégration de la release ML au backend #24

## Configuration

Compose accepte désormais MODEL_PATH, AUTH_COOKIE_SECURE et CORS_ORIGINS depuis
son environnement/.env. La valeur par défaut de MODEL_PATH reste le modèle
historique ; .env.example propose la release rf-cleveland-v1.

Pour sélectionner la release complète disponible localement :

```text
MODEL_PATH=/models/releases/rf-cleveland-v1/pipeline.joblib
```

Les quatre autres fichiers doivent accompagner le modèle dans ce dossier.
Le joblib est ignoré par Git : récupérer le dossier complet via le canal de
distribution des artefacts, ou produire une release vérifiée avec DATA-ML #22.

En HTTPS : AUTH_COOKIE_SECURE=true. Uniquement en HTTP local : false.
CORS_ORIGINS doit inclure l’origine exacte du frontend ou du Swagger utilisé
pour le login, sans slash final, par exemple http://localhost:8001 pour Swagger.
Les cookies de session ne sont pas accessibles au JavaScript.

Après modification de configuration :

```powershell
docker compose up -d --no-build backend
```

Si l’image n’inclut pas encore BACKEND #24, la reconstruire d’abord. La base et
son volume sont conservés ; aucun reset du compte administrateur n’est nécessaire.

## Vérification HTTP isolée

Depuis APP, PowerShell, après mise à jour de l’image backend :

```powershell
docker compose run --rm --no-deps -T -e OPENBLAS_NUM_THREADS=1 -e OMP_NUM_THREADS=1 --volume "${PWD}/scripts/verify_model_info_release.py:/tmp/verify_release.py:ro" --volume "${PWD}/docs:/reports" backend python /tmp/verify_release.py --report /reports/verification-model-info-docker.json
```

Le script utilise les dépendances de l’image backend et les artefacts sélectionnés
par Compose. Il crée une base cardioscope_test_<uuid>, applique les migrations,
initialise un administrateur temporaire avec un secret aléatoire en mémoire,
et lance un serveur HTTP accessible seulement dans ce conteneur temporaire.
Il teste /health, le refus anonyme de /model-info, CSRF, login, /me puis le succès
de /model-info. Il compare version et empreinte au manifeste et vérifie no-store.

Enfin il arrête ce serveur et supprime uniquement sa base temporaire. Le rapport
est écrit après nettoyage réussi et ne contient aucun mot de passe ni cookie.
Les identifiants de la base doivent permettre CREATE DATABASE/DROP DATABASE,
comme dans le conteneur PostgreSQL de développement. Ne pas utiliser un compte
de production pour cette recette.

Ce test ne se connecte pas avec le véritable compte de l’administrateur et ne
valide pas encore l’interface de connexion frontend ni HTTPS au déploiement.

## Résultat local du 20 novembre 2026

Recette réussie : /health 200, /model-info anonyme 401, CSRF 200, login 200,
/admin/me 200 et /model-info authentifié 200. Version rf-cleveland-v1,
accuracy de test 0,8689, Cache-Control: no-store. Le nettoyage de la base temporaire
est terminé avant l’écriture du [rapport](verification-model-info-docker.json).
Le backend courant expose également la route dans OpenAPI et refuse l’anonymat.

L’image locale a été actualisée à partir de la précédente image backend validée,
en y copiant le code app courant ; aucune dépendance Python n’a changé. Le
Dockerfile canonique reste utilisable pour une reconstruction complète de l’équipe.
