#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")/.."

recipient="${1:?Indiquer la cle GPG}"

umask 077
mkdir -p backups

# find arrondit l'age en minutes vers le bas : +10079 inclut 7 jours revolus.
# Appliquer la retention meme si la nouvelle sauvegarde echoue ensuite.
find backups -maxdepth 1 -type f -name "cardioscope-*.dump.gpg" -mmin +10079 -print -delete

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
final="backups/cardioscope-${stamp}.dump.gpg"
partial="${final}.partial"

if [[ -e "$final" || -e "$partial" ]]; then
    echo "Un fichier porte deja ce nom." >&2
    exit 1
fi

cleanup() {
    rm -f -- "$partial"
}

trap cleanup EXIT

docker compose config --quiet

docker compose exec -T db pg_isready -U cardioscope -d cardioscope >/dev/null

docker compose exec -T db pg_dump -U cardioscope -d cardioscope -Fc |
    gpg --batch --encrypt --recipient "$recipient" --output "$partial"

test -s "$partial"

mv -- "$partial" "$final"

trap - EXIT

echo "Sauvegarde chiffree creee : $final"
