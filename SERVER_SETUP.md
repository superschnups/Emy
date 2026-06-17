# Setup Admin-Server auf dem VPS

Diese Anleitung hilft dir, den Admin-Bereich (den du lokal unter `http://karate:3001` nutzt) auch auf deinem Server verfügbar zu machen.

## 1. Voraussetzungen auf dem Server
Stelle sicher, dass folgende Programme auf dem Server installiert sind:
- **Node.js** (v18+)
- **Hugo** (für den Rebuild)
- **Git** (zum Übertragen der Daten)

## 2. Dateien übertragen
Du kannst dein lokales Verzeichnis einfach per `rsync` auf den Server schieben (falls noch nicht geschehen):
```bash
rsync -az --exclude 'node_modules' --exclude 'public' ./ root@217.160.212.198:/opt/karatehp/
```

## 3. Installation auf dem Server
Wechsle auf dem Server in das Verzeichnis und installiere die Abhängigkeiten:
```bash
cd /opt/karatehp
npm install
```

## 4. Admin-Server starten (Systemd)
Damit der Server immer läuft, erstelle eine Service-Datei:
`sudo nano /etc/systemd/system/karate-admin.service`

Inhalt:
```ini
[Unit]
Description=MiyaKarate Admin Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/karatehp
ExecStart=/usr/bin/node admin-server.js
Restart=always

[Install]
WantedBy=multi-user.target
```

Danach aktivieren:
```bash
sudo systemctl daemon-reload
sudo systemctl enable karate-admin
sudo systemctl start karate-admin
```

## 5. Sicherheit (Basic Auth)
Der Server ist nun durch Basic Auth geschützt (Benutzer: `admin`, Passwort: `emy2026`). 
**Wichtig:** Ändere das Passwort in der `admin-server.js` Datei auf dem Server!

## 6. Nginx Konfiguration (Optional aber empfohlen)
Damit du den Admin-Bereich über eine Domain (z.B. `admin.emy.bonzeipunk.de`) erreichen kannst, füge dies zu deiner Nginx-Konf hinzu:

```nginx
server {
    listen 80;
    server_name admin.emy.bonzeipunk.de;

    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Vergiss nicht, `certbot` für SSL zu nutzen!
