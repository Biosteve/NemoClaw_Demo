#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PARENT="$(dirname "$ROOT")"
NAME="$(basename "$ROOT")"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${1:-$PARENT/${NAME}-${STAMP}.tgz}"

mkdir -p "$(dirname "$OUT")"

tar \
  --create \
  --gzip \
  --file "$OUT" \
  --directory "$PARENT" \
  --exclude="$NAME/.env" \
  --exclude="$NAME/demo-app/state" \
  --exclude="$NAME/demo-app/__pycache__" \
  --exclude="$NAME/**/__pycache__" \
  --exclude="$NAME/**/*.pyc" \
  --exclude="$NAME/*.tgz" \
  "$NAME"

echo "Created portable archive:"
echo "  $OUT"
echo
echo "Restore on another machine:"
echo "  tar -xzf $(basename "$OUT") -C ~"
echo "  cd ~/$NAME"
echo "  cp .env.example .env"
echo "  chmod 600 .env"
echo "  vi .env"
echo "  ./scripts/brev-runtime-setup.sh"
echo "  ./scripts/live-demo-ready.sh"
