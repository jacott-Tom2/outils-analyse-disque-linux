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

## Procédure Proxmox + Mac

Si le disque USB est connecté au serveur Proxmox, identifiez-le sur Proxmox :

```bash
lsblk -o NAME,SIZE,FSTYPE,LABEL,MODEL,TRAN,MOUNTPOINTS
```

Repérez la partition dont `TRAN` vaut `usb`, puis montez-la en lecture seule. Exemple pour un disque `HDD2` sur `/dev/sdd1` :

```bash
mkdir -p /mnt/disque-usb
mount -o ro,nosuid,nodev,noexec /dev/sdd1 /mnt/disque-usb
```

Lancez l'inventaire depuis Proxmox :

```bash
python3 -m disk_audit /mnt/disque-usb \
  --device /dev/sdd --no-hash -o /root/rapports/HDD2
```

Copiez ensuite le rapport sur un Mac, dans un terminal macOS (et non dans le terminal `root@Proxmox`) :

```bash
scp -r root@ADRESSE_PROXMOX:/root/rapports/HDD2 ~/HDD2-rapport
open ~/HDD2-rapport/summary.html
```

Après vérification du premier rapport, relancez l'analyse complète sans `--no-hash` pour détecter les doublons :

```bash
python3 -m disk_audit /mnt/disque-usb \
  --device /dev/sdd -o /root/rapports/HDD2-complet
```

Répétez la procédure avec un dossier de sortie différent pour chaque disque (`HDD1`, `HDD2`, etc.). Ne montez jamais deux disques avec le même dossier de destination.

### Ordre de travail conseillé

1. Faire l'inventaire rapide avec `--no-hash`.
2. Lire `summary.html` et repérer les erreurs d'accès.
3. Vérifier les catégories `photo`, `pdf`, `word`, `excel` et `powerpoint` dans `files.csv`.
4. Faire l'analyse complète avec les SHA-256.
5. Copier les fichiers importants vers deux destinations distinctes.
6. Ne supprimer ou reformater aucun disque avant vérification des copies.

Le programme ne déplace, ne supprime et ne modifie aucun fichier source. Les fichiers illisibles apparaissent dans le rapport avec un risque élevé.

## Conseils de sécurité

1. Tester d'abord le disque avec un câble et un adaptateur fiables.
2. Ne pas lancer `fsck`, de réparation ou de formatage avant la récupération des données.
3. Si le disque émet des bruits anormaux ou produit des erreurs de lecture, créer une image avec `ddrescue` avant une analyse complète.
4. Garder au moins deux copies vérifiées des photos et documents récupérés.

## Licence

MIT — voir [LICENSE](LICENSE).
