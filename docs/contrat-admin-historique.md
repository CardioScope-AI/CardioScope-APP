# Contrat des nouvelles fonctionnalités : admin, historique et modèle

- Carte : **CardioScope-APP #16**.
- Version proposée : **extensions v1**, 19 novembre 2026.
- Statut : **validé par l’équipe**, confirmation transmise le 19 novembre 2026 ; extensions non encore implémentées.
- Référence existante : [contrat de prédiction](contrat-api.md).

Ce document fixe une proposition concrète pour que les responsables frontend,
backend, ML et déploiement puissent développer les mêmes échanges. Une règle
ci-dessous est la référence commune validée par l’équipe. Les durées de
conservation des simulations et sauvegardes sont proposées dans
[la politique APP #17](regles-conservation.md), également validée par l’équipe.

## 1. Parcours et choix proposés

- Application exclusivement réservée au compte administrateur : connexion obligatoire
  pour le formulaire, le résultat, le PDF, l’historique et la fiche du modèle.
  Seuls des profils fictifs sont acceptés ; aucun parcours visiteur.
- Un unique administrateur consulte et supprime l’historique global. Il est créé
  par une commande d’initialisation ; aucune inscription publique n’est ajoutée.
- La consultation publique de l’historique n’existe pas, même si l’identifiant
  d’une simulation est connu.
- Base proposée : **PostgreSQL**, accès SQLAlchemy et migrations Alembic.
- Authentification proposée : **session serveur avec jeton opaque en cookie**.
  Les mots de passe sont hachés avec une bibliothèque de hachage de mots de passe.
  Aucun mot de passe ou jeton n’est placé dans le code source ou les logs.
- Le frontend appelle `/api/...` ; le proxy relaie vers FastAPI en retirant `/api`.
  Une seule origine frontend/API est privilégiée, en local comme au déploiement.
- Aucun historique enregistré ne devient automatiquement une donnée d’entraînement.

## 2. Conventions communes

- Corps de requête et réponse : `application/json`, sauf réponse `204`, sans corps.
- Identifiants admin/simulation : chaînes UUID ; aucune signification métier.
- Dates : ISO 8601 en UTC avec suffixe `Z`, par exemple `2026-11-19T14:30:00Z`.
- Un identifiant de release ML est une chaîne immuable ; `artifact_sha256` contient
  exactement 64 caractères hexadécimaux minuscules.
- Ne jamais renvoyer mot de passe, hash de mot de passe, hash de session, jeton de
  session ou chemin local de fichiers dans une réponse JSON.
- Les réponses admin et CSRF portent `Cache-Control: no-store`.
- Les clés JSON ne sont pas ordonnées par le client ; le backend reconstruit les
  colonnes du modèle suivant le contrat de prédiction actuel.
- Les 13 mesures restent obligatoires, finies et non nulles ; les catégories et
  les types `integer`/`number` restent ceux du contrat actuel.

## 3. Tableau des routes cibles

Les chemins ci-dessous sont ceux de FastAPI ; le navigateur ajoute `/api`.
Les nouvelles routes ne doivent pas être présentées comme déjà disponibles.

| Méthode | Route | Accès | Succès | Principales erreurs |
| --- | --- | --- | --- | --- |
| GET | `/health` | Public | 200 | 503, format historique conservé |
| POST | `/predict` | Admin + CSRF | 200 | 401, 403, 422, 503, 500 |
| GET | `/model-info` | Admin connecté | 200 | 401, 503 |
| GET | `/admin/csrf` | Public ou admin | 200 | 503 |
| POST | `/admin/login` | Public + protection CSRF | 200 | 401, 403, 422, 429, 503 |
| GET | `/admin/me` | Admin connecté | 200 | 401, 503 |
| POST | `/admin/logout` | Contexte CSRF valide | 204 | 403, 503 |
| GET | `/admin/simulations` | Admin connecté | 200 | 401, 422, 503 |
| GET | `/admin/simulations/{id}` | Admin connecté | 200 | 401, 404, 422, 503 |
| DELETE | `/admin/simulations/{id}` | Admin + CSRF | 204 | 401, 403, 404, 422, 503 |

`/admin/csrf` est une route de support nécessaire au parcours de connexion
proposé. Elle appartient à la mise en œuvre des sessions, pas à une nouvelle
inscription. Seuls le login, son support CSRF et la sonde technique /health
restent accessibles sans session. Swagger et OpenAPI sont limités au
développement ou protégés au déploiement.

## 4. Session et protection des actions admin

### 4.1 Cookie de session

Nom proposé : `cardioscope_admin`. Jeton aléatoire d’au moins 32 octets, créé
à chaque connexion réussie ; seul son hash est conservé côté serveur.

| Attribut / règle | Proposition |
| --- | --- |
| HttpOnly | Toujours activé ; le frontend ne lit pas ce cookie |
| Secure | Activé en HTTPS ; désactivé seulement pour le développement HTTP local |
| SameSite | `Lax` pour le déploiement même origine prévu |
| Path | `/`, compatible avec accès direct et proxy `/api` |
| Domain | Non défini : cookie limité à l’hôte qui le reçoit |
| Expiration absolue | 8 heures après le login |
| Inactivité | Expiration après 30 minutes sans requête admin authentifiée réussie |
| Max-Age | 28 800 secondes au maximum ; l’expiration serveur reste décisive |

Le backend contrôle expiration, révocation et compte actif sur chaque route
privée. Le frontend appelle `/admin/me` au chargement et efface les données admin
en mémoire après un `401` ou une déconnexion. Un cookie présent ne prouve pas une
session valide. Une modification du mot de passe révoque toutes les sessions.

Plusieurs sessions du même compte sont permises ; logout révoque la session
courante. L’initialisation doit empêcher la création d’un deuxième administrateur.

### 4.2 CSRF : séquence contractuelle

1. Le frontend demande `GET /admin/csrf`, avec cookies. Le serveur crée ou retrouve
   un contexte CSRF et répond avec `csrf_token`. Avant login, ce contexte est
   anonyme, expire après 10 minutes et ne donne aucun accès admin.
2. Le frontend conserve le jeton CSRF en mémoire et envoie `X-CSRF-Token` lors du
   login, du logout, de POST /predict et d’un DELETE. Le token est lié au contexte serveur et vérifié
   avec lui ; un token fourni sans contexte valide est refusé.
3. Après login, le contexte est renouvelé et lié à la nouvelle session. Le frontend
   redemande `/admin/csrf`. Il peut également le demander après un rechargement.
4. Une session expirée obtient un contexte anonyme, jamais un accès privé.
   Les contextes sont invalidés ou expirent côté serveur.
5. Les écritures admin vérifient aussi l’origine selon la liste configurée.
   Un navigateur non autorisé ou un token manquant/invalide reçoit `403`.
   Les clients de test envoient également l’en-tête Origin attendu.

Le token CSRF n’est pas le jeton de session. Les détails de stockage du contexte
et son cookie de liaison sont à documenter dans BACKEND #18/#20 ; aucune valeur
de session authentifiante ne doit être accessible au JavaScript.

Exemple de `GET /admin/csrf` :

```json
{"csrf_token":"EXEMPLE_DE_TOKEN_CSRF","expires_at":"2026-11-19T14:40:00Z"}
```

Au déploiement même origine, les cookies sont relayés par le proxy. Si l’équipe
retient finalement des origines distinctes, elle doit réviser ici les attributs de
cookie, les origines exactes et les credentials CORS ; pas de wildcard avec cookies.
Le frontend utilisera alors `credentials: "include"`. CORS seul n’est pas une
protection CSRF.

## 5. Connexion, identité et déconnexion

### POST /admin/login

En-têtes : `Content-Type: application/json`, `X-CSRF-Token` et Origin attendu.

```json
{"username":"admin","password":"EXEMPLE_A_REMPLACER"}
```

Les deux champs sont obligatoires et non vides. Le mot de passe n’est jamais
tronqué, trimé ni transformé silencieusement. Un nom d’utilisateur incorrect et un
mot de passe incorrect donnent la même erreur `401 invalid_credentials`.

Succès `200` : en-tête Set-Cookie de session et corps suivant. Les UUID d’exemple
ne représentent pas un identifiant réel.

```json
{
  "admin":{"id":"9de9b841-e261-4d28-8a9a-a8c9f9af214e","username":"admin"},
  "session":{"expires_at":"2026-11-19T22:30:00Z","idle_timeout_seconds":1800}
}
```

Limitation proposée : après 5 échecs sur 15 minutes, un même couple identifiant /
origine réseau est temporairement bloqué ; appliquer aussi une limite globale
par origine réseau. Répondre `429 rate_limited` avec Retry-After en secondes.
Ne pas se fier à un X-Forwarded-For arbitraire ; les proxies de confiance sont
configurés dans APP #20/#21. Le compteur partagé fonctionne avec plusieurs workers.

### GET /admin/me

Succès : même forme `admin` et `session` que le login, avec l’expiration absolue
réelle de la session ; pas de nouveau token authentifiant dans le JSON.
Absence de session ou session invalide/révoquée/expirée : `401 unauthenticated`.
Le frontend n’a pas besoin de distinguer ces causes pour demander une reconnexion.

### POST /admin/logout

En-tête CSRF et origine valides. Révoquer la session puis supprimer son cookie avec
le même Path/Domain. Réponse `204`, sans corps. Si la session a déjà expiré, un
contexte CSRF anonyme obtenu via `/admin/csrf` permet de nettoyer les cookies et de
répondre encore `204`. Une ancienne session ne redevient jamais utilisable.

## 6. Prédiction et enregistrement des simulations

### Requête existante

Les 13 champs et leurs encodages restent définis dans `contrat-api.md`.
Session admin valide, origine autorisée et X-CSRF-Token obligatoires.
Sans session : 401 ; CSRF refusé : 403. Aucun calcul ni enregistrement dans
ces cas. L’identité provient de la session, jamais du corps de requête.
Le champ num est exclu. Les saisies restent fictives.

### Réponse cible après livraison de l’historique

Proposition : enrichir la réponse `200` après une prédiction valide ET un commit
réussi en base. Cette forme remplace l’ancienne réponse minimale lors de la
livraison coordonnée de BACKEND #21. L’API actuelle ne l’implémente pas encore.

```json
{
  "prediction":1,
  "simulation_id":"5381f57e-aabc-4635-a3b8-52264d1c4795",
  "created_at":"2026-11-19T14:30:00Z",
  "model_version":"rf-cleveland-release-exemple",
  "artifact_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

Les empreintes et versions dans les exemples sont illustratives, pas celles d’un
artefact livré. `prediction` reste strictement l’entier `0` ou `1`, sans probabilité.
Les champs additionnels doivent être conservés dans l’état de résultat par le
frontend : le client actuel ne retourne que prediction et devra être adapté.
`simulation_id` n’autorise aucune consultation publique de l’historique.

### Règles d’écriture

- Enregistrer une seule ligne par requête réussie : UUID, date UTC, 13 valeurs
  numériques validées, classe, version et SHA-256 du modèle effectivement chargé.
- Ne pas enregistrer de succès pour une validation `422`, un modèle indisponible
  ou une erreur d’inférence. Un échec de commit ne renvoie pas de résultat `200`.
- Si la base est indisponible : `503 storage_unavailable`, et le frontend garde
  les saisies. Ne jamais annoncer un résultat sauvegardé avant confirmation.
- Une coupure réseau peut survenir après un commit ; le frontend ne relance pas
  automatiquement POST /predict. Deux demandes explicites peuvent créer deux
  simulations : ce contrat ne promet pas d’idempotence.
- Ne pas enregistrer nom patient, identifiant personnel, adresse IP ou token dans
  la ligne de simulation. Les limites du login sont traitées séparément.
- La version et le hash proviennent du pipeline et de ses métadonnées contrôlés
  ensemble au démarrage ; ne pas relire une version indépendante à chaque requête.

Si l’équipe veut un mode prédiction sans stockage lors d’une panne DB ou une clé
d’idempotence, elle doit amender ce paragraphe avant l’implémentation.

## 7. Consultation de l’historique

### GET /admin/simulations

Session admin obligatoire. Paramètres proposés :

| Paramètre | Type / défaut | Règle |
| --- | --- | --- |
| page | integer, 1 | Minimum 1 |
| page_size | integer, 20 | Entre 1 et 100 |
| prediction | integer, facultatif | 0 ou 1 |
| created_from | date-heure UTC, facultative | Borne inclusive |
| created_before | date-heure UTC, facultative | Borne exclusive |

Trier par created_at décroissant, puis id décroissant pour stabiliser les égalités.
Si les bornes sont inversées ou invalides, répondre 422. La pagination par page
n’est pas un instantané : une nouvelle simulation peut décaler les pages ; le
frontend recharge après une création/suppression.

Réponse `200`, avec total correspondant aux filtres. Une page hors de la dernière
page disponible renvoie items vide, pas 404.

```json
{
  "items":[{
    "id":"5381f57e-aabc-4635-a3b8-52264d1c4795",
    "created_at":"2026-11-19T14:30:00Z",
    "prediction":1,
    "model_version":"rf-cleveland-release-exemple",
    "summary":{"age":63,"trestbps":145,"chol":233}
  }],
  "page":1,
  "page_size":20,
  "total":1
}
```

### GET /admin/simulations/{id}

ID UUID syntaxiquement incorrect : 422. Session invalide : 401. Avec session valide,
un identifiant valide absent ou supprimé : 404. La vérification de session précède
l’accès à la ligne en base. Réponse complète `200` :

```json
{
  "id":"5381f57e-aabc-4635-a3b8-52264d1c4795",
  "created_at":"2026-11-19T14:30:00Z",
  "prediction":1,
  "model_version":"rf-cleveland-release-exemple",
  "artifact_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "profile":{
    "age":63,"sex":1,"cp":1,"trestbps":145,"chol":233,"fbs":1,
    "restecg":2,"thalach":150,"exang":0,"oldpeak":2.3,"slope":3,"ca":0,"thal":6
  }
}
```

Cette version est celle du calcul historique, pas nécessairement celle du modèle
actuellement chargé. La suppression/purge est définie avec APP #17.

### DELETE /admin/simulations/{id}

Session et protection CSRF obligatoires. Succès 204 sans corps, sans suppression
d’artefact ML. ID invalide : 422 ; ligne déjà absente ou supprimée : 404. La méthode
de suppression physique/logique et les délais sont arrêtés dans APP #17.
Le frontend affiche une confirmation puis attend la réponse serveur avant de
retirer l’élément. Une copie PDF déjà exportée ne peut pas être effacée à distance.

## 8. Informations du modèle pour l’admin

### GET /model-info

Session administrateur obligatoire ; sinon 401. Exposer les métadonnées validées du modèle chargé, sans
chemin local ni fichier joblib. Réponse `200` proposée ; les valeurs null indiquent
une métrique non fournie, jamais zéro par défaut.

```json
{
  "schema_version":1,
  "model_version":"rf-cleveland-release-exemple",
  "artifact_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "model_name":"RandomForestClassifier",
  "dataset":"UCI Heart Disease / Cleveland",
  "features":["age","sex","cp","trestbps","chol","fbs","restecg","thalach","exang","oldpeak","slope","ca","thal"],
  "target":{"0":"absence","1":"présence"},
  "evaluation":{
    "train_samples":242,"test_samples":61,"cv_folds":5,
    "cv_metrics":{"accuracy":null,"precision":null,"recall":null,"f1":null,"roc_auc":null},
    "test_metrics":{"accuracy":null,"precision":null,"recall":null,"specificity":null,"f1":null,"roc_auc":null},
    "confusion_matrix":null
  },
  "limitations":["Démonstrateur pédagogique ; ceci ne constitue pas un diagnostic médical."]
}
```

Lorsqu’elle est fournie, confusion_matrix est un objet avec true_negative,
false_positive, false_negative et true_positive, tous entiers positifs ou nuls.
La somme doit égaler test_samples. Les métriques sont des nombres entre 0 et 1,
convertis en pourcentage seulement pour l’affichage. CV et test restent distincts.
Version obligatoire et non vide ; release absente, malformée ou incohérente :
503 `model_unavailable`. Une erreur de lecture de la fiche ne doit pas remplacer
silencieusement les métriques par des valeurs inventées.

DATA-ML #19/#22 doit produire les champs correspondants. DATA-ML #21 valide la
cohérence avant livraison. Le backend charge un ensemble atomique pipeline /
métadonnées / rapport pour ne pas mélanger deux releases.

## 9. Erreurs communes cibles

Conserver l’enveloppe error déjà présente dans le backend. Les nouvelles erreurs
ci-dessous doivent être ajoutées explicitement : le gestionnaire générique actuel
ne les crée pas toutes et transforme tout HTTPException 503 en model_unavailable.
Il devra notamment distinguer storage_unavailable dans BACKEND #21.

```json
{"error":{"code":"unauthenticated","message":"Connectez-vous pour accéder à cet espace."}}
```

| HTTP | error.code | Utilisation |
| --- | --- | --- |
| 401 | invalid_credentials | Login refusé, cause non révélée |
| 401 | unauthenticated | Session absente, révoquée ou expirée |
| 403 | csrf_failed | Origine ou token CSRF refusé |
| 404 | not_found | Simulation absente après autorisation |
| 422 | validation_error | Champs JSON ou paramètres invalides ; fields disponible |
| 429 | rate_limited | Trop de tentatives de login, en-tête Retry-After |
| 503 | model_unavailable | Release ML indisponible/incohérente |
| 503 | storage_unavailable | Base indisponible ou écriture impossible |
| 500 | internal_error | Erreur inattendue ; détail dans les logs serveur |

Ne pas renvoyer les valeurs reçues ni les détails techniques dans fields.
Le format de validation reste celui du contrat actuel : location et message.
Les exceptions du middleware CORS peuvent conserver leur réponse propre aux
pré-vérifications ; ce tableau concerne les routes applicatives.

## 10. Modèle de données logique proposé

Les noms exacts des colonnes et migrations appartiennent à BACKEND #16.

| Entité | Contenu minimal | Contraintes |
| --- | --- | --- |
| Admin | id, username, password_hash, active | Un seul compte, unicité garantie en base |
| AdminSession | id, admin_id, token_hash, created_at, expires_at, last_seen_at, revoked_at | Token unique, aucune valeur brute de session stockée |
| Simulation | id, created_at, profile, prediction, model_version, artifact_sha256 | Profil validé, classe 0/1, version/hash de l’inférence |
| Contexte CSRF | identifiant/contexte, token vérifiable, expiration, lien session après login | N’accorde aucun accès admin ; stockage à documenter |
| Limitation login | clé de limitation, fenêtre et compte d’échecs | Partagée entre workers et bornée dans le temps |

L’historique regroupe les simulations de l’unique administrateur connecté.
Aucun compte visiteur ni inscription publique n’existe. Une migration ne crée pas de compte avec un mot de
passe par défaut ; la commande d’initialisation est distincte.

## 11. Livraison et compatibilité

1. Appliquer les choix validés de ce contrat et la politique de conservation APP #17.
2. Livrer schémas ML et migrations, puis sessions, autorisations et stockage.
3. Livrer model-info et routes admin avec schémas OpenAPI des erreurs réelles.
4. Adapter les clients frontend : réponse enrichie de predict, CSRF, cookies,
   identité, liste/détail/suppression et page du modèle.
5. Protéger les vues métier frontend et rediriger vers la connexion après un 401.
   Configurer la base persistante (APP #18), puis le proxy du frontend compilé
   (APP #21) et les sessions au déploiement (APP #20).
6. Vérifier le refus des accès anonymes aux routes métier, puis rejouer la
   simulation authentifiée, le parcours admin et les pannes DB/API
   dans la recette APP #23. L’historique n’est pas promis avant cette livraison.

Les scripts existants qui vérifient l’égalité stricte de la réponse minimale de
predict doivent être adaptés à la nouvelle forme, en vérifiant ses champs plutôt
qu’en supposant l’absence de clés supplémentaires. Les tests actuels de /health
restent valables : son format n’est pas modifié et la disponibilité du modèle n’est
pas assimilée à une vérification complète de la base.

## 12. Relecture de la carte APP #16

- [ ] Backend : routes, autorisation, erreurs, transactions et mode de session.
- [ ] Frontend : exemples consommables, CSRF, cookies, pagination et résultat enrichi.
- [ ] ML : identifiant immuable, empreinte et schéma public cohérents avec les exports.
- [ ] Déploiement : PostgreSQL, migrations, même origine et HTTPS cible.
- [x] Équipe : validation des choix et de la règle de conservation #17, confirmée le 19 novembre 2026.

La tâche documentaire est validée ; elle ne crée ni les tables ni les
nouvelles routes dans cette branche.

Références techniques :
- [OWASP : sessions](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [OWASP : CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
