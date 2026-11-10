# Brouillon du contrat API · à confirmer avec l’équipe

`POST /predict` : proposition uniquement, route non implémentée. JSON en entrée et en sortie.
Tous les champs, types, unités, encodages, bornes et codes HTTP ci-dessous restent à confirmer avec l’équipe avant développement.

| Champ proposé | Type JSON proposé | Sens / encodage à confirmer |
| --- | --- | --- |
| age | integer | âge en années |
| sex | integer | encodage UCI à confirmer |
| cp | integer | type de douleur thoracique, 1–4 à confirmer |
| trestbps | number | pression au repos, mmHg |
| chol | number | cholestérol, mg/dl |
| fbs | integer | glycémie à jeun > 120 mg/dl, 0/1 |
| restecg | integer | ECG au repos, 0–2 |
| thalach | number | fréquence cardiaque maximale |
| exang | integer | angine à l’effort, 0/1 |
| oldpeak | number | dépression ST |
| slope | integer | pente ST, 1–3 |
| ca | integer | nombre de vaisseaux, 0–3 |
| thal | integer | codes UCI 3/6/7 à confirmer |

Le caractère obligatoire, les valeurs manquantes et l’ordre des colonnes du pipeline sont à confirmer. La cible `num` n’est pas une entrée. La transformation proposée de `num > 0` vers 1 devra être validée lors de la tâche ML.

Exemple d’entrée à valider :
```json
{"age":63,"sex":1,"cp":1,"trestbps":145,"chol":233,"fbs":1,"restecg":2,"thalach":150,"exang":0,"oldpeak":2.3,"slope":3,"ca":0,"thal":6}
```

Exemple de réponse à valider :
```json
{"prediction": 1}
```
Le type integer, les classes 0/1 et leur interprétation restent à confirmer ; aucune probabilité n’est promise.

| Code proposé, à confirmer | Cas proposé |
| --- | --- |
| 200 | Prédiction produite |
| 422 | Données invalides |
| 503 | Pipeline absent ou inutilisable |
| 500 | Erreur interne |

Le format des erreurs reste à définir. Actuellement seul `GET /health` est implémenté : 503 avec `{"status":"model_unavailable","model_ready":false}` ou 200 avec `{"status":"ready","model_ready":true}`. Swagger : `/docs`. Le frontend utilise le préfixe `/api`, retiré par le proxy Vite.
