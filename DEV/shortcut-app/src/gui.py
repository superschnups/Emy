import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime

class ShortcutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Shortcut Hub")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f5f5f7") # Heller Apple-ähnlicher Hintergrund
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, 'data', 'shortcuts.json')
        self.data = self.load_data()
        self.last_mtime = os.path.getmtime(self.db_path) if os.path.exists(self.db_path) else 0

        self.apply_styles()
        self.setup_ui()
        self.root.bind("<FocusIn>", self.on_focus_in)

    def load_data(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: return {}
        return {}

    def save_data(self):
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        self.last_mtime = os.path.getmtime(self.db_path) if os.path.exists(self.db_path) else 0

    def on_focus_in(self, event):
        if event.widget == self.root:
            mtime = os.path.getmtime(self.db_path) if os.path.exists(self.db_path) else 0
            if mtime != self.last_mtime:
                self.last_mtime = mtime
                self.data = self.load_data()
                
                # App-Auswahl merken und Liste aktualisieren
                current_selection = self.app_listbox.curselection()
                selected_app = self.app_listbox.get(current_selection[0]).strip() if current_selection else None
                
                self.refresh_app_list()
                
                if selected_app:
                    # Versuche die vorherige App wieder zu selektieren
                    for i in range(self.app_listbox.size()):
                        if self.app_listbox.get(i).strip() == selected_app:
                            self.app_listbox.selection_clear(0, tk.END)
                            self.app_listbox.select_set(i)
                            self.refresh_shortcuts(selected_app)
                            break
                else:
                    self.refresh_shortcuts()
                self.refresh_history()

    def apply_styles(self):
        style = ttk.Style()
        style.theme_use('clam') # Basis für modernes Styling

        # Allgemeine Farben
        bg_color = "#f5f5f7"
        sidebar_color = "#ffffff"
        accent_color = "#007aff" # macOS Blue

        # Frame Styling
        style.configure("TFrame", background=bg_color)
        style.configure("Sidebar.TFrame", background=sidebar_color)

        # Button Styling (Professional & Flat)
        style.configure("TButton", padding=6, font=("Segoe UI", 9))
        style.map("TButton", background=[('active', '#e1e1e1')])

        # Treeview (Tabelle) Styling
        style.configure("Treeview", 
                        rowheight=30, 
                        font=("Segoe UI", 10), 
                        background="white", 
                        fieldbackground="white",
                        borderwidth=0)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#eeeeee")
        style.map("Treeview", background=[('selected', accent_color)], foreground=[('selected', 'white')])

        # Label Styling
        style.configure("TLabel", background=bg_color, font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))

    def setup_ui(self):
        # --- OBERER BEREICH (Suche & History) ---
        header_frame = tk.Frame(self.root, bg="#f5f5f7", height=100)
        header_frame.pack(fill=tk.X, padx=20, pady=15)
        
        # Suche auf der linken Seite
        search_container = tk.Frame(header_frame, bg="#f5f5f7")
        search_container.pack(side=tk.LEFT, anchor="center")
        
        tk.Label(search_container, text="SUCHE", font=("Segoe UI", 9, "bold"), bg="#f5f5f7", fg="#86868b").pack(anchor=tk.W)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search_change)
        self.search_entry = tk.Entry(search_container, textvariable=self.search_var, width=35, 
                                    font=("Segoe UI", 12), relief=tk.FLAT, highlightthickness=1, 
                                    highlightbackground="#d2d2d7", highlightcolor="#007aff")
        self.search_entry.pack(pady=5)
        
        # History auf der rechten Seite (breit gezogen)
        history_container = tk.Frame(header_frame, bg="#f5f5f7")
        history_container.pack(side=tk.RIGHT, fill=tk.Y)
        
        tk.Label(history_container, text="RECENT UPDATES", font=("Segoe UI", 9, "bold"), bg="#f5f5f7", fg="#86868b").pack(anchor=tk.E)
        self.history_text = tk.Text(history_container, height=3, width=70, font=("Segoe UI", 10), 
                                   bg="#f5f5f7", borderwidth=0, highlightthickness=0, cursor="arrow")
        self.history_text.pack(pady=5)
        self.history_text.tag_configure("red_bold", foreground="#d70015", font=("Segoe UI", 10, "bold")) # Apple Red
        self.history_text.tag_configure("gray", foreground="#86868b", font=("Segoe UI", 10))
        self.history_text.tag_configure("right", justify='right')

        # --- HAUPTBEREICH (SplitView) ---
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # --- LINKS: APPS SIDEBAR ---
        self.left_frame = tk.Frame(self.paned, bg="white", padx=10, pady=10)
        self.paned.add(self.left_frame, weight=1)

        btn_bar_left = tk.Frame(self.left_frame, bg="white")
        btn_bar_left.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(btn_bar_left, text="App +", command=self.add_app).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        ttk.Button(btn_bar_left, text="Edit", command=self.rename_app).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        ttk.Button(btn_bar_left, text="Del", command=self.delete_app).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        self.app_listbox = tk.Listbox(self.left_frame, font=("Segoe UI", 11), selectmode=tk.SINGLE, 
                                     relief=tk.FLAT, borderwidth=0, highlightthickness=0,
                                     activestyle='none', selectbackground="#e8f2ff", selectforeground="black")
        self.app_listbox.pack(fill=tk.BOTH, expand=True)
        self.app_listbox.bind('<<ListboxSelect>>', self.on_app_select)

        # --- RECHTS: CONTENT AREA ---
        self.right_frame = tk.Frame(self.paned, bg="white", padx=15, pady=10)
        self.paned.add(self.right_frame, weight=4)

        top_right_header = tk.Frame(self.right_frame, bg="white")
        top_right_header.pack(fill=tk.X, pady=(0, 15))

        self.label_current_app = tk.Label(top_right_header, text="Alle Shortcuts", font=("Segoe UI", 16, "bold"), bg="white")
        self.label_current_app.pack(side=tk.LEFT)

        btn_bar_right = tk.Frame(top_right_header, bg="white")
        btn_bar_right.pack(side=tk.RIGHT)
        ttk.Button(btn_bar_right, text="Shortcut +", command=self.add_shortcut).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_bar_right, text="Bearbeiten", command=self.edit_shortcut).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_bar_right, text="Löschen", command=self.delete_shortcut).pack(side=tk.LEFT, padx=2)

        # Tabelle (Treeview)
        columns = ("app", "name", "key", "tags", "desc")
        self.tree = ttk.Treeview(self.right_frame, columns=columns, show='headings', selectmode="browse")
        
        column_map = {"app": ("Programm", 120), "name": ("Bezeichnung", 180), "key": ("Shortcut", 120), 
                      "tags": ("Tags", 150), "desc": ("Information", 300)}
        
        for col, (name, width) in column_map.items():
            self.tree.heading(col, text=name.upper())
            self.tree.column(col, width=width, anchor=tk.W)

        # Zebra-Streifen Tag
        self.tree.tag_configure('oddrow', background='#f9f9f9')
        self.tree.tag_configure('evenrow', background='white')

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<Double-1>', lambda e: self.edit_shortcut())

        self.refresh_app_list()
        self.refresh_shortcuts()
        self.refresh_history()

    def refresh_history(self):
        all_shortcuts = []
        for app, shortcuts in self.data.items():
            for s in shortcuts:
                if 'date' in s:
                    all_shortcuts.append((s['date'], app, s['name'], s['key']))
        
        # Sortiere nach echtem Datum
        all_shortcuts.sort(key=lambda x: datetime.strptime(x[0], "%d.%m.%Y"), reverse=True)
        top3 = all_shortcuts[:3]
        
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete("1.0", tk.END)
        
        if top3:
            for d, a, n, k in top3:
                self.history_text.insert(tk.END, f"[{a}] ", "gray")
                self.history_text.insert(tk.END, f"{k.upper()} ", "red_bold")
                self.history_text.insert(tk.END, f"({d})\n", "gray")
            self.history_text.tag_add("right", "1.0", tk.END)
        else:
            self.history_text.insert(tk.END, "Keine History verfügbar", "gray")
            self.history_text.tag_add("right", "1.0", tk.END)
            
        self.history_text.config(state=tk.DISABLED)

    # --- LOGIK METHODEN (Unverändert, nur optisch integriert) ---
    def refresh_app_list(self):
        current_selection = self.app_listbox.curselection()
        selected_app = self.app_listbox.get(current_selection[0]) if current_selection else None
        self.app_listbox.delete(0, tk.END)
        for app in sorted(self.data.keys()):
            self.app_listbox.insert(tk.END, f"  {app}") # Kleiner Einzug
            if f"  {app}" == selected_app or app == selected_app:
                self.app_listbox.select_set(self.app_listbox.size()-1)

    def on_app_select(self, event):
        selection = self.app_listbox.curselection()
        if selection:
            self.search_var.set("")
            app_name = self.app_listbox.get(selection[0]).strip()
            self.label_current_app.config(text=app_name)
            self.refresh_shortcuts(app_name)

    def add_app(self):
        new_app = simpledialog.askstring("App hinzufügen", "Name der App:")
        if new_app and new_app not in self.data:
            self.data[new_app] = []
            self.save_data()
            self.refresh_app_list()

    def rename_app(self):
        selection = self.app_listbox.curselection()
        if not selection: return
        old_name = self.app_listbox.get(selection[0]).strip()
        new_name = simpledialog.askstring("App umbenennen", f"Neuer Name für {old_name}:", initialvalue=old_name)
        if new_name and new_name != old_name:
            self.data[new_name] = self.data.pop(old_name)
            self.save_data()
            self.refresh_app_list()
            self.label_current_app.config(text=new_name)

    def delete_app(self):
        selection = self.app_listbox.curselection()
        if not selection: return
        app_name = self.app_listbox.get(selection[0]).strip()
        if messagebox.askyesno("Löschen", f"Soll '{app_name}' wirklich gelöscht werden?"):
            del self.data[app_name]
            self.save_data()
            self.refresh_app_list()
            self.refresh_shortcuts()
            self.refresh_history()

    def on_search_change(self, *args):
        query = self.search_var.get().lower()
        if query:
            self.app_listbox.selection_clear(0, tk.END)
            self.label_current_app.config(text=f"Suche: '{query}'")
            self.refresh_shortcuts(query=query)
        else:
            selection = self.app_listbox.curselection()
            if selection:
                app_name = self.app_listbox.get(selection[0]).strip()
                self.label_current_app.config(text=app_name)
                self.refresh_shortcuts(app_name)
            else:
                self.label_current_app.config(text="Alle Shortcuts")
                self.refresh_shortcuts()

    def refresh_shortcuts(self, app_name=None, query=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        count = 0
        def add_to_tree(app, s, count):
            tag = 'evenrow' if count % 2 == 0 else 'oddrow'
            self.tree.insert("", tk.END, values=(app, s['name'], s['key'], ", ".join(s.get('tags', [])), s.get('description', "")), tags=(tag,))
            return count + 1

        if query:
            for app, shortcuts in self.data.items():
                for s in shortcuts:
                    if (query in app.lower() or query in s['name'].lower() or query in s['key'].lower() or any(query in t.lower() for t in s.get('tags', []))):
                        count = add_to_tree(app, s, count)
        elif app_name:
            for s in self.data.get(app_name, []):
                count = add_to_tree(app_name, s, count)
        else:
            for app, shortcuts in self.data.items():
                for s in shortcuts:
                    count = add_to_tree(app, s, count)

    def shortcut_dialog(self, initial_data=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Shortcut Details")
        dialog.geometry("500x600")
        dialog.configure(bg="#f5f5f7")
        dialog.transient(self.root)
        dialog.grab_set()

        fields = {}
        entries = [("Bezeichnung:", "name"), ("Shortcut:", "key"), ("Tags:", "tags"), ("Information:", "description")]
        
        container = tk.Frame(dialog, bg="#f5f5f7", padx=20, pady=20)
        container.pack(fill=tk.BOTH, expand=True)

        for label, key in entries:
            tk.Label(container, text=label.upper(), font=("Segoe UI", 8, "bold"), bg="#f5f5f7", fg="#86868b").pack(anchor=tk.W, pady=(10, 0))
            if key == "key":
                self.key_var = tk.StringVar()
                if initial_data: self.key_var.set(initial_data.get("key", ""))
                entry = tk.Entry(container, textvariable=self.key_var, font=("Segoe UI", 11), relief=tk.FLAT, highlightthickness=1, highlightbackground="#d2d2d7")
                self.key_var.trace_add("write", lambda *args: self.check_duplicates(self.key_var.get(), duplicate_label))
            else:
                entry = tk.Entry(container, font=("Segoe UI", 11), relief=tk.FLAT, highlightthickness=1, highlightbackground="#d2d2d7")
                if initial_data:
                    val = initial_data.get(key, "")
                    if key == "tags": val = ", ".join(val)
                    entry.insert(0, val)
            entry.pack(fill=tk.X, pady=5)
            fields[key] = entry

        tk.Label(container, text="CONFLICT CHECK", font=("Segoe UI", 8, "bold"), bg="#f5f5f7", fg="#86868b").pack(anchor=tk.W, pady=(15, 0))
        duplicate_label = tk.Text(container, height=6, font=("Segoe UI", 9), bg="#ffffff", relief=tk.FLAT, highlightthickness=1, highlightbackground="#d2d2d7")
        duplicate_label.pack(fill=tk.X, pady=5)
        duplicate_label.config(state=tk.DISABLED)

        result = [None]
        def save():
            name, key = fields["name"].get(), self.key_var.get()
            if name and key:
                conflicts = []
                for app, shortcuts in self.data.items():
                    for s in shortcuts:
                        if initial_data and s['key'] == initial_data.get('key') and s['name'] == initial_data.get('name'): continue
                        if s['key'].strip().lower() == key.strip().lower(): conflicts.append(f"[{app}] {s['name']}")
                if conflicts and not messagebox.askyesno("Shortcut-Konflikt", "Bereits vergeben in:\n" + "\n".join(conflicts) + "\n\nTrotzdem speichern?"): return
                
                result[0] = {
                    "name": name, "key": key,
                    "tags": [t.strip() for t in fields["tags"].get().split(",") if t.strip()],
                    "description": fields["description"].get(),
                    "date": datetime.now().strftime("%d.%m.%Y")
                }
                dialog.destroy()
            else: messagebox.showerror("Fehler", "Pflichtfelder ausfüllen!")

        tk.Button(container, text="ÄNDERUNGEN SPEICHERN", command=save, bg="#007aff", fg="white", 
                  font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=20, pady=10).pack(pady=20, fill=tk.X)
        
        if initial_data: self.check_duplicates(initial_data.get("key", ""), duplicate_label)
        self.root.wait_window(dialog)
        return result[0]

    def check_duplicates(self, current_key, text_widget):
        text_widget.config(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        if len(current_key.strip()) < 2: 
            text_widget.config(state=tk.DISABLED); return
        matches = []
        search_key = current_key.lower()
        for app, shortcuts in self.data.items():
            for s in shortcuts:
                if search_key in s['key'].lower(): matches.append(f"[{app}] {s['name']} ({s['key']})")
        if matches: text_widget.insert(tk.END, "\n".join(matches))
        else: text_widget.insert(tk.END, "Keine Konflikte gefunden.")
        text_widget.config(state=tk.DISABLED)

    def add_shortcut(self):
        selection = self.app_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warnung", "App wählen!"); return
        app_name = self.app_listbox.get(selection[0]).strip()
        new_s = self.shortcut_dialog()
        if new_s:
            self.data[app_name].append(new_s)
            self.save_data()
            self.refresh_shortcuts(app_name)
            self.refresh_history()

    def edit_shortcut(self):
        tree_selection = self.tree.selection()
        if not tree_selection: return
        item_id = tree_selection[0]
        item_values = self.tree.item(item_id, 'values')
        app_name = item_values[0]
        shortcuts = self.data.get(app_name, [])
        idx = -1
        for i, s in enumerate(shortcuts):
            if s['name'] == item_values[1] and s['key'] == item_values[2]:
                idx = i; break
        if idx == -1: return
        new_data = self.shortcut_dialog(shortcuts[idx])
        if new_data:
            self.data[app_name][idx] = new_data
            self.save_data()
            if self.search_var.get(): self.on_search_change()
            else: self.refresh_shortcuts(app_name)
            self.refresh_history()

    def delete_shortcut(self):
        tree_selection = self.tree.selection()
        if not tree_selection: return
        item_id = tree_selection[0]
        item_values = self.tree.item(item_id, 'values')
        app_name = item_values[0]
        if messagebox.askyesno("Löschen", "Shortcut wirklich löschen?"):
            shortcuts = self.data.get(app_name, [])
            for i, s in enumerate(shortcuts):
                if s['name'] == item_values[1] and s['key'] == item_values[2]:
                    shortcuts.pop(i); break
            self.data[app_name] = shortcuts
            self.save_data()
            if self.search_var.get(): self.on_search_change()
            else: self.refresh_shortcuts(app_name)
            self.refresh_history()

if __name__ == "__main__":
    root = tk.Tk()
    app = ShortcutApp(root)
    root.mainloop()
