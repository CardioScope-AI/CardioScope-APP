# CardioScope · Application

Intégration de l’application étudiante, configuration et déploiement local. Les quatre dépôts doivent être voisins :
```text
CardioScope/
  CardioScope-APP/
  CardioScope-BACKEND/
  CardioScope-DATA-ML/
  CardioScope-FRONTEND/
```

| Dépôt | Rôle |
| --- | --- |
| [FRONTEND](https://github.com/CardioScope-AI/CardioScope-FRONTEND) | React, Vite, Tailwind |
| [BACKEND](https://github.com/CardioScope-AI/CardioScope-BACKEND) | FastAPI et chargement du pipeline |
| [DATA-ML](https://github.com/CardioScope-AI/CardioScope-DATA-ML) | Données, notebooks, scripts, export |
| [APP](https://github.com/CardioScope-AI/CardioScope-APP) | Intégration, Compose, contrat partagé |

## Démarrage commun Windows et Linux
Prérequis : Git, Docker avec moteur Linux actif et Docker Compose v2 ou ultérieur. Sous Windows : Docker Desktop démarré, backend WSL2 configuré et accès aux dossiers autorisé. Ports 5173 et 8000 libres. Internet requis au premier build. Aucun Python ou Node sur l’hôte n’est requis avec Docker.

Depuis `CardioScope-APP` :
```text
docker compose config
docker compose up --build
```
Ouvrir **http://localhost:5173/** ou **http://localhost:5173/#simulation**. Swagger : http://localhost:8000/docs. API via proxy : http://localhost:5173/api/health.

Les services démarrent sans modèle. Le frontend attend seulement le démarrage du backend, pas une réponse 200 de `/health`. Le 503 attendu signifie « modèle indisponible », pas un échec de démarrage.

Dans un second terminal, depuis App :
```text
docker compose ps
docker compose logs --tail=50 backend frontend
curl.exe -i http://localhost:5173/
curl.exe -i http://localhost:8000/docs
curl.exe -i http://localhost:5173/api/health
```
Sous Linux remplacer `curl.exe` par `curl`. Réponses attendues : 200 pour l’interface et Swagger, 503 avec `model_ready: false` pour health sans pipeline. Dans le navigateur, le bouton de disponibilité doit afficher « API accessible · modèle non disponible ». Le frontend utilise `/api` et le proxy Vite contacte `http://backend:8000` sur le réseau Compose.

Arrêt : Ctrl+C puis `docker compose down`, ou `docker compose down` depuis un second terminal. Pour démarrer en arrière-plan : `docker compose up --build -d`. Après modification des sources : relancer avec `--build` (pas de montage des sources). Après export du modèle : `docker compose restart backend`.

## Versions et pipeline
Images fixées : Node `24.15.0-bookworm-slim`, Python `3.13.7-slim-bookworm`. Frontend installé par `npm ci` et son lockfile, compilé pendant le build Docker puis servi depuis `dist/` avec la commande Compose `npm run preview` ; dépendances Python versionnées dans requirements.txt. Les tags fixent les versions d’exécution, mais pas les correctifs du système de base ni les dépendances Python transitives.

Le dossier voisin `../CardioScope-DATA-ML/artifacts` existe dès le clonage et est monté en lecture seule dans `/models`. Le futur `pipeline.joblib` n’est pas nécessaire au démarrage. Backend et ML partagent les versions Python/scikit-learn/joblib/NumPy/SciPy ; voir leurs README. ML reste une image et une commande séparées, sans entraînement dans Compose.

## Démarrage sans Docker sur Windows
Depuis le dossier parent, avec Python 3.13.7 et Node 24.15.0 :
```powershell
cd .\CardioScope-BACKEND
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Dans un second terminal, depuis le dossier parent :
```powershell
cd .\CardioScope-FRONTEND
npm.cmd ci
npm.cmd run dev
```
Compilation frontend : `npm.cmd run build`. Utiliser directement le Python du venv évite de modifier la politique d’exécution PowerShell. Arrêt : Ctrl+C dans chaque terminal.

## Répartition initiale proposée pour cinq membres
1. Interface et accessibilité : accueil et future simulation dans FRONTEND.
2. API : validation, erreurs et future route `/predict` dans BACKEND.
3. Données : provenance, nettoyage et exploration dans DATA-ML/notebooks.
4. ML : évaluation, pipeline et export dans DATA-ML/scripts ; coordonner les fichiers avec le membre données.
5. Intégration : Compose, documentation et validation du contrat dans APP.

Le [contrat API](docs/contrat-api.md) est un brouillon : champs, types, encodages et codes HTTP à confirmer ensemble. `/predict` n’est pas encore implémenté. Le démonstrateur ne fournit aucun diagnostic médical.

## Vérifications effectuées le 8 novembre 2026

- Les quatre dépôts étaient propres avant modification ; leurs remotes `origin` correspondent aux liens ci-dessus. Les quatre README existants ont été lus.
- Windows : Node 24.15.0, Python 3.13.7. Installation frontend, puis réinstallation `npm ci` depuis le cache et compilation `npm run build` réussies avec Vite 8.3.6 et Tailwind 4.3.5. L’installation finale npm n’a signalé aucune vulnérabilité.
- Installation des requirements backend réussie ; `pip check` ne signale aucune dépendance cassée. Imports scikit-learn 1.6.1, joblib 1.4.2, NumPy 2.2.6 et SciPy 1.15.3 vérifiés.
- Serveurs Vite et Uvicorn réellement démarrés en local : HTTP 200 pour `/`, `/src/main.js`, `/docs` et `/openapi.json`. HTTP 503 et `model_ready: false` pour `/health` et pour `/api/health` via le proxy Vite. Aucun pipeline présent lors de ces essais.
- `docker compose config` réussi. `docker compose up --build -d` tenté mais bloqué par le moteur Docker Desktop Linux arrêté (pipe `dockerDesktopLinuxEngine` absent). Aucun build d’image ni réseau Docker validé ; relancer les commandes ci-dessus après démarrage de Docker Desktop.
- Aucun test visuel ou JavaScript dans un navigateur effectué. Aucun entraînement, export ML ou chargement de pipeline réel testé. L’image ML n’a pas été construite.
- Les serveurs lancés pour les contrôles ont été arrêtés. Aucun commit ni push.

## Compiler et servir le frontend (APP #4)

La version compilée se trouve dans `CardioScope-FRONTEND/dist/`. Elle se distingue du serveur de développement : pas de client Vite de développement ni d'aperçu des résultats simulés. Le serveur de démonstration Vite Preview conserve le proxy `/api` défini dans `vite.config.js` ; ne pas ouvrir `dist/index.html` directement ni utiliser un serveur statique sans proxy pour tester l'API.

### Sans Docker sur Windows

Depuis `CardioScope-FRONTEND`, arrêter le serveur de développement s'il occupe le port 5173, puis :

```powershell
npm.cmd ci
npm.cmd run build
npm.cmd run preview -- --host 127.0.0.1
```

`npm ci` réinstalle les dépendances du lockfile. Lancer le backend séparément sur le port 8000 selon son README. Ouvrir `http://127.0.0.1:5173/`, puis les vues `/#simulation` et `/#performances`. Les liens avec `#` sont traités dans le navigateur.

Pour utiliser un backend sur une autre adresse, définir la cible avant de lancer Preview :

```powershell
$env:API_PROXY_TARGET="http://127.0.0.1:8000"
npm.cmd run preview -- --host 127.0.0.1
```

### Sans Docker sous Linux

Avec Node 24.15.0 installé sous Linux, depuis le dépôt frontend :

```sh
npm ci
npm run build
API_PROXY_TARGET=http://127.0.0.1:8000 npm run preview -- --host 127.0.0.1
```

Pour consulter depuis un autre poste du réseau, remplacer l'hôte d'écoute par `0.0.0.0` et utiliser l'adresse IP du serveur dans le navigateur. La cible du proxy reste l'adresse du backend joignable depuis le processus Preview. Ne pas réutiliser les `node_modules` Windows pour une installation Linux ; préférer un clone séparé dans le système de fichiers Linux.

### Avec Docker Compose

Le Dockerfile du dépôt FRONTEND exécute déjà `npm ci` puis `npm run build`. Dans ce dépôt APP, `compose.yaml` remplace maintenant sa commande de démarrage de développement par `npm run preview`. La cible du proxy reste `http://backend:8000`. Aucun changement du Dockerfile frontend n'est nécessaire.

```sh
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose logs --tail=50 frontend backend
```

Après modification des sources frontend, reconstruire l'image avec `docker compose up --build -d`. Arrêt : `docker compose down`.

### Vérification HTTP reproductible

Depuis le dépôt APP, avec Node 24.15.0 :

```sh
node scripts/verify-frontend.mjs http://127.0.0.1:5173
node scripts/verify-frontend.mjs http://127.0.0.1:5173 --with-api
```

Le premier contrôle exige un HTML compilé sans client Vite de développement, puis vérifie le chargement des fichiers JS/CSS et leurs types MIME. Le second contrôle vérifie aussi le proxy `/api/health` : 200 si modèle prêt, ou 503 avec le format attendu si modèle absent. Un 503 attendu prouve que le proxy atteint le backend ; ce n'est pas un échec de service du frontend. Une panne réseau ou un format health inattendu fait échouer le contrôle.

Ces contrôles HTTP ne remplacent pas le test dans le navigateur : navigation entre les trois vues, affichage mobile, saisie du formulaire et résultat réel lorsque `/predict` sera disponible. Aucun score ni prédiction simulée n'est utilisé pour prouver une intégration réelle.

### Périmètre et état de validation

Vite Preview sert à la démonstration locale de la compilation ; ce n'est pas un serveur de production. Un déploiement public nécessitera un serveur adapté (par exemple un reverse proxy avec service des fichiers statiques) et une configuration dédiée.

La compilation locale a réussi. Les contrôles HTTP du build et du proxy sont exécutés avec des processus Preview et Uvicorn temporaires sous Windows. Le lancement Linux natif reste à vérifier après installation de son environnement. Docker Compose est validé syntaxiquement ; le démarrage des conteneurs reste à vérifier lorsque le moteur Docker Linux sera disponible. Les sources frontend vérifiées sont celles présentes dans le dépôt voisin au moment du test ; le README ne prétend pas valider des branches GitHub non récupérées.
