# Outils d'analyse de disque Linux

Scanner non destructif pour inventorier d'anciens disques et repérer les fichiers personnels importants.

Le rapport produit pour chaque point de montage contient :

- informations SMART et capacité du disque quand `smartctl`/`lsblk` sont disponibles ;
- inventaire CSV de tous les fichiers accessibles ;
- catégories photos, PDF, Word, Excel, PowerPoint, vidéos, archives et système probable ;
- arborescence synthétique ;
- doublons détectés par SHA-256 ;
- erreurs d'accès, extensions suspectes et indicateurs de risque ;
- rapport HTML autonome consultable hors ligne.

## Installation

```bash
sudo apt install smartmontools util-linux
git clone https://github.com/USER/outils-analyse-disque-linux.git
cd outils-analyse-disque-linux
```

Python 3.10 ou plus récent est recommandé. Aucune bibliothèque externe n'est nécessaire.

## Utilisation

Monter le disque en lecture seule, puis lancer :

```bash
python3 -m disk_audit /media/$USER/DISQUE_001 -o rapports/DISQUE_001
```

Pour associer le point de montage à un périphérique et récupérer SMART :

```bash
sudo python3 -m disk_audit /media/$USER/DISQUE_001 \
  --device /dev/sdb -o rapports/DISQUE_001
```

Pour un premier inventaire rapide sans calculer les empreintes :

```bash
python3 -m disk_audit /media/$USER/DISQUE_001 \
  --no-hash -o rapports/DISQUE_001
```

Les résultats sont écrits dans le dossier de sortie : `summary.html`, `files.csv`, `duplicates.csv`, `tree.csv` et `smart.json`.

Le programme ne déplace, ne supprime et ne modifie aucun fichier source. Les fichiers illisibles apparaissent dans le rapport avec un risque élevé.

## Conseils de sécurité

1. Tester d'abord le disque avec un câble et un adaptateur fiables.
2. Ne pas lancer `fsck`, de réparation ou de formatage avant la récupération des données.
3. Si le disque émet des bruits anormaux ou produit des erreurs de lecture, créer une image avec `ddrescue` avant une analyse complète.
4. Garder au moins deux copies vérifiées des photos et documents récupérés.

## Licence

MIT — voir [LICENSE](LICENSE).
