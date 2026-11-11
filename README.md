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

La compilation locale a réussi. Les contrôles HTTP du build et du proxy sont exécutés avec des processus Preview et Uvicorn temporaires sous Windows. Le lancement compilé est également vérifié sous Ubuntu/WSL2 ; voir le rapport `docs/verification-frontend-linux.json`. Docker Compose est validé syntaxiquement ; le démarrage des conteneurs reste à vérifier lorsque le moteur Docker Linux sera disponible. Les sources frontend vérifiées sont celles présentes dans le dépôt voisin au moment du test ; le README ne prétend pas valider des branches GitHub non récupérées.

## Vérifier FastAPI sous Linux (APP #3)

Ce contrôle s'exécute réellement sous Linux (Ubuntu natif ou WSL), avec Python 3.13.7 et les dépendances du dépôt backend. Il ne remplace pas une démonstration depuis un autre poste et ne valide ni Docker ni les prédictions d'un modèle entraîné.

### Préparation Ubuntu / WSL depuis Windows

Ouvrir Ubuntu avec `wsl -d Ubuntu`. Les chemins Windows sont accessibles sous `/mnt/c/`. Conserver l'environnement Python Linux dans le dossier personnel Linux pour éviter de remplacer le `.venv` Windows et pour accélérer l'installation :

```sh
export PATH="$HOME/.local/bin:$PATH"
uv python install 3.13.7
uv venv --python 3.13.7 "$HOME/.local/share/cardioscope/backend-venv"
cd "/mnt/c/Users/pc/Desktop/ENSA/CI 2/mine/AI/CardioScope/CardioScope-BACKEND"
uv pip install --python "$HOME/.local/share/cardioscope/backend-venv/bin/python" -r requirements-dev.txt
```

Ces commandes supposent `uv` déjà installé. Sur un autre poste, adapter le chemin du projet. Les dépôts APP et BACKEND doivent être voisins, avec les branches contenant les gestionnaires d'erreurs, la configuration CORS et les tests récupérées côté backend. Aucun environnement Windows n'est réutilisé sous Linux.

### Contrôle automatique reproductible

Depuis le dépôt APP, dans Ubuntu :

```sh
"$HOME/.local/share/cardioscope/backend-venv/bin/python" scripts/verify_fastapi_linux.py --report docs/verification-fastapi-linux.json
```

Le script :

- Exige Linux et Python 3.13.7, puis exécute les tests backend.
- Lance Uvicorn sur un port local temporaire, depuis un autre dossier que le backend, avec un chemin de modèle volontairement absent.
- Vérifie `/docs` et `/openapi.json` (200), `/health` sans modèle (503 avec son JSON attendu), une route absente (404) et une méthode incorrecte (405).
- Vérifie une pré-vérification JSON POST autorisée et une origine non autorisée.
- Arrête le serveur temporaire, puis enregistre versions, commit backend, état des sources et résultats dans le rapport demandé.

Le chemin `--backend /chemin/vers/CardioScope-BACKEND` peut être précisé si les dépôts ne sont pas voisins. Les routes 422/500 sont testées uniquement par l'application de test du backend ; aucune route de panne n'est ajoutée au serveur réel. Un OPTIONS réussi sur `/predict` ne démontre pas que cette route est implémentée.

### Lancement manuel et accès depuis Windows

Depuis le dépôt backend dans Ubuntu :

```sh
"$HOME/.local/share/cardioscope/backend-venv/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Dans le navigateur Windows, ouvrir `http://localhost:8000/docs` et `http://localhost:8000/health`. Arrêter avec Ctrl+C. Si le port est déjà occupé, arrêter l'autre backend ou choisir 8001 et adapter les URL. La réponse health 503 est attendue sans modèle. Le lancement manuel reste indépendant du serveur temporaire du contrôle automatique.

### Limites

La validation est acquise uniquement après exécution réussie du script dans Linux ; les commandes seules ne constituent pas une preuve. Le rapport ne doit être ajouté au dépôt qu'après une exécution réelle. Les tests d'inférence et du parcours complet frontend/backend restent dépendants de `/predict` et de l'artefact ML entraîné.

### Validation réalisée sous Ubuntu / WSL2

La vérification complète sans modèle a réussi avec Python 3.13.7 dans Ubuntu/WSL2. Le rapport original est conservé dans [`docs/verification-fastapi-linux.json`](docs/verification-fastapi-linux.json), horodaté `2026-11-11T23:17:38.669833+00:00` (UTC).

- Commit backend testé : `77915455d42f5fc543cfa2af5b8404ee8cd2051e`.
- Les huit tests backend ont réussi.
- Serveur Uvicorn réel : `/docs` et `/openapi.json` répondent 200 ; `/health` répond 503 avec le JSON prévu sans modèle.
- Une route absente répond 404 et une méthode incorrecte répond 405.
- Pré-vérification CORS : origine autorisée 200, origine non autorisée 400.
- Le serveur temporaire a été arrêté à la fin du contrôle.

Le rapport conserve `backend_has_local_changes: true`. Après inspection, Git Windows ne signale aucune modification du backend et les différences signalées par Git WSL disparaissent avec `git diff --ignore-space-at-eol --exit-code` (code 0) : elles correspondent aux fins de ligne du dépôt partagé Windows/Linux, sans différence de code détectée par ce contrôle. Le rapport brut n'a pas été modifié pour masquer cet indicateur.

APP #3 est donc validée pour le lancement local sous Linux/WSL sans modèle. Docker, la prédiction réelle avec `/predict` et l'accès depuis un autre poste du réseau restent hors de cette validation.

## Validation du frontend compilé sous Linux / WSL2

Le contrôle a réussi avec Node Linux 24.15.0 et npm 11.12.1. Le rapport est conservé dans [`docs/verification-frontend-linux.json`](docs/verification-frontend-linux.json) et identifie le commit frontend testé (`00fcc2c877e016f64bcbc25363f22d696f9f1c34`).

Les fichiers suivis par Git du dépôt frontend ont été copiés dans un dossier temporaire du système de fichiers Linux. `npm ci` a installé des dépendances Linux séparées, les neuf tests frontend ont réussi, puis `npm run build` a généré `dist/`. Preview et Uvicorn ont été lancés temporairement sous Linux : le contrôle `scripts/verify-frontend.mjs --with-api` a vérifié le HTML compilé, les deux fichiers JS/CSS et le proxy `/api/health` (503 attendu sans modèle). Les processus et la copie temporaire ont été supprimés à la fin ; les dépendances Windows n'ont pas été remplacées.

La compilation et le service local du frontend sous Linux sont validés. Ce contrôle HTTP n'est pas un test visuel dans un navigateur et ne valide ni Docker ni une prédiction réelle avec `/predict`.
