import json
import os

class ShortcutManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.shortcuts = self._load_data()

    def _load_data(self):
        if not os.path.exists(self.db_path):
            return []
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def save_data(self):
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.shortcuts, f, indent=2, ensure_ascii=False)

    def add_shortcut(self, name, command, description="", tags=None):
        if tags is None:
            tags = []
        self.shortcuts.append({
            "name": name,
            "command": command,
            "description": description,
            "tags": tags
        })
        self.save_data()

    def search(self, query):
        query = query.lower()
        results = []
        for s in self.shortcuts:
            if (query in s['name'].lower() or 
                query in s['description'].lower() or 
                any(query in t.lower() for t in s['tags'])):
                results.append(s)
        return results

    def list_all(self):
        return self.shortcuts
