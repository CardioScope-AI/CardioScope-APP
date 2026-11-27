# Catalogue des modèles évalués

Extension du contrat : Random Forest reste le seul prédicteur actif. XGBoost
est disponible pour consulter ses performances, sans sélection d’algorithme
dans le formulaire de simulation. SVM et régression logistique ne sont pas
affichés tant que leurs exports et leur prise en charge ne sont pas validés.

## GET /models

Session administrateur requise, même cookie que `/model-info`. Réponse JSON
200 avec `Cache-Control: no-store`. L’objet contient `schema_version: 1`,
`active_model_version` (chaîne) et `models` (tableau de fiches).
Voir [l’exemple complet issu de la vérification HTTP](exemples/catalogue-modeles.json).
Chaque fiche reprend le
schéma réel de `/model-info` (version, SHA-256 du pipeline, `model_name`, dataset,
13 variables, cible, évaluation, limites). `model_name` accepte
`RandomForestClassifier` ou `XGBClassifier`. L’évaluation contient les tailles
train/test, les plis CV, les moyennes CV, les scores du test et la matrice de
confusion. La spécificité CV est facultative et vaut null si non fournie.
Les scores sont compris entre 0 et 1, null pour une mesure absente. Les versions
sont uniques et la version active apparaît exactement une fois.

401 : `unauthenticated`. 503 : `catalog_unavailable`, enveloppe `error` existante.
Une release comparative déclarée mais absente ou invalide rend le catalogue
indisponible ; aucune fiche partielle trompeuse n’est renvoyée. Le prédicteur
actif, `/health` et `/model-info` restent indépendants du catalogue.

`/model-info` conserve la fiche du modèle actif. `/predict` et son payload ne
changent pas. Lire une fiche XGBoost ne modifie jamais `MODEL_PATH`.

## Validation et déploiement

DATA-ML exporte une release immuable `xgb-cleveland-v1`, avec pipeline, métadonnées,
rapport, manifeste et trace de vérification. L’exporteur recalcule les scores du
test avec l’objet sauvegardé et les scores CV avec des copies, dans le même
environnement Linux que l’entraînement. Les empreintes lient les trois fichiers
principaux. Les hashes garantissent la cohérence, pas l’identité du producteur.

Le backend prend au démarrage une liste de chemins administrés, séparés par des
virgules, dans `COMPARISON_MODEL_PATHS`. Il vérifie les hashes et le schéma, mais
ne désérialise pas les pipelines de comparaison. Il n’a donc pas besoin de la
bibliothèque XGBoost pour consulter les scores. Les chemins ne viennent pas
d’une requête HTTP et ne sont pas exposés dans la réponse.

Dans APP, conserver `MODEL_PATH=/models/releases/rf-cleveland-v1/pipeline.joblib`
et ajouter `COMPARISON_MODEL_PATHS=/models/releases/xgb-cleveland-v1/pipeline.joblib`
au `.env` local. Les pipelines joblib restent hors de Git : transférer le dossier
complet depuis une source de confiance et le vérifier dans DATA-ML.
Puis lancer `docker compose up -d --build`.

Le frontend utilise `/api/models` via le proxy Nginx. Il affiche le rôle de
chaque modèle, le comparatif CV/test, et un sélecteur de détail (scores, matrice,
limites). Aucun score SVM/logistique n’est inventé. Un 401 renvoie à la connexion ;
un 503 ou une panne réseau affiche un message et un bouton pour réessayer.

## Lecture des résultats

Les deux expériences utilisent Cleveland, un split stratifié 80/20 seed 42 et
cinq plis stratifiés mélangés seed 42 sur les 242 observations d’entraînement.
Le test compte 61 observations. La release historique RF ne contient pas toutes
les nouvelles clés de provenance de XGBoost : la comparaison de protocole est
documentée par les expériences, pas déduite des seuls nombres de profils.
Les écarts CV/test ne désignent pas automatiquement un meilleur modèle et ne
constituent pas une validation clinique.
