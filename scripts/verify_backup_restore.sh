#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "$0")/.."

archive="${1:?Usage: bash scripts/verify_backup_restore.sh backups/fichier.dump.gpg}"
test -s "$archive"
docker compose config --quiet
docker compose exec -T db pg_isready -U cardioscope -d cardioscope >/dev/null

# Lire le format de l'archive sans extraire de donnees sur le poste hote.
gpg --batch --decrypt "$archive" 2>/dev/null |
    docker compose exec -T db pg_restore --list >/dev/null

database="app24_restore_check_$(date -u +%Y%m%d%H%M%S)_$$"
docker compose exec -T db createdb -U cardioscope "$database"
cleanup() {
    docker compose exec -T db dropdb -U cardioscope --if-exists "$database" >/dev/null
}
trap cleanup EXIT

gpg --batch --decrypt "$archive" 2>/dev/null |
    docker compose exec -T db pg_restore -U cardioscope --no-owner --no-acl -d "$database"

tables_ok="$(docker compose exec -T db psql -v ON_ERROR_STOP=1 -U cardioscope -d "$database" -Atqc \
    "SELECT to_regclass('public.admins') IS NOT NULL AND to_regclass('public.admin_sessions') IS NOT NULL AND to_regclass('public.csrf_contexts') IS NOT NULL AND to_regclass('public.login_attempt_windows') IS NOT NULL AND to_regclass('public.simulations') IS NOT NULL AND to_regclass('public.alembic_version') IS NOT NULL;")"
test "$tables_ok" = t

admins_before="$(docker compose exec -T db psql -v ON_ERROR_STOP=1 -U cardioscope -d "$database" -Atqc 'SELECT count(*) FROM admins;')"
test "$admins_before" -ge 1

# Prouver le nettoyage avec des lignes fictives, exclusivement dans la base isolee.
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U cardioscope -d "$database" -qAtc \
    "BEGIN;
     INSERT INTO admin_sessions (admin_id, token_hash, expires_at)
       SELECT id, repeat(md5(random()::text), 2), now() + interval '1 hour' FROM admins LIMIT 1;
     INSERT INTO csrf_contexts (binding_hash, token_hash, session_id, expires_at)
       SELECT repeat(md5(random()::text), 2), repeat(md5(random()::text), 2), id,
              now() + interval '1 hour' FROM admin_sessions LIMIT 1;
     INSERT INTO login_attempt_windows (key_hash, expires_at)
       VALUES (repeat(md5(random()::text), 2), now() + interval '1 hour');
     INSERT INTO simulations (prediction, model_version, artifact_sha256,
       age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang,
       oldpeak, slope, ca, thal)
       VALUES (0, 'restore-check', repeat('a', 64),
       50, 1, 1, 120, 200, 0, 0, 150, 0, 0, 1, 0, 3);
     COMMIT;"

counts_before="$(docker compose exec -T db psql -v ON_ERROR_STOP=1 -U cardioscope -d "$database" -Atqc \
    'SELECT (SELECT count(*) FROM admin_sessions), (SELECT count(*) FROM csrf_contexts), (SELECT count(*) FROM login_attempt_windows), (SELECT count(*) FROM simulations);')"
IFS='|' read -r sessions csrf attempts simulations <<< "$counts_before"
test "$sessions" -ge 1 && test "$csrf" -ge 1 && test "$attempts" -ge 1 && test "$simulations" -ge 1

# Appliquer seulement sur la base de test le nettoyage impose avant reouverture.
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U cardioscope -d "$database" -qAtc \
    'BEGIN; DELETE FROM csrf_contexts; DELETE FROM admin_sessions; DELETE FROM login_attempt_windows; DELETE FROM simulations; COMMIT;'

counts_after="$(docker compose exec -T db psql -v ON_ERROR_STOP=1 -U cardioscope -d "$database" -Atqc \
    'SELECT (SELECT count(*) FROM admins), (SELECT count(*) FROM admin_sessions), (SELECT count(*) FROM csrf_contexts), (SELECT count(*) FROM login_attempt_windows), (SELECT count(*) FROM simulations);')"
test "$counts_after" = "$admins_before|0|0|0|0"

echo "Restauration isolee et nettoyage verifies. Comptes admin conserves : $admins_before."
