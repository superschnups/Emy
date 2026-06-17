#!/usr/bin/env python3
import sqlite3
import time
import hashlib
import random
import string
import os
import sys
import subprocess

# --- LOGGING FUER DEBUGGING ---
LOG_FILE = "/tmp/anki_brain.log"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.strftime('%H:%M:%S')} - {msg}\n")

# --- KONFIGURATION ---
ANKI_BASE_PATH = os.path.expanduser("~/Library/Application Support/Anki2")

def find_anki_db():
    for root, dirs, files in os.walk(ANKI_BASE_PATH):
        if "collection.anki2" in files:
            return os.path.join(root, "collection.anki2")
    return None

def is_anki_running():
    try:
        # Voller Pfad zu pgrep, um sicherzugehen
        # -x sorgt fuer einen exakten Match auf 'anki'
        res = subprocess.run(["/usr/bin/pgrep", "-x", "anki"], capture_output=True)
        log(f"pgrep exit code: {res.returncode}")
        return res.returncode == 0
    except Exception as e:
        log(f"pgrep error: {e}")
        return False

def get_guid():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def get_csum(fld):
    return int(hashlib.sha1(fld.encode('utf-8')).hexdigest()[:8], 16)

def add_card(front, back, deck_name="Default", model_name="Basic"):
    log(f"Versuche Karte hinzuzufuegen: Front='{front}', Back='{back}'")
    
    if is_anki_running():
        msg = "Anki läuft noch! Bitte schließe Anki, bevor du Karten hinzufügst."
        log(msg)
        # Sound direkt abspielen, da osascript sound name unzuverlässig ist
        os.system("afplay /System/Library/Sounds/Sosumi.aiff &")
        cmd = f'osascript -e "display notification \\"{msg}\\" with title \\"Anki-Brain Fehler\\""'
        os.system(cmd)
        return False

    db_path = find_anki_db()
    if not db_path:
        log("Datenbank nicht gefunden")
        return False

    try:
        conn = sqlite3.connect(db_path)
        conn.create_collation("unicase", lambda a, b: (a > b) - (a < b))
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM decks WHERE name = ?", (deck_name,))
        res = cursor.fetchone()
        deck_id = res[0] if res else 1

        cursor.execute("SELECT id FROM notetypes WHERE name = ?", (model_name,))
        res = cursor.fetchone()
        model_id = res[0] if res else None
        
        if not model_id:
            cursor.execute("SELECT id FROM notetypes WHERE name LIKE 'Basic%' OR name LIKE 'Einfach%' LIMIT 1")
            res = cursor.fetchone()
            model_id = res[0] if res else None

        if not model_id:
            log("Notiztyp nicht gefunden")
            return False

        note_id = int(time.time() * 1000)
        time.sleep(0.01)
        card_id = int(time.time() * 1000)
        
        guid = get_guid()
        mod_time = int(time.time())
        flds = f"{front}\x1f{back}"
        csum = get_csum(front)

        cursor.execute("""
            INSERT INTO notes (id, guid, mid, mod, usn, tags, flds, sfld, csum, flags, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (note_id, guid, model_id, mod_time, -1, '', flds, front, csum, 0, ''))

        cursor.execute("SELECT COUNT(*) FROM cards WHERE did = ?", (deck_id,))
        due = cursor.fetchone()[0] + 1
        
        cursor.execute("""
            INSERT INTO cards (id, nid, did, ord, mod, usn, type, queue, due, ivl, factor, reps, lapses, left, odue, odid, flags, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (card_id, note_id, deck_id, 0, mod_time, -1, 0, 0, due, 0, 0, 0, 0, 0, 0, 0, 0, ''))

        # Update collection modification time and set usn to -1 to notify Anki of changes
        cursor.execute("UPDATE col SET mod = ?, usn = -1", (int(time.time() * 1000),))

        conn.commit()
        conn.close()
        log("Erfolgreich hinzugefuegt")
        return True
    except Exception as e:
        log(f"Datenbankfehler: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
    
    f = sys.argv[1]
    b = sys.argv[2]
    d = sys.argv[3] if len(sys.argv) > 3 else "Default"
    
    add_card(f, b, d)
