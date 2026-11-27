# Vérification Docker et Linux — APP #22

Date de vérification : 27 novembre 2026.

## Environnement

- Windows avec Docker Desktop et moteur Linux via WSL2.
- Docker Engine : Linux, `x86_64`, version `29.9.3`.
- Vérifications effectuées depuis PowerShell et depuis Ubuntu/WSL.

## Résultats

- `docker compose config --quiet` : réussi.
- `docker compose ps` : les services `db`, `backend` et `frontend` sont actifs
  et indiqués `healthy`.
- `GET http://localhost:5173/` : HTTP 200, page frontend servie par Nginx.
- `GET http://localhost:8000/docs` : HTTP 200, documentation FastAPI accessible.
- `GET http://localhost:5173/api/health` : HTTP 200, réponse
  `{"status":"ready","model_ready":true}`.
- Depuis Ubuntu/WSL, Docker Engine répond et les URL frontend, documentation
  API et santé du modèle ont également répondu HTTP 200.

## Conclusion et limites

Le démarrage de l’application avec Docker Compose et son accès depuis
Ubuntu/WSL ont été vérifiés. Le modèle était prêt au moment du contrôle.
Cette vérification ne constitue pas un essai depuis un second poste du réseau.
