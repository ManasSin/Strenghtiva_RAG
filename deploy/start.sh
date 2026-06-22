#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start.sh — install dependencies, start all services, tail live logs.
# Run as root on the VPS after copying the project.
# Usage: bash start.sh [--no-nginx] [--port 8501]
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

APP_DIR="/opt/strengthiva"
APP_USER="strengthiva"
PORT="8501"
SKIP_NGINX=false
LOG_DIR="/var/log/strengthiva"
DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Parse flags ───────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-nginx) SKIP_NGINX=true; shift ;;
        --port)     PORT="$2"; shift 2 ;;
        *) echo "Unknown flag: $1"; exit 1 ;;
    esac
done

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[1;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

log()  { echo -e "${BLUE}[start]${NC} $*"; }
ok()   { echo -e "${GREEN}[ok]${NC}   $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }
err()  { echo -e "${RED}[error]${NC} $*" >&2; exit 1; }
hdr()  { echo -e "\n${BOLD}${CYAN}══ $* ══${NC}"; }

# ─────────────────────────────────────────────────────────────────────────────
hdr "Pre-flight checks"
# ─────────────────────────────────────────────────────────────────────────────

[[ $EUID -eq 0 ]] || err "Run as root: sudo bash start.sh"

# Check .env exists and has a real API key
ENV_FILE="$APP_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    warn ".env not found at $ENV_FILE — creating from example..."
    if [[ -f "$APP_DIR/.env.example" ]]; then
        cp "$APP_DIR/.env.example" "$ENV_FILE"
        chown "$APP_USER":"$APP_USER" "$ENV_FILE" 2>/dev/null || true
    fi
fi

API_KEY="$(grep -E '^OPENAI_API_KEY=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"' | tr -d "'" || true)"
if [[ -z "$API_KEY" || "$API_KEY" == "sk-your-key-here" || "$API_KEY" == sk-xfs* ]]; then
    echo ""
    warn "OPENAI_API_KEY looks unset or is still the placeholder."
    warn "Edit $ENV_FILE and set a real key, then re-run this script."
    echo ""
    read -rp "Continue anyway? [y/N]: " cont
    [[ "$cont" =~ ^[Yy]$ ]] || exit 0
fi

# ─────────────────────────────────────────────────────────────────────────────
hdr "Python environment"
# ─────────────────────────────────────────────────────────────────────────────

VENV="$APP_DIR/.venv"
if [[ ! -d "$VENV" ]]; then
    log "Virtual environment not found — creating it..."
    python3 -m venv "$VENV"
    chown -R "$APP_USER":"$APP_USER" "$VENV"
fi

log "Installing / upgrading Python dependencies..."
"$VENV/bin/pip" install --upgrade pip -q
"$VENV/bin/pip" install -r "$APP_DIR/requirements.txt" -q
ok "Dependencies up to date."

# ─────────────────────────────────────────────────────────────────────────────
hdr "Streamlit config"
# ─────────────────────────────────────────────────────────────────────────────

mkdir -p "$APP_DIR/.streamlit"
cat > "$APP_DIR/.streamlit/config.toml" <<EOF
[server]
port = $PORT
headless = true
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false

[logger]
level = "info"
EOF
chown -R "$APP_USER":"$APP_USER" "$APP_DIR/.streamlit"
ok "Streamlit config written (port $PORT)."

# ─────────────────────────────────────────────────────────────────────────────
hdr "Supervisor (process manager)"
# ─────────────────────────────────────────────────────────────────────────────

mkdir -p "$LOG_DIR"
chown -R "$APP_USER":"$APP_USER" "$LOG_DIR"

# Write / overwrite supervisor config
cat > /etc/supervisor/conf.d/strengthiva.conf <<EOF
[program:strengthiva]
command=$VENV/bin/streamlit run $APP_DIR/main.py
directory=$APP_DIR
user=$APP_USER
autostart=true
autorestart=true
startretries=5
stopasgroup=true
killasgroup=true
stdout_logfile=$LOG_DIR/app.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
stderr_logfile=$LOG_DIR/error.log
stderr_logfile_maxbytes=10MB
stderr_logfile_backups=5
environment=HOME="/home/$APP_USER",USER="$APP_USER"
EOF

# Ensure supervisord is running
if ! command -v supervisorctl &>/dev/null; then
    err "Supervisor not installed. Run install.sh first."
fi

systemctl enable supervisor -q 2>/dev/null || true
systemctl start  supervisor 2>/dev/null || true
supervisorctl reread  -c /etc/supervisor/supervisord.conf 2>/dev/null
supervisorctl update  -c /etc/supervisor/supervisord.conf 2>/dev/null
supervisorctl restart strengthiva 2>/dev/null || supervisorctl start strengthiva

sleep 2
STATUS="$(supervisorctl status strengthiva | awk '{print $2}')"
if [[ "$STATUS" == "RUNNING" ]]; then
    ok "Streamlit app is RUNNING (port $PORT)."
else
    warn "App status: $STATUS — check $LOG_DIR/error.log"
fi

# ─────────────────────────────────────────────────────────────────────────────
hdr "Nginx"
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$SKIP_NGINX" == "true" ]]; then
    warn "Nginx skipped (--no-nginx passed). App accessible at http://localhost:$PORT"
else
    if ! command -v nginx &>/dev/null; then
        warn "Nginx not found — skipping. Run install.sh or pass --no-nginx."
    else
        # Regenerate nginx config with current port
        cat > /etc/nginx/sites-available/strengthiva <<EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass         http://127.0.0.1:$PORT;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade \$http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host \$host;
        proxy_set_header   X-Real-IP \$remote_addr;
        proxy_set_header   X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }
}
EOF
        ln -sf /etc/nginx/sites-available/strengthiva /etc/nginx/sites-enabled/strengthiva
        rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

        nginx -t -q && systemctl reload nginx
        ok "Nginx is serving → http://$(curl -s ifconfig.me 2>/dev/null || echo '<your-server-ip>')"
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
hdr "Service summary"
# ─────────────────────────────────────────────────────────────────────────────

PUBLIC_IP="$(curl -s --max-time 3 ifconfig.me 2>/dev/null || echo '<server-ip>')"

echo ""
echo -e "${BOLD}  Service       Status${NC}"
echo    "  ─────────────────────────────────────────────"
supervisorctl status strengthiva | awk '{printf "  Streamlit     %s (pid %s, uptime %s)\n", $2, $4, $5}'
nginx -t -q 2>/dev/null \
    && echo -e "  Nginx         ${GREEN}RUNNING${NC} → port 80" \
    || echo -e "  Nginx         ${YELLOW}not running${NC}"
echo ""
echo -e "  App URL       ${CYAN}http://$PUBLIC_IP${NC}         (via Nginx)"
echo -e "  Direct        ${CYAN}http://$PUBLIC_IP:$PORT${NC}   (Streamlit)"
echo ""
echo -e "  Logs (live):  tail -f $LOG_DIR/app.log"
echo -e "  Error log:    tail -f $LOG_DIR/error.log"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
hdr "Live logs  (Ctrl+C to stop tailing — services keep running)"
# ─────────────────────────────────────────────────────────────────────────────

# Give the app a moment to write first lines
sleep 2
tail -f "$LOG_DIR/app.log" "$LOG_DIR/error.log" 2>/dev/null \
  --pid "$(supervisorctl pid strengthiva 2>/dev/null || echo 1)" \
  || tail -f "$LOG_DIR/app.log"
