#!/bin/bash
# ============================================================================
# GMS Chatbot -- own-server AI setup script
#
# Run this ON your Oracle Cloud VM (or any Ubuntu VPS) after you've created
# it and SSH'd in. It installs Ollama, pulls a model, sets it to always run
# in the background, and puts a password-protected reverse proxy in front
# of it so random people on the internet can't use your server for free.
#
# Usage:
#   chmod +x oracle_setup.sh
#   ./oracle_setup.sh
# ============================================================================

set -e

echo "=== GMS Chatbot -- AI server setup ==="
echo ""

# 1. Install Ollama
echo "[1/6] Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# 2. Make Ollama listen on all network interfaces, not just localhost --
#    otherwise Vercel can never reach it from the outside
echo "[2/6] Configuring Ollama to accept external connections..."
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null << 'EOF'
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama
sudo systemctl enable ollama

# 3. Pull a model -- llama3.1 8B is a solid balance of quality and speed
#    for a CPU-only free-tier server. Swap this line if you want a
#    different one (mistral, qwen2.5, etc).
echo "[3/6] Pulling the model (this takes a few minutes)..."
ollama pull llama3.1

# 4. Generate a random secret token to protect your server -- Ollama has
#    NO built-in authentication, so anyone who finds your IP could use it
#    (and burn your server's resources) without this.
echo "[4/6] Generating your access token..."
SECRET_TOKEN=$(openssl rand -hex 24)
echo "$SECRET_TOKEN" > ~/gms_server_token.txt
echo "    Token saved to ~/gms_server_token.txt"

# 5. Install nginx as a reverse proxy that checks for the token before
#    forwarding requests to Ollama
echo "[5/6] Setting up the protected proxy (nginx on port 8443)..."
sudo apt-get update -y -qq
sudo apt-get install -y -qq nginx

sudo tee /etc/nginx/sites-available/gms-ai-proxy > /dev/null << EOF
server {
    listen 8443;

    location / {
        if (\$http_authorization != "Bearer ${SECRET_TOKEN}") {
            return 401;
        }
        proxy_pass http://127.0.0.1:11434;
        proxy_set_header Host \$host;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/gms-ai-proxy /etc/nginx/sites-enabled/gms-ai-proxy
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# 6. Open the port in the OS firewall (you STILL need to also open port
#    8443 in Oracle's web console under your instance's Security List /
#    Network Security Group -- this script can't do that part for you)
echo "[6/6] Opening port 8443 in the local firewall..."
sudo iptables -I INPUT -p tcp --dport 8443 -j ACCEPT 2>/dev/null || true
sudo netfilter-persistent save 2>/dev/null || true

echo ""
echo "=========================================================="
echo "  DONE. Your AI server is running."
echo "=========================================================="
echo ""
echo "  Your access token (also saved to ~/gms_server_token.txt):"
echo "  $SECRET_TOKEN"
echo ""
echo "  ONE MANUAL STEP LEFT (Oracle won't let this script do it):"
echo "  Go to your Oracle Cloud console -> your instance -> "
echo "  'Subnet' -> 'Security List' -> 'Add Ingress Rule':"
echo "    Source CIDR: 0.0.0.0/0"
echo "    Destination Port: 8443"
echo "    Protocol: TCP"
echo ""
echo "  Then in Vercel -> Settings -> Environment Variables, add:"
echo "    OWN_SERVER_URL   = http://<this-server's-public-IP>:8443"
echo "    OWN_SERVER_MODEL = llama3.1"
echo "    OWN_SERVER_TOKEN = $SECRET_TOKEN"
echo ""
echo "  Then redeploy on Vercel and test on /ai"
echo "=========================================================="
