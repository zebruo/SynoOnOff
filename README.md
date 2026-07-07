# SynoOnOff

SynoOnOff est un petit outil qui permet d'allumer et d'éteindre un NAS Synology à distance depuis un PC Windows, sans passer par l'interface web de DSM ni par une manipulation manuelle.

## Pourquoi

Un NAS Synology consomme de l'énergie et fait du bruit en continu, alors qu'il n'est pas toujours utile de le laisser allumé. Mais l'éteindre manuellement puis devoir se déplacer pour le rallumer physiquement est contraignant. SynoOnOff automatise les deux sens :

- **Allumer** le NAS à distance, sans y toucher physiquement, grâce au **Wake-on-LAN** (un signal réseau qui réveille la carte réseau du NAS même éteint).
- **L'éteindre** proprement à distance, via une connexion **SSH** sécurisée qui déclenche l'arrêt du système.

## Comment ça se présente

Le projet propose trois façons d'utiliser la même logique :

- une **interface graphique** simple, avec un bouton pour allumer, un champ mot de passe et un bouton pour éteindre, un indicateur de statut en ligne/hors ligne, et un rapport d'activité ;
- une **ligne de commande** (`python synology_power.py on`/`off`), qui ne nécessite aucune interaction humaine et peut donc être déclenchée automatiquement — par exemple par le Planificateur de tâches Windows pour éteindre le NAS chaque soir à heure fixe, ou intégrée dans un script plus large ;
- un **exécutable Windows autonome**, qui ne nécessite pas d'installer Python pour être utilisé.

La configuration (adresse du NAS, identifiants) est modifiable directement depuis l'interface et sauvegardée localement, sans jamais être codée en dur dans le programme partagé.

Trois fichiers `.bat` sont fournis comme raccourcis de lancement pour une utilisation **depuis les sources** (sans passer par l'exécutable compilé) :

- **`nas_gui.bat`** — lance l'interface graphique sans fenêtre console (`pythonw`), pratique pour quelqu'un qui clone le dépôt sans vouloir compiler l'exe.
- **`allumer_nas.bat`** / **`eteindre_nas.bat`** — lancent le CLI (`python synology_power.py on`/`off`) sans avoir à retaper la commande ; utiles aussi comme base pour une éventuelle tâche planifiée Windows, seul le CLI se prêtant à l'automatisation.

## Fonctionnement de la configuration à la première utilisation

Au tout premier lancement, aucun fichier de configuration personnel n'existe encore : l'application affiche des **valeurs d'exemple génériques** (`Mon NAS`, `192.168.1.100`, utilisateur `admin`...) définies dans le code source.

1. Tu remplaces ces valeurs par les tiennes (adresse IP, adresse MAC, port SSH, utilisateur, nom du NAS) directement dans les champs de l'interface.
2. En cliquant sur **"Enregistrer la configuration"**, un fichier `config.json` est créé à côté du script (ou de l'exécutable).
3. À chaque lancement suivant, ce fichier est automatiquement relu et **prend le dessus** sur les valeurs génériques du code — plus besoin de tout ressaisir.

L'intérêt de ce fonctionnement : le code source (et l'exécutable compilé) ne contient jamais d'informations personnelles. Tu peux donc le partager ou le recompiler pour quelqu'un d'autre sans rien exposer — chaque utilisateur crée son propre `config.json` local, qui n'est jamais suivi par Git (voir `.gitignore`).

## Ce que ce n'est pas

- Ça ne remplace pas l'interface DSM : c'est un raccourci pour les deux actions les plus répétitives (allumer/éteindre), pas un outil de gestion du NAS.
- Ça ne fonctionne qu'en local (même réseau Wi-Fi/Ethernet que le NAS) — pas depuis l'extérieur d'Internet.
