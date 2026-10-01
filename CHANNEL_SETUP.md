# Module Canal Telegram

Le parcours client existant reste inchangé. Le module Canal ajoute la gestion des publications depuis le panneau administrateur.

## Variables Railway

Ajoutez :

- `CHANNEL_ID=@GLOBALUSDTFINANCE1`
- `BOT_USERNAME=LoanApply24Bot`

`BOT_TOKEN` reste inchangé et doit rester uniquement dans les variables Railway.

## Permissions du bot dans le canal

Le bot `@LoanApply24Bot` doit être administrateur du canal avec les droits nécessaires pour :

- publier des messages ;
- modifier/supprimer ses messages ;
- gérer les messages épinglés.

Ne donnez pas au bot le droit d'ajouter de nouveaux administrateurs.

## Fonctions ajoutées

- publication automatique d'une nouvelle demande ;
- langue du client : FR / EN / ES / PT ;
- mise à jour de la publication lors des changements d'étape ;
- publication manuelle depuis `/admin` ;
- aperçu avant publication ;
- publication photo + légende ;
- programmation UTC ;
- restauration des publications programmées après redémarrage ;
- modification, suppression, épinglage et désépinglage ;
- statistiques et historique récent ;
- boutons vers le bot ;
- aucun KYC, portefeuille, TXID ou autre donnée privée dans les publications automatiques.
