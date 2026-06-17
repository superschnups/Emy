#!/bin/bash

source="/Users/jessi/Library/Application Support/BetterTouchTool"
destination_nvme="/Volumes/nvme/Sascha_Data/betterTouchTool_backups_hier_und_icloud_backup_folder"
destination_icloud="/Users/jessi/Library/Mobile Documents/com~apple~CloudDocs/backups/macosbackis/bettertouchtool/BetterTouchToolWeeklyZip"
email_recipient="rodegang@googlemail.com"
state_file="$HOME/.btt_last_icloud_run"

function handle_error() {
    local message="$1"
    echo "❌ Error: $message"
    
    # macOS Notification
    osascript -e "display notification \"$message\" with title \"BTT Backup Fehler\""
    
    # Email senden
    echo "$message" | mail -s "Fehler: BetterTouchTool Backup" "$email_recipient"
    
    exit 1
}


function backup_better_touch_tool_nvme() {
    
    timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
    backup_filename="BetterTouchToolBackup_$timestamp.zip"
    backup_path="$destination_nvme/$backup_filename"
    
    # Create a zip archive of the BetterTouchTool data
    zip -r "$backup_path" "$source" || handle_error "Zip-Erstellung fehlgeschlagen (NVMe)"
    
    echo "Backup created at: $backup_path"
}


function backup_better_touch_tool_icloud() {
    
    timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
    backup_filename="BetterTouchToolBackup_$timestamp.zip"
    backup_path="$destination_icloud/$backup_filename"
    
    # Create a zip archive of the BetterTouchTool data
    zip -r "$backup_path" "$source" || handle_error "Zip-Erstellung fehlgeschlagen (iCloud)"
    
    echo "Backup created at: $backup_path"
}

function check_folders() {
    if [ ! -d "$source" ]; then
        handle_error "Quellordner existiert nicht: $source"
    fi
    
    if [ ! -d "$destination_nvme" ]; then
        handle_error "Zielordner NVMe existiert nicht: $destination_nvme"
    fi
    
    if [ ! -d "$destination_icloud" ]; then
        handle_error "Zielordner iCloud existiert nicht: $destination_icloud"
    fi
}

function start_backup() {
    check_folders
    
    # NVMe Backup immer ausführen
    backup_better_touch_tool_nvme
    
    # iCloud Backup nur alle 3 Tage (259200 Sekunden)
    current_time=$(date +%s)
    last_run=0
    
    if [ -f "$state_file" ]; then
        last_run=$(cat "$state_file")
    fi
    
    time_diff=$((current_time - last_run))
    
    if [ $time_diff -ge 259200 ]; then
        echo "⏳ 3 Tage vergangen. Starte iCloud Backup..."
        backup_better_touch_tool_icloud
        echo "$current_time" > "$state_file"
    else
        days_left=$(( (259200 - time_diff) / 86400 ))
        echo "⏭️ iCloud Backup übersprungen (letztes Backup war vor weniger als 3 Tagen). Nächstes in ca. $days_left Tagen."
    fi
}

start_backup