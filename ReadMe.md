# README

Ce code Python est conçu pour automatiser la configuration des routeurs dans un réseau en utilisant des fichiers de configuration au format JSON. Il prend en compte deux fichiers associés : `lecture_json.py` et `fonctions.py`.

## Prérequis

Assurez-vous d'avoir les fichiers `lecture_json.py` et `fonctions.py` dans le même répertoire que ce script. Ces fichiers contiennent des fonctions nécessaires à l'exécution du programme.
Assurez-vous également d'avoir installer les bibliothèques suivantes : sys, time, threading, telnetlib, gns3fy, json et os.

## Utilisation

Exécutez le script en ligne de commande en fournissant le nom du fichier JSON en argument. Assurez-vous d'avoir au préalable ouvert le projet (du même nom que le fichier JSON) dans GNS3 (le démarrage des routeurs n'est pas nécessaire). Vous pouvez utiliser ce code avec les projets contenus dans les dossiers suivants : Policies et BigNetwork. Vous pourrez lire toutes les lignes de configuration entrées dans les routeurs via telnet. Pour cela, il suffit de consulter les fichier TXT présents dans le dossier Configs.

Par exemple :

```bash
python main.py Policies/Policies.json

