# Optimisation et automatisation

## Optimisation appliquée

Le mode normal ne calcule plus le SHA-256 de chaque fichier. Il commence par inventorier les fichiers et ne hache que les groupes ayant une taille identique, car deux fichiers de tailles différentes ne peuvent pas être des doublons exacts.

```bash
python3 -m disk_audit /mnt/disque-usb --device /dev/sdd -o /root/rapports/HDD2
```

Pour désactiver complètement les empreintes :

```bash
python3 -m disk_audit /mnt/disque-usb --no-hash -o /root/rapports/HDD2-rapide
```

Pour une vérification exhaustive de tous les fichiers :

```bash
python3 -m disk_audit /mnt/disque-usb --hash-all -o /root/rapports/HDD2-exhaustif
```

Le programme affiche maintenant une progression tous les 1 000 fichiers et tous les 100 hachages. Les erreurs de lecture sont conservées dans le rapport au lieu d'arrêter toute l'analyse.

## Lancement automatisé et sûr

Le script [`scripts/analyze-mounted-disk.sh`](../scripts/analyze-mounted-disk.sh) vérifie le point de montage et le périphérique, empêche deux analyses simultanées avec `flock`, puis lance l'analyse. Il ne monte, ne démonte, ne déplace et ne supprime rien.

```bash
chmod +x scripts/analyze-mounted-disk.sh
sudo scripts/analyze-mounted-disk.sh \
  /mnt/disque-usb /dev/sdd HDD2
```

Pour un inventaire sans hachage :

```bash
sudo scripts/analyze-mounted-disk.sh \
  /mnt/disque-usb /dev/sdd HDD2-rapide --no-hash
```

Le rapport est créé dans `/root/rapports/<nom>`. Pour automatiser plusieurs disques, appelez le script une fois par disque avec un nom distinct. Il est préférable de brancher et monter les disques manuellement en lecture seule, puis de lancer le script, plutôt que d'autoriser un montage automatique de périphériques inconnus.

## Limites

- Le hachage reste limité par la vitesse de lecture du disque.
- Un disque qui produit des erreurs ou des bruits anormaux doit être imagé avec `ddrescue` avant une analyse répétée.
- `smartctl` peut fournir des informations partielles derrière certains boîtiers USB.
