# Persistance PostgreSQL — APP #18

PostgreSQL 17 utilise le volume Docker nommé `postgres_data`, monté dans
`/var/lib/postgresql/data`. Le port 5432 n’est pas publié sur Windows/Linux : les
services Compose accèdent à `db:5432`. Le backend attend une base healthy.

## Premier lancement

Depuis APP, copier `.env.example` vers `.env` (PowerShell :
`Copy-Item .env.example .env` ; Linux : `cp .env.example .env`). Renseigner un mot
de passe aléatoire unique et long dans POSTGRES_PASSWORD. Ce fichier est ignoré
par Git. Ne pas afficher la configuration résolue contenant les secrets.

```sh
docker compose config --quiet
docker compose up -d db
docker compose ps db
docker compose exec -T db pg_isready -U cardioscope -d cardioscope
docker compose exec -T db psql -U cardioscope -d cardioscope -c "SELECT current_database();"
```

Le compte initial de l’image est un compte privilégié d’exploitation, adapté au
démonstrateur isolé. Avant un déploiement partagé, séparer le compte de migration
du compte applicatif aux droits minimaux. Ne pas exposer la base à Internet.

DB_HOST, DB_PORT, DB_NAME, DB_USER et DB_PASSWORD sont transmis au backend.
L’application du schéma et la création du compte initial sont des étapes
explicites : suivre le [guide APP #19](migrations-initialisation-admin.md) avec
une image backend qui contient Alembic et `app.init_admin`. Ce guide ne remplace
pas la migration ; Compose ne l’exécute pas automatiquement au démarrage.

## Vérifier la conservation après recréation

Après téléchargement de l’image, lancer le contrôle automatique depuis APP :

```sh
python scripts/verify_postgres_persistence.py
```

Sous Linux, utiliser `python3` si nécessaire. Le script recrée uniquement le
conteneur db (courte interruption), vérifie la ligne, retire sa table temporaire
et écrit `docs/verification-postgresql.json` uniquement après succès.

Sur une base de démonstration, créer une table de contrôle :

```sh
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U cardioscope -d cardioscope -c "CREATE TABLE IF NOT EXISTS app18_persistence_probe (id integer PRIMARY KEY); INSERT INTO app18_persistence_probe VALUES (1) ON CONFLICT DO NOTHING;"
docker compose up -d --force-recreate db
```

Attendre que `docker compose ps db` indique healthy, puis :

```sh
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U cardioscope -d cardioscope -c "SELECT count(*) FROM app18_persistence_probe WHERE id = 1;"
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U cardioscope -d cardioscope -c "DROP TABLE app18_persistence_probe;"
```

Le compteur attendu est 1. Toute erreur SQL ou autre compteur fait échouer la
vérification. Ces commandes doivent être exécutées sur un moteur Docker Linux
disponible ; la documentation seule ne constitue pas une preuve d’exécution.

## Arrêter et reprendre

`docker compose stop` arrête les services. `docker compose down` retire les
conteneurs et le réseau mais conserve le volume. `docker compose up -d` réutilise
les données. Garder le même nom de projet Compose et le même emplacement de dépôt :
un autre nom de projet peut sélectionner un autre volume.

Ne pas utiliser `docker compose down -v`, ni supprimer/pruner les volumes : ces
actions détruisent les données. La persistance ne remplace pas une sauvegarde.
Les sauvegardes et la restauration relèvent de APP #24.

POSTGRES_PASSWORD initialise uniquement un volume vide : modifier `.env` ne change
pas le mot de passe existant. Une rotation exige une modification du compte en
base et une mise à jour coordonnée du backend. Un changement de version majeure
de PostgreSQL nécessite une migration, pas un remplacement direct du tag.

La rotation des logs Docker limite leur taille ; elle ne garantit pas 14 jours.
La purge quotidienne, la rétention temporelle des logs et les sauvegardes de
7 jours restent à implémenter selon [APP #17](regles-conservation.md).

Référence : [image officielle PostgreSQL](https://hub.docker.com/_/postgres).

## Validation réelle du 19 novembre 2026

Le [rapport de vérification](verification-postgresql.json) atteste du contrôle
exécuté avec PostgreSQL 17.12 sous Docker Desktop : création d’une ligne temporaire,
recréation du conteneur (identifiants différents), lecture de la même ligne après
recréation, puis suppression de la table temporaire. Le service db est healthy.

La persistance du volume est validée. Ce contrôle ne prouve pas que les migrations
ont été appliquées, que l’admin a été initialisé, ni que le login et les parcours
métier fonctionnent.
