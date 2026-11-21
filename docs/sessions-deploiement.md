# Sessions au déploiement — APP #20

Le backend utilise des cookies de session `HttpOnly`, `SameSite=Lax` et `Path=/`.
Le cookie de session expire après 8 heures au maximum et après 30 minutes
d’inactivité. Le jeton brut n’est pas stocké dans PostgreSQL. Le cookie `Secure`
est activé par défaut par `AUTH_COOKIE_SECURE=true`.

## Configuration Compose

Dans `.env`, définir les variables transmises au service backend :

```dotenv
AUTH_COOKIE_SECURE=true
CORS_ORIGINS=https://cardioscope.example
```

`CORS_ORIGINS` doit contenir les origines exactes utilisées par le navigateur,
séparées par des virgules : protocole, nom d’hôte et port éventuel, sans chemin
ni slash final. Ne pas utiliser `*`. Le frontend et l’API doivent être présentés
sous le même nom d’hôte afin que le navigateur envoie le cookie au proxy API.
La configuration Compose transmet ces variables à l’API. Après toute
modification, recréer le backend :

```sh
docker compose config --quiet
docker compose up -d --force-recreate backend
```

## HTTPS

Pour un déploiement partagé, terminer TLS sur un reverse proxy et servir le site
en HTTPS. Garder `AUTH_COOKIE_SECURE=true`, conserver les ports des conteneurs
non publiés directement sur Internet et n’autoriser que le trafic HTTPS vers le
proxy. Le proxy doit router `/api` vers le backend et le reste vers le frontend,
sur le même hôte public. Vérifier que le proxy conserve les en-têtes `Origin` et
`X-CSRF-Token` et qu’il ne met pas en cache les réponses d’authentification.

APP fournit une configuration de démonstration locale, pas un reverse proxy TLS
de production. Le certificat, le DNS, le pare-feu et la terminaison TLS doivent
être configurés dans l’environnement d’hébergement.

## Développement local en HTTP

Sur `http://localhost:5173`, les navigateurs n’enverront pas un cookie `Secure`.
Pour un essai local seulement, régler dans `.env` :

```dotenv
AUTH_COOKIE_SECURE=false
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Ne pas conserver ce réglage lors d’un déploiement HTTPS. Si le frontend utilise
un autre port ou nom d’hôte, ajouter son origine exacte à `CORS_ORIGINS`.
L’origine doit correspondre à l’adresse visible dans la barre du navigateur.

## Limites proxy et accès réseau

Le backend utilise l’adresse client de la connexion pour limiter les tentatives
de connexion. Ne pas faire confiance à `X-Forwarded-For` fourni par le client.
La configuration APP ne définit pas de liste de proxies de confiance : placer
l’API derrière un proxy contrôlé qui remplace les en-têtes transmis et traiter
l’adressage réseau côté infrastructure avant d’activer ce support.

Ne pas exposer directement le port backend au réseau public. Le réglage
`CARDIOSCOPE_BIND_ADDRESS=0.0.0.0` est réservé à un réseau de démonstration de
confiance et ne fournit ni HTTPS ni cookies Secure fonctionnels en HTTP.
