#!/usr/bin/env python3
"""
BTT Diagnose-Script
Findet duplizierte und verdächtige Keyboard Shortcuts in der BTT-Datenbank.
Einfach ausführen: python3 ~/bin/btt_diagnose.py
"""

import sqlite3
import os
import glob
import sys
import shutil
import tempfile
from datetime import datetime

# ── Key Code → Lesbare Bezeichnung ──────────────────────────────────────────
KEYCODES = {
    0:'A', 1:'S', 2:'D', 3:'F', 4:'H', 5:'G', 6:'Z', 7:'X', 8:'C', 9:'V',
    11:'B', 12:'Q', 13:'W', 14:'E', 15:'R', 16:'Y', 17:'T',
    18:'1', 19:'2', 20:'3', 21:'4', 23:'5', 24:'=', 25:'9', 26:'7',
    27:'-', 28:'8', 29:'0', 30:']', 31:'O', 32:'U', 33:'[', 34:'I', 35:'P',
    36:'Return', 37:'L', 38:'J', 39:"'", 40:'K', 41:';', 42:'\\',
    43:',', 44:'/', 45:'N', 46:'M', 47:'.', 48:'Tab', 49:'Space',
    50:'`', 51:'Delete', 53:'Escape', 65:'Numpad.', 67:'Numpad*',
    69:'Numpad+', 75:'Numpad/', 76:'NumpadEnter', 78:'Numpad-',
    81:'Numpad=', 82:'Numpad0', 83:'Numpad1', 84:'Numpad2', 85:'Numpad3',
    86:'Numpad4', 87:'Numpad5', 88:'Numpad6', 89:'Numpad7',
    91:'Numpad8', 92:'Numpad9',
    96:'F5', 97:'F6', 98:'F7', 99:'F3', 100:'F8', 101:'F9', 103:'F11',
    105:'F13', 106:'F16', 107:'F14', 109:'F10', 111:'F12', 113:'F15',
    115:'Home', 116:'PageUp', 117:'ForwardDelete', 118:'F4', 119:'End',
    120:'F2', 121:'PageDown', 122:'F1',
    123:'←', 124:'→', 125:'↓', 126:'↑',
    -1:'(kein Key)',
}

def decode_key(code):
    return KEYCODES.get(code, f'KeyCode_{code}')

# ── Modifier Flags → Lesbare Bezeichnung ────────────────────────────────────
MOD_FLAGS = [
    (8388608, 'Fn'),
    (1048576, '⌘'),
    (524288,  '⌥'),
    (262144,  '⌃'),
    (131072,  '⇧'),
    (65536,   'CapsLock'),
]

def decode_mod(mod):
    if mod is None or mod <= 0:
        return '(kein Modifier)'
    parts = []
    for flag, name in MOD_FLAGS:
        if mod & flag:
            parts.append(name)
    return '+'.join(parts) if parts else f'Mod_{mod}'

def shortcut_str(keycode, mod):
    return f"{decode_mod(mod)}+{decode_key(keycode)}"

# ── BTT Datenbank finden ─────────────────────────────────────────────────────
def find_btt_db():
    base = os.path.expanduser('~/Library/Application Support/BetterTouchTool/')
    pattern = os.path.join(base, 'btt_data_store.version_*')
    candidates = [
        f for f in glob.glob(pattern)
        if not f.endswith(('-shm', '-wal'))
        and '_tmp_backup' not in f
    ]
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)

# ── Analyse ──────────────────────────────────────────────────────────────────
def analyse(db_path):
    print(f"\n{'='*60}")
    print(f"  BTT SHORTCUT DIAGNOSE")
    print(f"  {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"  DB: {os.path.basename(db_path)}\n")

    tmp = tempfile.mktemp(suffix='.db')
    shutil.copy2(db_path, tmp)

    conn = sqlite3.connect(tmp)
    cur = conn.cursor()

    # ── Integrity Check ──────────────────────────────────────────────────────
    cur.execute("PRAGMA integrity_check")
    ic = cur.fetchone()[0]
    status = "✓ OK" if ic == 'ok' else f"✗ FEHLER: {ic}"
    print(f"  Datenbankintegrität:  {status}")

    # ── Gesamt-Statistik ─────────────────────────────────────────────────────
    cur.execute("SELECT COUNT(*) FROM ZBTTBASEENTITY WHERE ZGESTURETYPE = 0")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM ZBTTBASEENTITY WHERE ZGESTURETYPE = 0 AND ZISENABLED = 1")
    enabled = cur.fetchone()[0]
    print(f"  Keyboard Shortcuts:   {total} gesamt, {enabled} aktiv\n")

    # ── 1. Duplikate ─────────────────────────────────────────────────────────
    cur.execute('''
        SELECT ZKEYCODE, ZMODIFIERKEYS, COUNT(*) as cnt, GROUP_CONCAT(Z_PK) as pks
        FROM ZBTTBASEENTITY
        WHERE ZGESTURETYPE = 0 AND ZKEYCODE >= 0
        GROUP BY ZKEYCODE, ZMODIFIERKEYS
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC, ZKEYCODE
    ''')
    dupes = cur.fetchall()

    if dupes:
        print(f"  ⚠  DUPLIZIERTE SHORTCUTS ({len(dupes)} Kombinationen)")
        print(f"  {'─'*54}")
        for keycode, mod, cnt, pks in dupes:
            shortcut = shortcut_str(keycode, mod)
            pk_list = [int(p) for p in pks.split(',')]
            entries = []
            for pk in pk_list:
                cur.execute('''
                    SELECT ZTRIGGERLABEL, ZACTIONLABEL, ZNAME, ZISENABLED,
                           ZBELONGSTOPRESET, ZBUNDLEIDENTIFIER
                    FROM ZBTTBASEENTITY WHERE Z_PK = ?
                ''', (pk,))
                row = cur.fetchone()
                if row:
                    label = row[0] or row[1] or row[2] or '(kein Label)'
                    enabled_str = '✓' if row[3] == 1 else '✗'
                    app = row[5] or 'Global'
                    entries.append((pk, label, enabled_str, app))

            print(f"\n  [{cnt}x] {shortcut}")
            for pk, label, en, app in entries:
                print(f"        PK={pk:5}  {en}  App: {app:<35}  Label: {label}")
    else:
        print("  ✓  Keine duplizierten Shortcuts gefunden")

    print()

    # ── 2. Shortcuts ohne Action ─────────────────────────────────────────────
    cur.execute('''
        SELECT Z_PK, ZKEYCODE, ZMODIFIERKEYS, ZTRIGGERLABEL, ZISENABLED
        FROM ZBTTBASEENTITY
        WHERE ZGESTURETYPE = 0
          AND ZISENABLED = 1
          AND ZKEYCODE >= 0
          AND ZACTIONDATA IS NULL
          AND ZADDITIONALACTIONSTRING IS NULL
          AND ZGESTURECONFIG IS NULL
    ''')
    no_action = cur.fetchall()
    if no_action:
        print(f"  ⚠  AKTIVE SHORTCUTS OHNE AKTION ({len(no_action)} Stück)")
        print(f"  {'─'*54}")
        for pk, kc, mod, label, en in no_action:
            print(f"  PK={pk:5}  {shortcut_str(kc, mod):<25}  Label: {label or '(kein Label)'}")
        print()
    else:
        print("  ✓  Alle aktiven Shortcuts haben eine Aktion\n")

    # ── 3. Shortcuts mit KeyCode -1 (defekt) ────────────────────────────────
    cur.execute('''
        SELECT COUNT(*) FROM ZBTTBASEENTITY
        WHERE ZGESTURETYPE = 0 AND ZKEYCODE = -1 AND ZISENABLED = 1
    ''')
    broken = cur.fetchone()[0]
    if broken > 0:
        print(f"  ⚠  AKTIVE SHORTCUTS MIT UNGÜLTIGEM KEYCODE (-1): {broken}")
        cur.execute('''
            SELECT Z_PK, ZMODIFIERKEYS, ZTRIGGERLABEL, ZACTIONLABEL
            FROM ZBTTBASEENTITY
            WHERE ZGESTURETYPE = 0 AND ZKEYCODE = -1 AND ZISENABLED = 1
        ''')
        for pk, mod, tl, al in cur.fetchall():
            label = tl or al or '(kein Label)'
            print(f"  PK={pk:5}  Mod={decode_mod(mod)}  Label: {label}")
        print()
    else:
        print("  ✓  Keine Shortcuts mit ungültigem KeyCode\n")

    # ── Zusammenfassung ──────────────────────────────────────────────────────
    print(f"{'='*60}")
    total_issues = len(dupes) + (len(no_action) if no_action else 0) + broken
    if total_issues == 0:
        print("  ✓  Alles in Ordnung – keine Probleme gefunden")
    else:
        print(f"  ⚠  {total_issues} Problem(e) gefunden")
        if dupes:
            print(f"     • {len(dupes)} duplizierte Shortcut-Kombinationen")
            print(f"       → Löschen und neu anlegen behebt das Problem")
        if no_action:
            print(f"     • {len(no_action)} aktive Shortcuts ohne Aktion")
        if broken:
            print(f"     • {broken} Shortcuts mit ungültigem KeyCode")
    print(f"{'='*60}\n")

    conn.close()
    os.unlink(tmp)

# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) > 1:
        db = sys.argv[1]
    else:
        db = find_btt_db()

    if not db or not os.path.exists(db):
        print("✗ BTT-Datenbank nicht gefunden.")
        print("  Pfad manuell angeben: python3 ~/bin/btt_diagnose.py /pfad/zur/db")
        sys.exit(1)

    analyse(db)
