#!/bin/bash
# Sync-Script für Shortcuts-Datenbank von Mac zu VPS
set -euo pipefail

LOCAL_FILE="/Users/jessi/Library/Application Support/com.jessi.precision_engine/shortcuts.json"
REMOTE_DEST="root@217.160.212.198:/opt/karatehp/DEV/shortcut-app/data/shortcuts.json"

if [ ! -f "$LOCAL_FILE" ]; then
    echo "❌ Fehler: Lokale Datei $LOCAL_FILE existiert nicht!"
    exit 1
fi

echo "🚀 Synce Shortcuts zu VPS (${REMOTE_DEST})..."
rsync -az "$LOCAL_FILE" "$REMOTE_DEST"
echo "✅ Synchronisation erfolgreich abgeschlossen!"
