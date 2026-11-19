# Règles de conservation — APP #17

Statut : validé par l’équipe, confirmation transmise le 19 novembre 2026.
Mise en œuvre et vérification technique encore à réaliser.

Ce document complète le [contrat admin](contrat-admin-historique.md).
L’application est exclusivement réservée à un administrateur et aux profils
fictifs du démonstrateur. Les durées ci-dessous sont des choix de projet validés,
pas des obligations légales ni une politique adaptée à des données médicales réelles.

## 1. Données et durées proposées

| Données | Conservation maximale | Traitement à échéance |
| --- | --- | --- |
| Simulations : profil, résultat, date, version et empreinte du modèle | 90 jours après created_at | Suppression physique quotidienne |
| Sessions admin | 8 h absolues ou 30 min d’inactivité | Accès refusé immédiatement dès expiration ; nettoyage quotidien |
| Sessions expirées ou révoquées | 24 h après expiration ou révocation | Suppression physique |
| Contextes CSRF anonymes | 10 minutes | Invalidation immédiate puis nettoyage quotidien |
| Contextes CSRF liés à une session | Au plus la durée de la session | Invalidation avec la session ; nettoyage quotidien |
| Compteurs d’échecs de connexion | Fenêtre de 15 min ; blocage proposé de 15 min | Suppression au plus tard 24 h après fin du blocage |
| Logs techniques | 14 jours après émission | Rotation et suppression automatique |
| Sauvegardes quotidiennes de la base | 7 jours après création | Suppression automatique des copies expirées |
| Compte admin et hash du mot de passe | Durée d’exploitation du démonstrateur | Suppression à la fermeture du projet |

Toutes les dates sont en UTC. Une simulation est expirée si
`created_at <= maintenant_UTC - 90 jours`. La purge s’exécute chaque jour ;
la suppression physique peut donc suivre l’échéance de moins de 24 heures.
Les contrôles de session et CSRF n’attendent jamais la purge pour refuser un accès.

Les artefacts ML et rapports de métriques ne sont pas des simulations : leur
versionnement relève de DATA-ML #22. Une purge ou un DELETE ne supprime jamais
un modèle. La version historique stockée ne doit pas être remplacée par la version courante.

## 2. Suppression manuelle et automatique

- L’admin confirme puis appelle DELETE /admin/simulations/{id}, avec session et CSRF.
- Le backend supprime physiquement la ligne dans une transaction et ne répond 204
  qu’après commit. Après succès, détail et nouvelle suppression répondent 404.
- Un échec de stockage ne doit jamais être annoncé comme une suppression réussie.
- La purge applique le même principe aux simulations expirées, par lots bornés.
  Elle peut être relancée sans erreur si certaines lignes ont déjà disparu.
- Aucun profil ou résultat supprimé n’est recopié dans les logs ou une table d’audit.
  Seuls la date d’exécution, les compteurs et un code d’erreur technique sont journalisés.

Les sauvegardes déjà créées peuvent encore contenir une ligne supprimée jusqu’à
leur expiration, au plus 7 jours après la suppression. Ce délai doit être expliqué
dans la documentation admin. Il ne s’agit pas d’un effacement immédiat des sauvegardes.

## 3. Export PDF et minimisation

L’export PDF est téléchargé par l’admin ; aucune copie supplémentaire n’est
conservée sur le serveur. Le document indique la date, le résultat, la version du
modèle et le caractère pédagogique. Une copie téléchargée est gérée par l’admin :
la suppression en base ne l’efface pas de son ordinateur.

Ne pas collecter de nom patient, email, identifiant personnel ou texte libre.
Ne pas journaliser les 13 valeurs, mots de passe, cookies, jetons CSRF ou de session.
Les clés réseau nécessaires à la limitation du login restent distinctes des
simulations, avec la durée courte du tableau. Les logs applicatifs et du proxy
doivent suivre la même règle de minimisation et de rotation.
L’historique ne sert pas automatiquement au réentraînement.

## 4. Sauvegarde et restauration

- Sauvegarder quotidiennement la base avec un outil adapté à PostgreSQL ; vérifier
  le succès avant de remplacer une copie existante. Chiffrer les copies et limiter
  leur accès à l’exploitation ; ne placer ni sauvegarde ni secret dans Git.
- Conserver les secrets de chiffrement séparément des sauvegardes.
- Après restauration, maintenir le service fermé aux utilisateurs, révoquer toutes
  les sessions restaurées et vider les contextes CSRF et compteurs temporaires.
- Une ancienne sauvegarde peut ressusciter une suppression manuelle récente.
  Pour ce démonstrateur, vider l’ensemble de l’historique restauré avant réouverture,
  puis confirmer cette perte volontaire à l’admin. Ne pas promettre de récupération
  des simulations. Le compte admin reste disponible après contrôle de son état.
- Vérifier les migrations, les accès et une nouvelle connexion avant réouverture.

APP #24 documentera les commandes et un exercice réel de restauration. Si l’équipe
souhaite restaurer aussi l’historique, elle devra définir un mécanisme fiable de
réapplication des suppressions avant de changer cette règle.

## 5. Mise en œuvre attendue et responsabilités

| Dépôt / tâche | Travail attendu |
| --- | --- |
| BACKEND #16 et #21–#23 | Dates UTC, transactions et suppression physique ; commande de purge avec mode de simulation sans écriture |
| BACKEND #18–#20 | Expiration et révocation serveur, nettoyage des sessions et protection des actions |
| APP #18 | Stockage persistant et mécanisme planifié de purge quotidienne |
| APP #19 | Commandes de migration, initialisation et purge documentées |
| APP #20 | Secrets de session et paramètres de déploiement |
| APP #24 | Sauvegardes, rotation et restauration contrôlée |
| FRONTEND #28 | Confirmation de suppression et mise à jour après succès serveur |

La configuration cible doit proposer des paramètres documentés pour les durées,
avec validation de valeurs positives. La désactivation silencieuse de la purge
n’est pas admise. Sur échec, garder le service de purge en échec visible et alerter
l’exploitant ; ne pas produire un rapport de succès. La sauvegarde ne remplace pas
la persistance du volume PostgreSQL.

## 6. Critères de validation à implémenter

- Une simulation récente reste présente ; une simulation à la limite des 90 jours
  ou plus ancienne est sélectionnée par la purge ; vérifier précisément la frontière UTC.
- Le mode de simulation affiche les compteurs sans modifier la base ; deux purges
  successives ne provoquent pas d’erreur ni de suppression supplémentaire inattendue.
- Une session expirée est refusée même si sa ligne existe encore.
- Un DELETE confirmé retire la ligne ; une panne au commit ne renvoie pas 204.
- Les copies de plus de 7 jours et les logs de plus de 14 jours sont supprimés.
- Après restauration, aucune session ni simulation antérieure n’est réexposée.
- Aucun secret ni profil complet ne figure dans les logs de ces opérations.

La rédaction de cette politique ne prouve pas encore ces comportements : leur
validation nécessite les fonctionnalités backend et les scripts de déploiement.

## 7. Choix validés par l’équipe

- [x] Historique 90 jours, logs 14 jours, sauvegardes 7 jours.
- [x] Suppression physique, purge quotidienne et délais résiduels dans les copies.
- [x] Historique vidé après restauration pour éviter de rétablir des suppressions.
- [x] Usage exclusivement admin et profils fictifs, sans réentraînement automatique.
