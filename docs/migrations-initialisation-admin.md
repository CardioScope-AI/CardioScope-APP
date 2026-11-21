# Migrations et compte administrateur — APP #19

Ce guide décrit l’initialisation de la base CardioScope avec les commandes du
BACKEND. Les migrations créent le schéma ; elles ne créent aucun compte admin.
L’API ne lance pas les migrations et ne crée pas de compte automatiquement.

## Préparer les dépôts et la base

Les dépôts APP et BACKEND doivent être voisins. Récupérer une version du backend
qui contient `alembic.ini`, `migrations/` et `app.init_admin`. Depuis APP, copier
`.env.example` en `.env`, définir un mot de passe PostgreSQL long et aléatoire,
puis vérifier la configuration sans l’afficher :

```sh
docker compose config --quiet
docker compose up -d --wait db
```

## Appliquer ou mettre à jour le schéma

Construire l’image backend, puis exécuter la migration explicitement :

```sh
docker compose build backend
docker compose run --rm --no-deps backend python -m alembic upgrade head
docker compose run --rm --no-deps backend python -m alembic current
```

`upgrade head` applique uniquement les révisions manquantes. La révision `0001`
crée les tables admin, sessions, simulations, CSRF et limitation des tentatives.
La table `alembic_version` enregistre la révision présente. Pour chaque nouvelle
version backend, appliquer `upgrade head` avant de relancer les services qui
dépendent du schéma. Ne pas modifier ou supprimer une migration déjà appliquée.

Pour voir le schéma réellement installé, consulter le guide
[PostgreSQL backend](../../CardioScope-BACKEND/docs/base-donnees.md) dans le dépôt
BACKEND correspondant à l’image déployée.

## Créer le compte admin initial

Après la migration, lancer la commande dans un terminal interactif :

```sh
docker compose run --rm --no-deps backend python -m app.init_admin --username admin
```

Saisir le mot de passe deux fois lorsque la commande le demande. Il n’est pas
affiché. Choisir un mot de passe unique conforme à la politique backend (15 à
128 caractères). La commande stocke un hash Argon2id et refuse de créer ou de
modifier un compte si un administrateur existe déjà. Elle ne réinitialise pas
un mot de passe oublié.

Ne jamais placer le mot de passe dans `.env`, une commande, un ticket ou Git.
Pour un environnement sans terminal interactif, le backend accepte un fichier
secret monté en lecture seule avec `--password-file`; suivre les consignes du
[guide backend d’initialisation admin](../../CardioScope-BACKEND/docs/initialisation-admin.md).
Garder ce fichier hors des dépôts et le supprimer après usage.

## Vérifier et démarrer

`alembic current` doit afficher `0001 (head)` pour le schéma initial. Ensuite,
démarrer l’application :

```sh
docker compose up -d --build
docker compose ps
```

L’initialisation est une étape d’exploitation à effectuer une fois par base vide.
Ne pas supprimer le volume PostgreSQL pour « relancer » les migrations : cela
effacerait les données. Les détails de connexion DB et de rétention sont dans le
[guide PostgreSQL APP](persistance-postgresql.md).
