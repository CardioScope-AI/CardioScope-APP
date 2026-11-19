# CardioScope — Références de la démonstration finale

Date de répétition : 19/11/2026

## Branches et commits utilisés

- APP : branche `feat/08-repetition-version-finale` ; commit final à noter après le commit des documents.
- Backend : branche `main` ; commit `2dabcd`.
- Frontend : branche `main` ; commit `2804fd9`.
- DATA-ML : branche `feat/tache09` ; commit `e4751df`.

## Pipeline et environnement

- Artefact : `CardioScope-DATA-ML/artifacts/pipeline.joblib`
- Empreinte SHA-256 : `E2A61ED695024E2BD627A92F9C2DC9C8BB09A295329645D40505DD6C0877472D`
- Python : 3.13.7
- scikit-learn : 1.6.1
- joblib : 1.4.2
- NumPy : 2.2.6
- SciPy : 1.15.3
- Node : 24.15.0
- Tailwind CSS : 4.3.5
- Docker Desktop : 4.99.0
- Docker CLI : 29.9.3 (build 5457199)
- Docker Compose : v5.7.0
- Machine utilisée le 19/11 : Windows avec Docker Desktop et Ubuntu sous WSL2.

## Répétition Windows et réseau local — 19/11/2026

La répétition sur l’ordinateur hôte et l’accès par son adresse Wi-Fi sont consignés dans [`../tests/scenarios-demo.md`](../tests/scenarios-demo.md).

- Profils 01, 02 et 03 : classes affichées consignées dans le compte-rendu.
- Âge effacé : erreur affichée et envoi bloqué, consignés dans le compte-rendu.
- Âge corrigé : nouvelle prédiction consignée dans le compte-rendu.
- Accès par l’adresse Wi-Fi : vérifié depuis l’ordinateur hôte.
- Test depuis un deuxième appareil : pas effectué le 19/11.

## Répétition Linux / WSL2 — 19/11/2026

### Vérifications des services

- Environnement : Ubuntu sous WSL2 avec Docker Desktop.
- `docker compose ps` : backend et frontend démarrés (`Up`).
- Interface `http://localhost:5173/` : HTTP 200.
- Documentation API `http://localhost:8000/docs` : HTTP 200.
- État du modèle via `http://localhost:5173/api/health` : `{"status":"ready","model_ready":true}`.

### Scénarios vérifiés dans le navigateur

- Profil 01 : classe affichée = 0
- Profil 02 : classe affichée = 1
- Profil 03 : classe affichée = 0
- Âge effacé : erreur affichée = « Renseignez le champ “Âge”. » ; envoi bloqué = oui
- Âge corrigé : nouvelle prédiction affichée = 0

- Statut de la répétition dans le navigateur : **VALIDÉ**. Les trois profils, le blocage de l’envoi avec l’âge effacé et la nouvelle prédiction après correction ont été vérifiés.

## Test depuis un deuxième appareil

Le compte-rendu historique du 18/11 dans [`../tests/scenarios-demo.md`](../tests/scenarios-demo.md) indique qu’un essai a été effectué depuis un smartphone connecté au même Wi-Fi. Il est **validé pour la version testée le 18/11**.

Les commits et l’empreinte du pipeline de cet essai n’ayant pas été consignés, il reste à confirmer qu’il s’agissait de la même version que celle de la démonstration finale.

## Supports de soutenance

- Rapport final : à ajouter (chemin du fichier ou lien partagé).
- Diapositives finales : à ajouter (chemin du fichier ou lien partagé).

## État du gel

La référence du pipeline est identifiée par son empreinte SHA-256. Les répétitions Windows et Ubuntu/WSL2 sont consignées, y compris le parcours navigateur avec les trois profils, la validation de l’âge et la reprise après correction. La version APP sera figée après le commit final des documents. Les liens des supports et la correspondance des commits et du pipeline utilisés lors du test smartphone du 18/11 restent à confirmer.

La version APP sera figée après le commit final des documents. Les liens des supports et la correspondance des commits et du pipeline utilisés lors du test smartphone du 18/11 restent à confirmer.
