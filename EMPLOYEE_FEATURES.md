# Module Employé — LoanApply24Bot

Ajouté sans supprimer les fichiers/fonctions existants.

## Accès administrateur
- `/employe` ouvre la gestion des employés.
- `/employe_add TELEGRAM_ID` active un employé.
- `/employe_remove TELEGRAM_ID` désactive un employé.
- Le bouton **Employés / Commissions** est disponible dans le panneau `/admin`.

## Accès employé
Un compte autorisé voit **💼 Employé** dans son menu et peut consulter :
- son lien personnel ;
- ses filleuls ;
- ses commissions en attente ;
- ses commissions disponibles ;
- ses commissions déjà retirées.

## Commission
La base de commission actuelle du programme de parrainage est conservée et la répartition interne est calculée à **50 % employé / 50 % entreprise**. Une commission est créée en statut `pending` lorsqu'un employé apporte un nouveau filleul. L'administrateur doit la valider pour la passer à `available`.

Le système ne rend pas automatiquement une commission disponible sur la seule déclaration d'un paiement client.

## Confirmation client
Depuis **Notifications client**, l'administrateur peut envoyer une demande de confirmation. Le client reçoit deux boutons : **Accepter** ou **Rejeter**. La réponse est enregistrée dans `client_confirmations`.

## Déploiement
Le code reste compatible avec la structure actuelle Termux → GitHub → Railway. La migration SQLite est additive : elle crée uniquement les nouvelles tables.
