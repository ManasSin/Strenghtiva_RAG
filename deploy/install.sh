#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# install.sh — one-time server setup for Ayurvedic Health Assessment App
# Run as root or a sudo user on a fresh Ubuntu 22.04 / Debian 12 VPS.
# Usage: bash install.sh
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

APP_USER="${APP_USER:-strengthiva}"
APP_DIR="/opt/strengthiva"
PYTHON_VERSION="3.11"
PORT="${PORT:-8501}"

log() { echo -e "\033[1;34m[install]\033[0m $*"; }
ok()  { echo -e "\033[1;32m[ok]\033[0m $*"; }
err() { echo -e "\033[1;31m[error]\033[0m $*" >&2; exit 1; }

# ── 0. Must run as root ───────────────────────────────────────────────────────
[[ $EUID -eq 0 ]] || err "Run as root: sudo bash install.sh"

log "Updating package index..."
apt-get update -qq

# ── 1. System dependencies ────────────────────────────────────────────────────
log "Installing system packages..."
apt-get install -y -qq \
    python3 python3-pip python3-venv python3-dev \
    git curl wget unzip build-essential \
    libssl-dev libffi-dev \
    nginx \
    certbot python3-certbot-nginx \
    supervisor \
    ufw \
    2>/dev/null

ok "System packages installed."

# ── 2. Create dedicated app user ──────────────────────────────────────────────
if ! id "$APP_USER" &>/dev/null; then
    log "Creating user '$APP_USER'..."
    useradd -m -s /bin/bash "$APP_USER"
    ok "User '$APP_USER' created."
else
    ok "User '$APP_USER' already exists."
fi

# ── 3. Create app directory and copy files ────────────────────────────────────
log "Setting up app directory at $APP_DIR..."
mkdir -p "$APP_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_SOURCE="$(dirname "$SCRIPT_DIR")"  # parent of deploy/

cp -r "$APP_SOURCE"/. "$APP_DIR/"
chown -R "$APP_USER":"$APP_USER" "$APP_DIR"

ok "App files copied to $APP_DIR."

# ── 4. Python virtualenv + dependencies ──────────────────────────────────────
log "Creating Python virtual environment..."
sudo -u "$APP_USER" python3 -m venv "$APP_DIR/.venv"

log "Installing Python dependencies..."
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install --upgrade pip -q
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q

ok "Python dependencies installed."

# ── 5. Create .env from template if it doesn't exist ─────────────────────────
if [[ ! -f "$APP_DIR/.env" ]]; then
    log "Creating .env from .env.example..."
    if [[ -f "$APP_DIR/.env.example" ]]; then
        cp "$APP_DIR/.env.example" "$APP_DIR/.env"
        chown "$APP_USER":"$APP_USER" "$APP_DIR/.env"
        echo ""
        echo "  ⚠️  Edit $APP_DIR/.env and set your OPENAI_API_KEY before starting."
        echo ""
    else
        cat > "$APP_DIR/.env" <<EOF
OPENAI_API_KEY=sk-your-key-here
EOF
        chown "$APP_USER":"$APP_USER" "$APP_DIR/.env"
        echo ""
        echo "  ⚠️  Edit $APP_DIR/.env and replace 'sk-your-key-here' with your real key."
        echo ""
    fi
fi

# ── 6. Streamlit config ───────────────────────────────────────────────────────
log "Writing Streamlit server config..."
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

ok "Streamlit config written."

# ── 7. Supervisor service unit ────────────────────────────────────────────────
log "Configuring Supervisor to manage the app process..."
cat > /etc/supervisor/conf.d/strengthiva.conf <<EOF
[program:strengthiva]
command=$APP_DIR/.venv/bin/streamlit run $APP_DIR/main.py
directory=$APP_DIR
user=$APP_USER
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stdout_logfile=/var/log/strengthiva/app.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
stderr_logfile=/var/log/strengthiva/error.log
stderr_logfile_maxbytes=10MB
stderr_logfile_backups=5
environment=HOME="/home/$APP_USER",USER="$APP_USER"
EOF

mkdir -p /var/log/strengthiva
chown -R "$APP_USER":"$APP_USER" /var/log/strengthiva

supervisorctl reread
supervisorctl update

ok "Supervisor configured."

# ── 8. Nginx reverse proxy ────────────────────────────────────────────────────
log "Configuring Nginx reverse proxy..."
cat > /etc/nginx/sites-available/strengthiva <<EOF
server {
    listen 80;
    server_name _;      # replace _ with your domain e.g. health.example.com

    client_max_body_size 50M;

    location / {
        proxy_pass         http://127.0.0.1:$PORT;
        proxy_http_version 1.1;

        # WebSocket support (Streamlit requires this)
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

# Enable site, disable default
ln -sf /etc/nginx/sites-available/strengthiva /etc/nginx/sites-enabled/strengthiva
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl reload nginx
ok "Nginx configured and reloaded."

# ── 9. Firewall ───────────────────────────────────────────────────────────────
log "Configuring UFW firewall..."
ufw allow OpenSSH  -q
ufw allow 'Nginx Full' -q
ufw --force enable -q
ok "Firewall rules applied (SSH + HTTP/HTTPS open)."

# ── 10. Summary ───────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════"
ok "Installation complete."
echo ""
echo "  App directory : $APP_DIR"
echo "  App user      : $APP_USER"
echo "  Streamlit port: $PORT (internal, not exposed)"
echo "  Nginx         : port 80 → http://127.0.0.1:$PORT"
echo "  Logs          : /var/log/strengthiva/"
echo ""
echo "  Next steps:"
echo "  1. Edit $APP_DIR/.env  →  set OPENAI_API_KEY"
echo "  2. (optional) Set your domain in /etc/nginx/sites-available/strengthiva"
echo "  3. (optional) Run: certbot --nginx  to add HTTPS"
echo "  4. Run: bash $(dirname "$SCRIPT_DIR")/deploy/start.sh"
echo "════════════════════════════════════════════════════════"
