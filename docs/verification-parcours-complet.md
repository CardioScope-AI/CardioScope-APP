# Recette du parcours complet — APP #23

Date de vérification : 28 novembre 2026.

## Environnement

- Dépôt : `CardioScope-APP`, branche `feat/23-tester-parcours-complet`.
- Windows avec Docker Desktop et moteur Linux.
- Préalables intégrés : APP #22 (PR #35) et APP #24 (PR #36).
- Services Docker `db`, `backend` et `frontend` : `healthy`.

## Résultats

- `GET http://localhost:5173/` : HTTP 200.
- `GET http://localhost:5173/api/health` : HTTP 200.
- `GET http://localhost:8000/docs` : HTTP 200.
- Connexion à l’application locale avec une session administrateur : réussie.
- Profil fictif `Profil 01 · Risque faible` soumis : résultat affiché, classe prédite `0 — absence`.
- Enregistrement dans l’historique : vérifié. Le résumé affichait 45 ans, 120 mmHg, 180 mg/dL ; version du modèle `rf-cleveland-v1-local-test`.
- Détail : ouvert avec succès. Les 13 champs du profil correspondaient au profil fictif soumis, et la classe/version correspondaient à la ligne de l’historique.
- Suppression : la confirmation de l’application a été acceptée pour cette simulation de test. Après suppression, l’historique affichait `0 résultat`.
- Consultation directe de l’identifiant supprimé via l’API : réponse JSON `not_found` (`Simulation introuvable.`).

## Conclusion

Le parcours local simulation → enregistrement → historique → détail → suppression a réussi. Les valeurs utilisées étaient fictives. Aucun mot de passe, jeton, contenu de `.env` ni identifiant de compte n’est consigné ici.
