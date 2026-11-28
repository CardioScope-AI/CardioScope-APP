# Sauvegarde et restauration PostgreSQL — APP #24

Ce guide applique la [politique de conservation](regles-conservation.md) au
démonstrateur CardioScope. Il concerne la base PostgreSQL du service `db` dans
`compose.yaml`. Le volume Docker `postgres_data` garde la base entre deux
démarrages, mais ne protège pas contre la perte ou la corruption du volume.

## Ce qui est sauvegardé

Le fichier produit par `pg_dump -Fc` contient le schéma et les données de la base
`cardioscope` : administrateur, simulations, sessions, contextes CSRF, compteurs
de connexion et révision Alembic. Le chiffrement GPG produit un fichier
`backups/cardioscope-AAAAMMJJTHHMMSSZ.dump.gpg` ; aucun dump en clair n'est
écrit sur le poste hôte.

Cette opération ne sauvegarde ni les quatre dépôts Git, ni les artefacts ML,
ni `.env`, ni la clé privée GPG. Prévoir leur récupération séparément. Le
dossier `backups/` et `.env` sont exclus de Git. Une sauvegarde conservée sur
le même ordinateur ne suffit pas en cas de perte de cet ordinateur : copier
les archives chiffrées vers un stockage distinct, accessible seulement à
l'équipe chargée de l'exploitation. Conserver la clé privée et son moyen de
récupération **séparément** des archives. Ne jamais les publier dans Git ou
les joindre à une issue.

## 1. Préparer une sauvegarde

Depuis le dossier `CardioScope-APP`, vérifier la configuration sans afficher
le mot de passe, puis démarrer la base :

```sh
docker compose config --quiet
docker compose up -d --wait db
docker compose ps db
```

`config --quiet` valide `.env` et Compose. `up` démarre PostgreSQL ; `ps`
permet de vérifier l'état `healthy`. La clé **publique** du destinataire doit
être disponible dans GPG. Sous Windows, Git Bash fournit `bash` et `gpg` ;
vérifier la clé avec `gpg --list-keys --fingerprint` et relever son empreinte
complète. La clé privée correspondante sera nécessaire pour restaurer.

Dans Git Bash, toujours depuis `CardioScope-APP` :

```sh
bash scripts/backup_postgres.sh EMPREINTE_DE_LA_CLE_PUBLIQUE
```

Remplacer le texte en majuscules par l'empreinte réelle, sans guillemets
autour de la commande entière. Le script vérifie PostgreSQL, crée un dump au
format personnalisé, le chiffre avec GPG, puis publie le fichier seulement
si le transfert a réussi. Un fichier partiel est retiré en cas d'échec. Il
supprime les archives locales `cardioscope-*.dump.gpg` ayant atteint sept
jours **à chaque lancement**, même si la nouvelle sauvegarde échoue.
Cette rotation ne concerne pas les copies placées sur un autre stockage :
leur durée de vie doit également être limitée à sept jours.

Vérifier qu'un nouveau fichier non vide est apparu dans `backups/`, puis
exécuter le test de restauration isolée ci-dessous. Ne pas conclure au
succès sur la seule présence du fichier. En cas d'erreur, conserver le
message technique sans y copier de secret, corriger la cause et relancer ;
ne pas annoncer une sauvegarde réussie. Si les sauvegardes ne sont plus
produites, alerter l'équipe : la rotation peut laisser zéro copie valide.

### Exécution quotidienne

L'exploitation doit lancer `backup_postgres.sh` chaque jour sous un compte
ayant accès à Docker et à la clé publique GPG. Sous Windows, le Planificateur
de tâches peut lancer Git Bash avec une action de cette forme, en adaptant le
chemin et l'empreinte :

```text
Programme : C:\Program Files\Git\bin\bash.exe
Arguments : -lc "cd /c/Users/dell/Desktop/CardioScope/CardioScope-APP && bash scripts/backup_postgres.sh EMPREINTE_DE_LA_CLE_PUBLIQUE"
```

Choisir une heure quotidienne, activer l'exécution après un démarrage manqué,
puis contrôler le code de sortie et l'heure de la dernière archive. Docker
Desktop doit être opérationnel dans cette session. La planification n'est
**pas** créée par ce dépôt ; elle doit être configurée et vérifiée sur chaque
machine d'exploitation. L'ordinateur éteint ou un échec de Docker empêche
la sauvegarde : surveiller les échecs, ne pas se fier seulement à l'horaire.

## 2. Tester une restauration sans toucher à la base principale

Choisir le fichier chiffré à tester. Depuis `CardioScope-APP` dans Git Bash :

```sh
bash scripts/verify_backup_restore.sh backups/NOM_DU_FICHIER.dump.gpg
```

Le script déchiffre le flux en mémoire, vérifie que PostgreSQL peut lire
l'archive, crée une base de test au nom unique, y restaure le dump et vérifie
les tables attendues. Il y exécute le nettoyage imposé par la politique :
il ajoute d'abord des lignes fictives aux tables de sessions, contextes CSRF,
compteurs de connexion et simulations, puis vérifie qu'elles ont toutes été
vidées. Le nombre de comptes admin reste identique. La base de test est supprimée à
la fin, même si la vérification échoue. La base `cardioscope` n'est pas
modifiée. Le test nécessite la clé **privée** GPG ; si elle est protégée,
GPG peut demander sa phrase secrète localement. Ne jamais la transmettre
dans le terminal d'une commande, une capture ou un message.

Ce contrôle vérifie la restauration SQL et le nettoyage, pas le parcours de
connexion dans le navigateur.

## 3. Restaurer après perte de la base

Cette procédure vise une **base neuve et vide**, après perte du volume. Si
une base existante contient encore des données, ne pas y importer le dump :
effectuer d'abord un essai dans une base séparée, puis convenir avec l'équipe
de la bascule et du sort de l'ancienne base. Une restauration peut perdre les
changements intervenus après la date de l'archive.

1. Prévenir l'équipe et garder le service fermé aux utilisateurs. Arrêter
   `frontend` et `backend` avec `docker compose stop frontend backend`.
   Garder `db` disponible. Ne jamais lancer `docker compose down -v` pour
   cette opération : cette option supprime le volume.
2. Récupérer la version correspondante des dépôts, l'artefact ML utilisé
   par le backend, `.env` depuis son stockage sûr, l'archive chiffrée et la
   clé privée GPG depuis son stockage séparé. Vérifier la présence de
   `POSTGRES_PASSWORD` sans l'afficher. Démarrer seulement la base avec
   `docker compose up -d --wait db`.
3. Sur la base neuve, contrôler qu'aucune table applicative n'existe :

   ```sh
   docker compose exec -T db psql -U cardioscope -d cardioscope -Atqc "SELECT to_regclass('public.admins');"
   ```

   La sortie doit être vide. Si `admins` apparaît, s'arrêter : la base
   n'est pas vide.
4. Toujours depuis `CardioScope-APP` dans Git Bash, importer le flux
   déchiffré sans créer de dump en clair sur le disque hôte :

   ```sh
   set -o pipefail
   gpg --decrypt backups/NOM_DU_FICHIER.dump.gpg | docker compose exec -T db pg_restore -U cardioscope --no-owner --no-acl -d cardioscope
   ```

   `pipefail` fait échouer l'ensemble si GPG ou `pg_restore` échoue. Ne
   poursuivre que si la commande se termine sans erreur. Si l'import échoue,
   conserver le service fermé et repartir d'une **nouvelle base vide** ;
   ne pas superposer plusieurs imports incomplets.
5. Avant toute réouverture, retirer **toutes** les sessions restaurées, les
   contextes CSRF, les compteurs temporaires et l'historique des simulations.
   Ce choix évite de réexposer une simulation supprimée après la date de
   la sauvegarde. Le compte admin est conservé :

   ```sh
   docker compose exec -T db psql -v ON_ERROR_STOP=1 -U cardioscope -d cardioscope -c "BEGIN; DELETE FROM csrf_contexts; DELETE FROM admin_sessions; DELETE FROM login_attempt_windows; DELETE FROM simulations; COMMIT;"
   ```

   Si cette transaction échoue, ne pas ouvrir le service. Vérifier que les
   quatre compteurs sont à zéro et que le compte admin est présent et actif :

   ```sh
   docker compose exec -T db psql -v ON_ERROR_STOP=1 -U cardioscope -d cardioscope -c "SELECT (SELECT count(*) FROM admin_sessions) AS sessions, (SELECT count(*) FROM csrf_contexts) AS csrf, (SELECT count(*) FROM login_attempt_windows) AS tentatives, (SELECT count(*) FROM simulations) AS simulations, (SELECT count(*) FROM admins WHERE active) AS admins_actifs;"
   ```

6. Vérifier la révision du schéma avec le [guide des migrations](migrations-initialisation-admin.md)
   et appliquer les migrations manquantes **avant** de rouvrir :

   ```sh
   docker compose build backend
   docker compose run --rm --no-deps backend python -m alembic current
   docker compose run --rm --no-deps backend python -m alembic upgrade head
   docker compose run --rm --no-deps backend python -m alembic current
   ```

   `upgrade head` applique seulement les migrations absentes. Vérifier que
   la dernière commande indique la révision attendue par cette version du
   backend. Vérifier ensuite les accès, démarrer les services avec
   `docker compose up -d --build`, puis effectuer une **nouvelle** connexion
   admin et les contrôles fonctionnels prévus par l'équipe. Les anciennes
   sessions ne doivent plus fonctionner. Prévenir l'admin que l'historique
   restauré a été volontairement vidé. Rouvrir seulement après ces contrôles.

## Exercice local du 28 novembre 2026

- Base Docker PostgreSQL 17 disponible et `healthy` ; base principale
  `cardioscope` laissée intacte.
- Le script de sauvegarde a créé
  `backups/cardioscope-20261128T042052Z.dump.gpg` (3 085 octets). Ce fichier
  et l'archive antérieure de 03:35 UTC ont été reconnus comme archives
  chiffrées GPG et lus par `pg_restore --list` après déchiffrement en flux.
- `scripts/verify_backup_restore.sh` exécuté avec succès : restauration dans
  une base temporaire pour chacune des deux archives, tables attendues
  présentes, lignes fictives ajoutées puis nettoyées, un compte admin
  conservé, bases temporaires supprimées.
- Syntaxe Bash des scripts contrôlée. Aucun mot de passe, clé privée ou dump
  déchiffré n'a été enregistré dans le dépôt.

Cet exercice ne prouve pas qu'une tâche quotidienne est déjà planifiée, qu'une
copie hors du poste existe ou qu'une connexion admin a réussi après un sinistre.
Ces contrôles restent à faire dans le contexte réel d'exploitation avant
d'annoncer une reprise complète du service.
