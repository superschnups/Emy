import sqlite3
import time
import hashlib
import random
import string

def get_guid():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def get_csum(fld):
    return int(hashlib.sha1(fld.encode('utf-8')).hexdigest()[:8], 16)

def add_card(db_path, deck_id, model_id, front, back):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # IDs are typically timestamps in ms
    note_id = int(time.time() * 1000)
    # To avoid collision if we add multiple at once
    time.sleep(0.005)
    card_id = int(time.time() * 1000)
    
    guid = get_guid()
    mod_time = int(time.time())
    usn = -1 # -1 for sync
    tags = ''
    flds = f"{front}\x1f{back}"
    csum = get_csum(front)
    
    # Insert note
    cursor.execute("""
        INSERT INTO notes (id, guid, mid, mod, usn, tags, flds, sfld, csum, flags, data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (note_id, guid, model_id, mod_time, usn, tags, flds, front, csum, 0, ''))
    
    # Insert card
    # due = count of cards in the deck
    cursor.execute("SELECT COUNT(*) FROM cards WHERE did = ?", (deck_id,))
    due = cursor.fetchone()[0] + 1
    
    cursor.execute("""
        INSERT INTO cards (id, nid, did, ord, mod, usn, type, queue, due, ivl, factor, reps, lapses, left, odue, odid, flags, data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (card_id, note_id, deck_id, 0, mod_time, usn, 0, 0, due, 0, 0, 0, 0, 0, 0, 0, 0, ''))
    
    conn.commit()
    conn.close()
    print(f"Card added: {front}")

db_path = '/Users/jessi/Library/Application Support/Anki2/Benutzer 1/collection.anki2'
deck_id = 1668085869571 # Default
model_id = 1342697580586 # Basic

add_card(db_path, deck_id, model_id, "Wer ist dein neuer Senior-Engineer im Terminal?", "Gemini CLI")
add_card(db_path, deck_id, model_id, "Was ist der größte Vorteil der Sub-Agenten Delegation?", "Dass komplexe Aufgaben im Hintergrund erledigt werden, während der Chat sauber bleibt.")
