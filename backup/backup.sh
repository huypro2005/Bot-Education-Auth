#!/bin/sh

set -eu

TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
DB_HOST="${MYSQL_HOST:-mysql}"
DB_USER="root"
DB_NAME="${MYSQL_DATABASE:?MYSQL_DATABASE is required}"

BACKUP_DIR="/db_backups"
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql"
TMP_FILE="${BACKUP_FILE}.tmp"

echo "[$(date)] Starting backup..."

mkdir -p "$BACKUP_DIR"

mysqldump \
  -h"$DB_HOST" \
  -u"$DB_USER" \
  -p"${MYSQL_ROOT_PASSWORD:?MYSQL_ROOT_PASSWORD is required}" \
  --single-transaction \
  --quick \
  --lock-tables=false \
  --routines \
  --events \
  --triggers \
  "$DB_NAME" \
  > "$TMP_FILE"

mv -f "$TMP_FILE" "$BACKUP_FILE"
echo "[$(date)] Backup successful: $BACKUP_FILE"

# Xóa backup cũ hơn 7 ngày
find "$BACKUP_DIR" -type f -name "*.sql" -mtime +7 -delete || true