#!/usr/bin/env bash
set -Eeuo pipefail

# Analyse non destructive d'un point de montage. Le script ne monte, ne modifie
# et ne supprime aucun fichier du disque source.
if [[ $# -lt 3 || $# -gt 4 ]]; then
  echo "Usage: $0 MOUNT_POINT DEVICE DISK_NAME [--no-hash]" >&2
  exit 2
fi

MOUNT_POINT=$1
DEVICE=$2
DISK_NAME=$3
MODE=${4:-}
REPO_DIR=${REPO_DIR:-$(cd "$(dirname "$0")/.." && pwd)}
REPORT_ROOT=${REPORT_ROOT:-/root/rapports}
OUTPUT="$REPORT_ROOT/$DISK_NAME"

[[ -d "$MOUNT_POINT" ]] || { echo "Point de montage absent: $MOUNT_POINT" >&2; exit 1; }
findmnt -rn -T "$MOUNT_POINT" >/dev/null || { echo "Le chemin n'est pas un point de montage: $MOUNT_POINT" >&2; exit 1; }
[[ -b "$DEVICE" ]] || { echo "Périphérique absent: $DEVICE" >&2; exit 1; }
[[ "$DISK_NAME" != */* && "$DISK_NAME" != .* ]] || { echo "Nom de disque invalide" >&2; exit 1; }

mkdir -p "$REPORT_ROOT"
exec 9>"${LOCK_FILE:-/tmp/disk-audit.lock}"
flock -n 9 || { echo "Une autre analyse est déjà en cours" >&2; exit 1; }

cd "$REPO_DIR"
ARGS=("$MOUNT_POINT" --device "$DEVICE" -o "$OUTPUT")
[[ "$MODE" == "--no-hash" ]] && ARGS+=(--no-hash)
echo "Analyse de $MOUNT_POINT vers $OUTPUT"
exec python3 -m disk_audit "${ARGS[@]}"
