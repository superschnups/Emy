import argparse
import sys
import os
from manager import ShortcutManager

def main():
    # Pfad zur JSON-Datenbank relativ zum Skript
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'data', 'shortcuts.json')
    
    manager = ShortcutManager(db_path)
    
    parser = argparse.ArgumentParser(description="Shortcut-App: Verwalte deine Terminal-Befehle")
    subparsers = parser.add_subparsers(dest="command", help="Verfügbare Befehle")

    # List-Befehl
    subparsers.add_parser("list", help="Alle Shortcuts anzeigen")

    # Search-Befehl
    search_parser = subparsers.add_parser("search", help="Nach Shortcuts suchen")
    search_parser.add_argument("query", help="Suchbegriff (Name, Beschreibung oder Tag)")

    # Add-Befehl
    add_parser = subparsers.add_parser("add", help="Einen neuen Shortcut hinzufügen")
    add_parser.add_argument("--name", required=True, help="Name des Shortcuts")
    add_parser.add_argument("--cmd", required=True, help="Der eigentliche Befehl")
    add_parser.add_argument("--desc", default="", help="Beschreibung des Befehls")
    add_parser.add_argument("--tags", nargs="*", default=[], help="Tags zur Kategorisierung")

    args = parser.parse_args()

    if args.command == "list":
        shortcuts = manager.list_all()
        if not shortcuts:
            print("Keine Shortcuts gefunden.")
        for s in shortcuts:
            print(f"[{s['name']}] -> {s['command']} | {s['description']}")

    elif args.command == "search":
        results = manager.search(args.query)
        if not results:
            print(f"Keine Ergebnisse für '{args.query}' gefunden.")
        for s in results:
            print(f"Gefunden: [{s['name']}] -> {s['command']} ({s['description']})")

    elif args.command == "add":
        manager.add_shortcut(args.name, args.cmd, args.desc, args.tags)
        print(f"Shortcut '{args.name}' erfolgreich hinzugefügt.")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
