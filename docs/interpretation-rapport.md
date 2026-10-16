# Interpréter un rapport

Le rapport est constitué de plusieurs fichiers complémentaires.

## `summary.html`

Vue d'ensemble lisible dans un navigateur : volume analysé, catégories, doublons et erreurs d'accès.

## `files.csv`

Inventaire détaillé, avec le chemin relatif, l'extension, la catégorie, la taille, la date de modification et, si le hachage est activé, le SHA-256.

Les catégories personnelles prioritaires sont `photo`, `pdf`, `word`, `excel` et `powerpoint`. La catégorie `systeme_probable` ne signifie pas automatiquement que le fichier est inutile : elle indique seulement qu'une vérification humaine est nécessaire.

## `duplicates.csv`

Un groupe de doublons contient plusieurs chemins ayant la même taille et le même SHA-256. Garder au moins une copie vérifiée avant toute suppression.

## `smart.json`

Informations retournées par `smartctl` pour le périphérique indiqué avec `--device`. Sur certains boîtiers USB, le pont USB peut limiter les informations SMART ; un rapport SMART indisponible ne prouve pas que le disque est défectueux.

## Risques

- erreurs d'accès : données potentiellement illisibles ;
- fichiers système probables : ne pas supprimer automatiquement ;
- disque bruyant, très lent ou avec erreurs SMART : arrêter l'analyse et faire une image avec `ddrescue` ;
- une seule copie : données non sécurisées.
