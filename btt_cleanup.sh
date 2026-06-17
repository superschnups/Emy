#!/bin/bash
# BTT Tabula Rasa – Cleanup Script
# Löscht alle alten Datenbankdateien, behält Lizenz und Einstellungen.
# BTT MUSS beendet sein bevor dieses Script läuft!
#
# Ausführen: bash ~/bin/btt_cleanup.sh

BTT_DIR="$HOME/Library/Application Support/BetterTouchTool"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║           BTT CLEANUP – Tabula Rasa                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── Sicherheitscheck: läuft BTT noch? ───────────────────────────────────────
if pgrep -x "BetterTouchTool" > /dev/null; then
    echo "  ✗  BetterTouchTool läuft noch – bitte zuerst beenden!"
    echo "     killall BetterTouchTool  oder  Menüleiste → Quit BTT"
    echo ""
    exit 1
fi

echo "  ✓  BetterTouchTool ist nicht aktiv"
echo ""

# ── Was wird gelöscht? ───────────────────────────────────────────────────────
echo "  Folgende Dateien werden gelöscht:"
echo "  ─────────────────────────────────────────────────────────"
FILES_TO_DELETE=$(find "$BTT_DIR" -maxdepth 1 -name "btt_data_store.*" -type f)
COUNT=0
TOTAL_SIZE=0
while IFS= read -r f; do
    SIZE=$(du -sh "$f" 2>/dev/null | cut -f1)
    echo "  🗑  $(basename "$f")  ($SIZE)"
    COUNT=$((COUNT + 1))
done <<< "$FILES_TO_DELETE"

echo ""
echo "  Folgende Dateien BLEIBEN erhalten:"
echo "  ─────────────────────────────────────────────────────────"
echo "  ✓  bettertouchtool.bttlicense"
echo "  ✓  btt_usage_v2.plist"
echo "  ✓  btt_user_variables.plist"
echo "  ✓  floating_menu_variables.plist"
echo "  ✓  Backups/"
echo "  ✓  PresetBundles/"
echo "  ✓  Logs/"
echo ""

if [ $COUNT -eq 0 ]; then
    echo "  Keine Datenbankdateien gefunden – nichts zu tun."
    exit 0
fi

# ── Bestätigung ──────────────────────────────────────────────────────────────
echo "  $COUNT Datei(en) werden permanent gelöscht."
echo ""
read -p "  Fortfahren? (ja/nein): " CONFIRM

if [ "$CONFIRM" != "ja" ]; then
    echo ""
    echo "  Abgebrochen. Nichts wurde gelöscht."
    exit 0
fi

# ── Löschen ──────────────────────────────────────────────────────────────────
echo ""
echo "  Lösche Datenbankdateien..."
while IFS= read -r f; do
    rm "$f" && echo "  ✓  $(basename "$f")" || echo "  ✗  Fehler bei: $(basename "$f")"
done <<< "$FILES_TO_DELETE"

# ── iCloud Sync-Cache prüfen ─────────────────────────────────────────────────
ICLOUD_BTT="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Library/Application Support/BetterTouchTool"
if [ -d "$ICLOUD_BTT" ]; then
    echo ""
    echo "  ──────────────────────────────────────────────────────"
    echo "  ⚠  iCloud BTT-Ordner gefunden:"
    echo "     $ICLOUD_BTT"
    ICLOUD_COUNT=$(find "$ICLOUD_BTT" -name "btt_data_store.*" | wc -l | tr -d ' ')
    echo "     $ICLOUD_COUNT Datenbankdateien in iCloud"
    echo ""
    read -p "  iCloud-Datenbanken auch löschen? (ja/nein): " ICLOUD_CONFIRM
    if [ "$ICLOUD_CONFIRM" = "ja" ]; then
        find "$ICLOUD_BTT" -name "btt_data_store.*" -type f -delete
        echo "  ✓  iCloud-Datenbanken gelöscht"
    else
        echo "  iCloud übersprungen – BTT könnte die alte DB von dort zurückspielen!"
    fi
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Fertig! Nächste Schritte:                              ║"
echo "║                                                          ║"
echo "║  1. BetterTouchTool starten                              ║"
echo "║     → BTT erstellt eine frische, leere Datenbank         ║"
echo "║  2. File → Import Preset → dein .bttpreset Backup        ║"
echo "║     → Alle Shortcuts sind wieder da, keine Duplikate     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
