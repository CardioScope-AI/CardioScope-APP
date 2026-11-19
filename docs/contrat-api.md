# Contrat API — Validé par l'équipe

`POST /predict` reçoit et renvoie du JSON. Les 13 champs du profil patient sont tous obligatoires. Une valeur absente ou `null` est refusée.

Aucune borne métier n'est encore imposée sur les mesures. Un champ JSON supplémentaire est ignoré.

L'ordre des clés JSON n'est pas imposé au client. Le backend reconstruit les colonnes, sans la cible `num`, dans cet ordre : `age`, `sex`, `cp`, `trestbps`, `chol`, `fbs`, `restecg`, `thalach`, `exang`, `oldpeak`, `slope`, `ca`, `thal`.

| Champ | Type JSON | Sens / encodage |
| --- | --- | --- |
| age | integer | âge en années |
| sex | integer | 0 femme, 1 homme |
| cp | integer | 1 angine typique, 2 angine atypique, 3 douleur non angineuse, 4 asymptomatique |
| trestbps | number | pression au repos, mmHg |
| chol | number | cholestérol sérique, mg/dL |
| fbs | integer | glycémie à jeun > 120 mg/dL : 0 non, 1 oui |
| restecg | integer | 0 normal, 1 anomalie ST-T, 2 hypertrophie ventriculaire gauche |
| thalach | integer | fréquence cardiaque maximale, battements par minute |
| exang | integer | angine à l'effort : 0 non, 1 oui |
| oldpeak | number | dépression du segment ST |
| slope | integer | 1 ascendante, 2 plate, 3 descendante |
| ca | integer | nombre de vaisseaux principaux, 0 à 3 |
| thal | integer | 3 normal, 6 défaut fixe, 7 défaut réversible |

`num` n'est pas une entrée. La classe 0 correspond à `num` égal à 0 (absence de pathologie) et la classe 1 à `num` supérieur à 0 (présence de pathologie).

Exemple d'entrée :
```json
{"age":63,"sex":1,"cp":1,"trestbps":145,"chol":233,"fbs":1,"restecg":2,"thalach":150,"exang":0,"oldpeak":2.3,"slope":3,"ca":0,"thal":6}
```

Exemple de réponse :
```json
{"prediction": 1}
```
`prediction` est un entier : 0 pour l'absence, 1 pour la présence. Aucune probabilité n'est renvoyée.

| Code | Cas |
| --- | --- |
| 200 | Prédiction produite |
| 422 | Données invalides |
| 503 | Pipeline absent ou inutilisable |
| 500 | Erreur interne |

Les erreurs HTTP utilisent le format commun du backend. Pour une donnée invalide :
```json
{"error":{"code":"validation_error","message":"Les données envoyées sont invalides.","fields":[{"location":["body","age"],"message":"Valeur absente ou invalide."}]}}
```
`fields` n'accompagne que le code 422. Le code 503 est `model_unavailable`, avec le message « Le modèle est indisponible. ». Le code 500 est `internal_error`, avec le message « Une erreur interne est survenue. ».

`GET /health` conserve son format propre : 503 avec `{"status":"model_unavailable","model_ready":false}` ou 200 avec `{"status":"ready","model_ready":true}`. Swagger : `/docs`. Le frontend appelle ces routes avec le préfixe `/api`, retiré par le proxy Vite.

## Extensions proposées

La [proposition admin, historique et modèle](contrat-admin-historique.md) prépare les fonctionnalités suivantes dans APP #16. Sa réponse enrichie de prédiction ne sera applicable qu’à la livraison coordonnée du stockage et de son client frontend ; la réponse minimale décrite ci-dessus reste celle de la version actuelle.

### Accès cible : application réservée à l’administrateur

Dans les extensions APP #16, toutes les fonctionnalités métier nécessitent une
session administrateur. `POST /predict` exige aussi une protection CSRF. Le schéma
des 13 champs reste inchangé. Cette protection cible reste à implémenter ; voir
[le contrat admin](contrat-admin-historique.md). Aucun parcours visiteur n’est prévu.
