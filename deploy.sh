#!/bin/bash
set -e

SITE_DIR="$(cd "$(dirname "$0")" && pwd)"
#SERVER="root@bonzeipunk.de"
SERVER="punk"
SSH_KEY="/Users/jessi/.ssh/vpsserver/vpsserver"
REMOTE_DIR="/var/www/emy-karate"

echo "▶ Hugo bauen..."
cd "$SITE_DIR"
hugo --minify

echo "▶ SSH-Key laden..."
#SSH_ASKPASS_REQUIRE=never ssh-add "$SSH_KEY" <<< "bonzeikiller" 2>/dev/null || true
#SSH_ASKPASS_REQUIRE=never ssh-add "$SSH_KEY"  2>/dev/null || true
echo "▶ Auf Server übertragen..."
rsync -az --delete \
  -e "ssh -o StrictHostKeyChecking=no -i $SSH_KEY" \
  "$SITE_DIR/public/" "$SERVER:$REMOTE_DIR/"

echo ""
echo "✓ Fertig! https://emy-karate.de"
