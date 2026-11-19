# Service du frontend compilé — APP #21

Compose utilise `docker/frontend.Dockerfile` : Node construit le dépôt FRONTEND
voisin avec `npm ci` puis `npm run build`. L’image finale Nginx ne reçoit que
`dist/` et la configuration du serveur. Elle ne lance ni Vite Dev ni Vite Preview.
Le Dockerfile du dépôt FRONTEND reste utilisable pour son propre développement.

## Lancement

Prérequis : Docker Linux actif, Compose 2.17 ou ultérieur (contextes de build
additionnels), les quatre dépôts voisins, et `.env` renseigné selon APP #18.

```sh
docker compose config --quiet
docker compose build frontend
docker compose up -d --wait
docker compose exec -T frontend nginx -t
```

Ouvrir http://localhost:5173. Le port hôte 5173 est dirigé vers Nginx sur 8080.
Si les ports sont occupés, modifier FRONTEND_PORT et BACKEND_PORT dans `.env`
(par exemple 5174 et 8001), puis relancer Compose et adapter l’URL du contrôle.
Ces ports hôte ne changent pas la cible interne du proxy, backend:8000.
Les modifications de code frontend nécessitent une nouvelle compilation d’image.
La sonde du frontend vérifie son HTML indépendamment de la disponibilité du modèle.

## Fichiers et proxy

- `/` et les chemins de navigation servent le frontend ; un rechargement direct
  sur un chemin de navigation renvoie index.html.
- `/assets/` sert les fichiers compilés avec cache long ; un asset absent renvoie
  404, jamais index.html. Le HTML est revalidé pour récupérer les nouveaux builds.
- `/api/...` est transmis à `backend:8000`, en retirant uniquement le préfixe `/api`.
  Paramètres, méthode, corps JSON, cookies et en-tête CSRF sont relayés.
- Les erreurs API gardent leur statut et leur corps ; elles ne deviennent pas une
  page HTML de la SPA. Le proxy ne relance pas automatiquement un POST.
- Le backend est résolu via le DNS Docker pour permettre sa recréation sans
  reconstruire le frontend. Les réponses API ne sont pas mises en cache.
- Les appels API ne sont pas enregistrés dans l’access log Nginx. Le proxy remplace
  X-Forwarded-For par l’adresse du client immédiat plutôt que de faire confiance à
  une valeur fournie par celui-ci. Les logs ne doivent pas contenir de profils ou secrets.

## Vérification

Avec Node sur l’hôte :

```sh
node scripts/verify-frontend.mjs http://127.0.0.1:5173 --with-api --with-nginx --report docs/verification-frontend-nginx.json
```

Contrôler aussi : navigation, rechargement, asset absent (404), validation JSON
de `/api/predict` (422 pour un corps invalide), et réponse API inconnue (404).
La disponibilité `/api/health` peut être 200 si le modèle est prêt ou 503 dans son
format prévu si le modèle est absent. Ne pas présenter un 503 comme une prédiction réussie.

Le proxy laisse passer Set-Cookie et X-CSRF-Token, mais cela ne valide pas un login
qui n’est pas encore implémenté. La protection des routes reste une responsabilité
backend ; le service statique seul ne rend pas l’application privée.

## Limites du déploiement local

Validation HTTP réalisée le 19 novembre 2026 sous Docker Desktop Linux/WSL2,
sur http://127.0.0.1:5174 (backend publié sur 8001 car les ports habituels étaient
occupés). `nginx -t` réussit ; HTML et deux assets compilés servis, santé API 200,
rechargement SPA 200, asset absent 404, route API absente 404 JSON, POST invalide
422 JSON et règles de cache contrôlées. Voir le
[rapport de vérification](verification-frontend-nginx.json).
Le parcours de connexion admin reste à implémenter et n’est pas validé par ces tests.

Le service fourni est HTTP, limité par défaut à 127.0.0.1. Pour une publication,
APP #20 doit configurer HTTPS, les cookies Secure, les origines et les proxies de
confiance. Si un proxy TLS est placé devant Nginx, adapter la transmission du schéma
uniquement en fonction de ce proxy de confiance ; ne pas croire un en-tête client.
La rotation temporelle des logs sur 14 jours reste distincte de ce service.

Référence : [proxy_pass Nginx](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass).
