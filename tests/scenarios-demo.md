# CardioScope · Compte-rendu des tests depuis un deuxième poste

Document de validation de la carte **05 · Tester depuis un deuxième poste** du guide d'intégration CardioScope (ENSA Marrakech · Génie informatique).

---

## 1. Contexte et environnement de test

- **Date des tests** : 18 novembre 2026
- **Machine hôte (serveur)** : Windows avec Docker Compose (`CARDIOSCOPE_BIND_ADDRESS="0.0.0.0"`)
- **Adresse IPv4 du serveur (Wi-Fi local)** : `192.168.10.109`
- **Poste client (deuxième poste)** : Smartphone connecté sur le même réseau Wi-Fi local
- **Navigateur client** : Google Chrome mobile
- **Services testés** :
  - **Frontend** : React 19, Vite, Tailwind CSS v4 sur le port `5173`
  - **Backend** : FastAPI, Uvicorn, Pydantic sur le port `8000`
  - **Modèle ML** : `pipeline.joblib` (RandomForestClassifier entraîné sur Cleveland 80/20)

---

## 2. Résultats des scénarios de test

| # | Scénario | URL testée | Comportement attendu | Résultat observé | Statut |
|---|---|---|---|---|:---:|
| 01 | **Accès à l'API & État du modèle** | `http://192.168.10.109:8000/health` | HTTP 200 avec `{"status":"ready","model_ready":true}` | Réponse 200 OK reçue, modèle chargé au démarrage | **VALIDÉ** |
| 02 | **Accès à l'interface web** | `http://192.168.10.109:5173/#simulation` | La page se charge, responsive et navigation fluide | Interface affichée correctement, formulaires et boutons actifs | **VALIDÉ** |
| 03 | **Profil fictif 01 (Risque faible)** | Formulaire simulation | Pré-remplissage des 13 champs, prédiction : **Classe 0 (Absence)** | Saisies complétées, prédiction : Classe 0, récapitulatif exact | **VALIDÉ** |
| 04 | **Profil fictif 02 (Risque élevé)** | Formulaire simulation | Pré-remplissage des 13 champs, prédiction : **Classe 1 (Présence)** | Saisies complétées, prédiction : Classe 1, récapitulatif exact | **VALIDÉ** |
| 05 | **Profil fictif 03 (Cas de référence)** | Formulaire simulation | Pré-remplissage et prédiction cohérente avec le ML | Saisies complétées et prédiction validée | **VALIDÉ** |
| 06 | **Saisie invalide dans le formulaire** | Formulaire simulation | Blocage de la soumission, champ âge signalé en rouge | Envoi bloqué, message d'erreur visible, focus sur le champ | **VALIDÉ** |
| 07 | **Rejet de requête invalide par l'API** | `http://192.168.10.109:8000/docs` (`POST /predict`) | Code HTTP 422 avec format d'erreur `validation_error` | Code 422 Unprocessable Entity renvoyé sans exposer de trace technique | **VALIDÉ** |
| 08 | **Nouvelle simulation** | Bouton « Nouvelle simulation » | Effacement du résultat précédent et reset du formulaire | Formulaire réinitialisé, prêt pour une nouvelle saisie | **VALIDÉ** |

---

## 3. Synthèse et conclusion

L'ensemble de la chaîne de valeur CardioScope est validé depuis un deuxième poste du réseau local :
- La connectivité réseau et les règles de liaison (`0.0.0.0`) sont opérationnelles.
- Le proxy Frontend relaie correctement les requêtes vers le Backend.
- Le modèle Random Forest produit des prédictions fiables et reproductibles conformes au contrat de données.
- Les mécanismes de sécurité et de validation des saisies (côté client et côté serveur) fonctionnent parfaitement.
## Répétition finale sur l’ordinateur hôte — 19/11/2026

### Parcours local

- Profil 01 : classe affichée = 0
- Profil 02 : classe affichée = 1
- Profil 03 : classe affichée = 0
- Âge effacé : message « Renseignez le champ “Âge”. » ; envoi bloqué = oui
- Âge corrigé : nouvelle prédiction affichée = 0

### Accès par l’adresse Wi-Fi de l’ordinateur hôte

- Adresse testée : `http://192.168.1.161:5173/#simulation`
- Page accessible = oui
- Profil 01 : classe affichée = 0
- Profil 02 : classe affichée = 1
- Profil 03 : classe affichée = 0
- Âge effacé : erreur affichée et envoi bloqué = oui
- Âge corrigé : nouvelle prédiction affichée = 0

**Statut du test du 19/11 : vérifié depuis l’ordinateur hôte. Ce test n’a pas été effectué depuis un deuxième appareil.**

## Test depuis un deuxième appareil — 18/11/2026

Selon le compte-rendu historique de la section 1 à 3, l’application a été ouverte depuis un smartphone connecté au même Wi-Fi, avec Google Chrome mobile. L’API, l’interface, les profils, la saisie invalide et la nouvelle simulation y sont marqués **VALIDÉ**.

**Statut : VALIDÉ pour la version testée le 18/11/2026.** La répétition du 19/11 décrite plus haut a été faite depuis l’ordinateur hôte ; elle ne constitue pas un nouvel essai sur smartphone. Les commits et l’empreinte du pipeline utilisés le 18/11 n’ayant pas été consignés, leur correspondance avec la version finale reste à confirmer.
