# Deploy — Ayurvedic Health Assessment App

Targets Ubuntu 22.04 / Debian 12 VPS. All scripts must run as **root**.

## Files

| File | Purpose |
|---|---|
| `install.sh` | One-time server setup (system packages, user, venv, Nginx, Supervisor) |
| `start.sh` | Start / restart all services + tail live logs |
| `update.sh` | Pull new code and hot-reload without downtime |

## Architecture

```
Internet → Nginx :80 → Streamlit :8501 (supervisor-managed)
```

---

## Fresh VPS — step by step

### 1. Copy project to server
```bash
# From your local machine:
scp -r /path/to/strengthiva  root@<your-server-ip>:/tmp/strengthiva_src
```

Or clone directly on the server if it's in a git repo.

### 2. Run installer (once)
```bash
ssh root@<your-server-ip>
cd /tmp/strengthiva_src/deploy
bash install.sh
```

### 3. Set your OpenAI key
```bash
nano /opt/strengthiva/.env
# Set: OPENAI_API_KEY=sk-...
```

### 4. Start everything
```bash
bash /tmp/strengthiva_src/deploy/start.sh
```

That's it. The app will be live at `http://<your-server-ip>`.

---

## HTTPS (optional, needs a domain)

```bash
# Point your domain's A-record to the server IP first, then:
certbot --nginx -d health.yourdomain.com
```

Certbot will auto-edit the Nginx config and set up auto-renewal.

---

## Useful commands

```bash
# Service status
supervisorctl status strengthiva

# Live app log
tail -f /var/log/strengthiva/app.log

# Live error log
tail -f /var/log/strengthiva/error.log

# Restart app
supervisorctl restart strengthiva

# Stop app
supervisorctl stop strengthiva

# Nginx status
systemctl status nginx

# Deploy update
bash /opt/strengthiva/deploy/update.sh
```

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key |

Set in `/opt/strengthiva/.env`. File is never overwritten by `update.sh`.

## Ports

| Port | Service | Exposed |
|---|---|---|
| 80 | Nginx (HTTP) | Yes — public |
| 443 | Nginx (HTTPS, after certbot) | Yes — public |
| 8501 | Streamlit | No — localhost only |
