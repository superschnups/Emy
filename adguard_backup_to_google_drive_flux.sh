#!/bin/bash

# --- KONFIGURATION ---
RASPI_IP="192.168.0.61"
RASPI_USER="sascha"                 # Tausche 'root' gegen 'pi' falls du dich nicht als root einloggst
ADGUARD_DIR="/opt/AdGuardHome"
DRIVE_DIR="/Volumes/nvme/google_drive_meine_Ablage/AdGuard_Backup"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="${DRIVE_DIR}/adguard_backup_${TIMESTAMP}.tar.gz"

# 1. Auf dem Raspi lokal in /tmp komprimieren
echo "📦 Packe AdGuard-Ordner lokal auf dem Raspi..."
ssh  -i /Users/jessi/.ssh/adguard/adguard  ${RASPI_USER}@${RASPI_IP} "sudo tar -czf /tmp/adguard_temp.tar.gz ${ADGUARD_DIR}"

# 2. Das fertige Paket auf den Mac ins Google Drive ziehen
echo "🚚 Beame Backup rüber in dein Google Drive..."
scp -i /Users/jessi/.ssh/adguard/adguard ${RASPI_USER}@${RASPI_IP}:/tmp/adguard_temp.tar.gz "${BACKUP_FILE}"

# 3. Den temporären Müll auf dem Raspi wieder aufräumen
ssh -i /Users/jessi/.ssh/adguard/adguard ${RASPI_USER}@${RASPI_IP} "sudo rm /tmp/adguard_temp.tar.gz"

if [ $? -eq 0 ]; then
    echo "✅ Backup erfolgreich! Datei liegt im Drive: adguard_backup_${TIMESTAMP}.tar.gz"
else
    echo "❌ Fehler! Überprüfe die Pfade."
fi