#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# update.sh — pull latest code and hot-reload without downtime.
# Usage: bash update.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

APP_DIR="/opt/strengthiva"
APP_USER="strengthiva"
VENV="$APP_DIR/.venv"

BLUE='\033[1;34m'; GREEN='\033[0;32m'; NC='\033[0m'
log() { echo -e "${BLUE}[update]${NC} $*"; }
ok()  { echo -e "${GREEN}[ok]${NC}   $*"; }

[[ $EUID -eq 0 ]] || { echo "Run as root."; exit 1; }

log "Pulling latest code into $APP_DIR..."
cd "$APP_DIR"
# Copy changed files from deploy source (if running from repo clone on server)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(dirname "$SCRIPT_DIR")"
rsync -a --exclude='.env' --exclude='.venv' --exclude='data/' \
    "$SOURCE_DIR/" "$APP_DIR/"
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

log "Upgrading Python dependencies..."
"$VENV/bin/pip" install -r "$APP_DIR/requirements.txt" -q
ok "Dependencies up to date."

log "Restarting app via Supervisor..."
supervisorctl restart strengthiva
sleep 2
supervisorctl status strengthiva

ok "Update complete."
