import os
import shutil
import json
import time
import locale
import tkinter as tk
from tkinter import filedialog, messagebox
import threading

lang = 'en'
try:
    locale.setlocale(locale.LC_ALL, '')
    current_locale_info = locale.getlocale()
    if current_locale_info and current_locale_info[0]:
        if current_locale_info[0].startswith('it'):
            lang = 'it'
        elif current_locale_info[0].startswith('en'):
            lang = 'en'
    
    if lang == 'en':
        try:
            locale.setlocale(locale.LC_ALL, 'Italian_Italy.1252')
            lang = 'it'
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')
                lang = 'it'
            except locale.Error:
                pass
except Exception as e:
    print(f"Errore durante il rilevamento del locale: {e}")
    pass

TRANSLATIONS = {
    'it': {
        "window_title": "Smart File Organizer",
        "folder_label": "Cartella da Organizzare:",
        "browse_button": "Sfoglia...",
        "start_button": "Avvia Organizzazione",
        "stop_button": "Ferma Organizzazione",
        "rules_button": "Gestisci Regole",
        "status_waiting": "Stato: In attesa. Seleziona una cartella e avvia.",
        "status_running": "Servizio avviato. Monitoraggio in corso...",
        "status_stopped": "Servizio fermato. Seleziona una cartella e avvia.",
        "status_moved": "Spostato: {filename} -> {folder}/",
        "status_error": "Errore: {error}",
        "warn_title": "Attenzione",
        "warn_no_folder": "Per favore, seleziona prima una cartella da organizzare.",
        "rules_window_title": "Gestione Regole Personalizzate",
        "rules_list_label": "Regole Esistenti:",
        "rules_new_label": "Nuova Regola:",
        "rules_keyword_label": "Se contiene:",
        "rules_folder_label": "Sposta in:",
        "rules_add_button": "Aggiungi Regola",
        "rules_remove_button": "Rimuovi Selezionata",
        "rules_added_success": "Regola aggiunta con successo!",
        "rules_removed_success": "Regola rimossa con successo!",
        "rules_input_error": "Per favore, inserisci sia una parola chiave che una cartella.",
        "rules_no_selection_error": "Nessuna regola selezionata da rimuovere.",
        "rules_remove_confirm_title": "Conferma Eliminazione",
        "rules_remove_confirm_message": "Sei sicuro di voler eliminare le regole selezionate?",
        "rules_save_button": "Salva Modifiche",
        "extension_folder_name": "File {ext}",
        "other_folder_name": "Altro",
        "quit_title": "Esci",
        "quit_message": "Il servizio di organizzazione è attivo. Vuoi fermarlo e uscire?"
    },
    'en': {
        "window_title": "Smart File Organizer",
        "folder_label": "Folder to Organize:",
        "browse_button": "Browse...",
        "start_button": "Start Organizing",
        "stop_button": "Stop Organizing",
        "rules_button": "Manage Rules",
        "status_waiting": "Status: Waiting. Select a folder and start.",
        "status_running": "Service started. Monitoring in progress...",
        "status_stopped": "Status: Stopped. Select a folder and start.",
        "status_moved": "Moved: {filename} -> {folder}/",
        "status_error": "Error: {error}",
        "warn_title": "Warning",
        "warn_no_folder": "Please select a folder to organize first.",
        "rules_window_title": "Custom Rules Management",
        "rules_list_label": "Existing Rules:",
        "rules_new_label": "New Rule:",
        "rules_keyword_label": "If contains:",
        "rules_folder_label": "Move to:",
        "rules_add_button": "Add Rule",
        "rules_remove_button": "Remove Selected",
        "rules_added_success": "Rule added successfully!",
        "rules_removed_success": "Rule removed successfully!",
        "rules_input_error": "Please enter both a keyword and a folder.",
        "rules_no_selection_error": "No rule selected to remove.",
        "rules_remove_confirm_title": "Confirm Deletion",
        "rules_remove_confirm_message": "Are you sure you want to delete the selected rules?",
        "rules_save_button": "Save Changes",
        "extension_folder_name": "{ext} Files",
        "other_folder_name": "Other",
        "quit_title": "Quit",
        "quit_message": "The organizing service is running. Do you want to stop it and exit?"
    }
}

if lang not in TRANSLATIONS:
    lang = 'en'

T = TRANSLATIONS[lang]

RULES_FILE = 'rules.json'
CUSTOM_RULES = []

DEFAULT_RULES = [
    {'keyword': 'fattura', 'folder': 'Documenti/Fatture'},
    {'keyword': 'screenshot', 'folder': 'Immagini/Screenshots'}
]

class SmartOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(T["window_title"])
        self.root.geometry("500x350")
        if os.path.exists("icon.ico"):
            self.root.iconbitmap("icon.ico") 

        self.source_dir = tk.StringVar()
        self.is_running = False
        self.worker_thread = None
        self.editing_index = None

        self._load_rules()
        
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        dir_frame = tk.Frame(main_frame)
        dir_frame.pack(fill=tk.X, pady=10)
        
        dir_label = tk.Label(dir_frame, text=T["folder_label"])
        dir_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.dir_entry = tk.Entry(dir_frame, textvariable=self.source_dir, state='readonly', width=40)
        self.dir_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.browse_button = tk.Button(dir_frame, text=T["browse_button"], command=self.browse_folder)
        self.browse_button.pack(side=tk.LEFT, padx=(5, 0))

        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=20)

        self.start_button = tk.Button(button_frame, text=T["start_button"], command=self.start_organizing, bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"))
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = tk.Button(button_frame, text=T["stop_button"], command=self.stop_organizing, state=tk.DISABLED, bg="#f44336", fg="white", font=("Helvetica", 10, "bold"))
        self.stop_button.pack(side=tk.LEFT, padx=10)

        self.rules_button = tk.Button(main_frame, text=T["rules_button"], command=self.open_rules_window)
        self.rules_button.pack(pady=5)

        self.status_label = tk.Label(main_frame, text=T["status_waiting"], wraplength=480)
        self.status_label.pack(pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.source_dir.set(folder_selected)

    def open_rules_window(self):
        if hasattr(self, 'rules_window') and self.rules_window.winfo_exists():
            self.rules_window.lift()
            return

        rules_window = tk.Toplevel(self.root)
        rules_window.title(T["rules_window_title"])
        rules_window.geometry("600x400")
        rules_window.resizable(False, False)
        rules_window.transient(self.root)

        self.rules_window = rules_window

        list_frame = tk.Frame(rules_window, padx=10, pady=10)
        list_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(list_frame, text=T["rules_list_label"]).pack(anchor='w')

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.rules_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.rules_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.rules_listbox.yview)

        self.rules_listbox.bind('<<ListboxSelect>>', self._on_rule_select)
        self.rules_listbox.bind('<Double-1>', self._on_rule_double_click)

        self._update_rules_listbox()

        add_frame = tk.Frame(rules_window, padx=10, pady=10)
        add_frame.pack(fill=tk.X)

        tk.Label(add_frame, text=T["rules_new_label"]).grid(row=0, column=0, columnspan=4, sticky='w', pady=(0, 5))

        tk.Label(add_frame, text=T["rules_keyword_label"]).grid(row=1, column=0, sticky='w')
        self.keyword_entry = tk.Entry(add_frame, width=20)
        self.keyword_entry.grid(row=1, column=1, padx=5)
 
        tk.Label(add_frame, text=T["rules_folder_label"]).grid(row=1, column=2, sticky='w', padx=(10, 0))
        self.folder_entry = tk.Entry(add_frame, width=30)
        self.folder_entry.grid(row=1, column=3, padx=5)
 
        self.rule_browse_button = tk.Button(add_frame, text=T["browse_button"], command=self._browse_rule_folder)
        self.rule_browse_button.grid(row=1, column=4, padx=(5, 0))
 
        action_frame = tk.Frame(rules_window, padx=10, pady=10)
        action_frame.pack(fill=tk.X)

        self.add_save_button = tk.Button(action_frame, text=T["rules_add_button"], command=self._add_or_save_rule_action)
        self.add_save_button.pack(side=tk.RIGHT, padx=(10, 0))

        self.remove_rule_button = tk.Button(action_frame, text=T["rules_remove_button"], command=self._remove_rule_action, state=tk.DISABLED)
        self.remove_rule_button.pack(side=tk.RIGHT)

    def _browse_rule_folder(self):
        folder_selected = filedialog.askdirectory(parent=self.rules_window)
        if folder_selected:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_selected)

    def _on_rule_double_click(self, event):
        selected_indices = self.rules_listbox.curselection()
        if selected_indices:
            index = selected_indices[0]
            rule_to_edit = CUSTOM_RULES[index]

            self.keyword_entry.delete(0, tk.END)
            self.keyword_entry.insert(0, rule_to_edit['keyword'])

            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, rule_to_edit['folder'])

            self.editing_index = index
            self.add_save_button.config(text=T["rules_save_button"])
            self.rules_listbox.selection_clear(0, tk.END)
            self._on_rule_select()

    def _on_rule_select(self, event=None):
        if self.editing_index is not None:
            return

        if self.rules_listbox.curselection():
            self.remove_rule_button.config(state=tk.NORMAL)
        else:
            self.remove_rule_button.config(state=tk.DISABLED)

    def _load_rules(self):
        global CUSTOM_RULES
        try:
            if os.path.exists(RULES_FILE):
                with open(RULES_FILE, 'r', encoding='utf-8') as f:
                    CUSTOM_RULES = json.load(f)
            else:
                CUSTOM_RULES = DEFAULT_RULES
                self._save_rules()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Errore durante il caricamento delle regole: {e}. Verranno usate le regole di default.")
            CUSTOM_RULES = DEFAULT_RULES

    def _save_rules(self):
        try:
            with open(RULES_FILE, 'w', encoding='utf-8') as f:
                json.dump(CUSTOM_RULES, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Errore durante il salvataggio delle regole: {e}")
            messagebox.showerror(T["warn_title"], f"Errore durante il salvataggio delle regole: {e}", parent=self.rules_window if hasattr(self, 'rules_window') and self.rules_window.winfo_exists() else self.root)

    def _update_rules_listbox(self):
        self.rules_listbox.delete(0, tk.END)
        for rule in CUSTOM_RULES:
            self.rules_listbox.insert(tk.END, f"Se contiene '{rule['keyword']}' -> sposta in '{rule['folder']}'")

    def _add_or_save_rule_action(self):
        keyword = self.keyword_entry.get().strip()
        folder = self.folder_entry.get().strip()

        if not keyword or not folder:
            messagebox.showerror(T["warn_title"], T["rules_input_error"], parent=self.rules_window)
            return

        if self.editing_index is not None:
            CUSTOM_RULES[self.editing_index] = {'keyword': keyword, 'folder': folder}
            self.editing_index = None
            self.add_save_button.config(text=T["rules_add_button"])
        else:
            CUSTOM_RULES.append({'keyword': keyword, 'folder': folder})

        self._update_rules_listbox()
        self.keyword_entry.delete(0, tk.END)
        self.folder_entry.delete(0, tk.END)
        self._save_rules()

        if self.editing_index is None:
             messagebox.showinfo(T["rules_window_title"], T["rules_added_success"], parent=self.rules_window)

    def _remove_rule_action(self):
        selected_indices = self.rules_listbox.curselection()
        if selected_indices:
            confirm = messagebox.askyesno(
                title=T["rules_remove_confirm_title"],
                message=T["rules_remove_confirm_message"],
                parent=self.rules_window
            )

            if confirm:
                for index in reversed(selected_indices):
                    del CUSTOM_RULES[index]
                self._update_rules_listbox()
                self._on_rule_select() 
                self._save_rules()
        else:
            messagebox.showerror(T["warn_title"], T["rules_no_selection_error"], parent=self.rules_window)

    def start_organizing(self):
        if not self.source_dir.get():
            messagebox.showwarning(T["warn_title"], T["warn_no_folder"])
            return

        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.browse_button.config(state=tk.DISABLED)
        self.update_status(T["status_running"])

        self.worker_thread = threading.Thread(target=self.organize_worker, daemon=True)
        self.worker_thread.start()

    def stop_organizing(self):
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.browse_button.config(state=tk.NORMAL)
        self.update_status(T["status_stopped"])

    def organize_worker(self):
        source_path = self.source_dir.get()
        while self.is_running:
            try:
                for filename in os.listdir(source_path):
                    file_path = os.path.join(source_path, filename)
                    
                    if os.path.isdir(file_path) or filename.startswith('.'):
                        continue

                    moved = False
                    
                    for rule in CUSTOM_RULES:
                        if rule['keyword'].lower() in filename.lower():
                            if os.path.isabs(rule['folder']):
                                dest_folder = rule['folder']
                            else:
                                dest_folder = os.path.join(source_path, rule['folder'])
                            os.makedirs(dest_folder, exist_ok=True)
                            
                            shutil.move(file_path, os.path.join(dest_folder, filename))
                            self.update_status(T["status_moved"].format(filename=filename, folder=rule['folder']))
                            moved = True
                            break

                    if not moved:
                        _, file_extension = os.path.splitext(filename)

                        if file_extension:
                            ext_name = file_extension[1:].upper()
                            folder_name = T["extension_folder_name"].format(ext=ext_name)
                            dest_folder = os.path.join(source_path, folder_name)
                            os.makedirs(dest_folder, exist_ok=True)
                            shutil.move(file_path, os.path.join(dest_folder, filename))
                            self.update_status(T["status_moved"].format(filename=filename, folder=folder_name))
                        else:
                            dest_folder = os.path.join(source_path, T["other_folder_name"])
                            os.makedirs(dest_folder, exist_ok=True)
                            shutil.move(file_path, os.path.join(dest_folder, filename))
                            self.update_status(T["status_moved"].format(filename=filename, folder=T["other_folder_name"]))

            except Exception as e:
                self.update_status(T["status_error"].format(error=e))

            time.sleep(10)

    def update_status(self, message):
        self.root.after(0, lambda: self.status_label.config(text=message))

    def on_closing(self):
        if self.is_running:
            if messagebox.askokcancel(T["quit_title"], T["quit_message"]):
                self.stop_organizing()
                self.root.destroy()
        else:
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartOrganizerApp(root)
    root.mainloop()



