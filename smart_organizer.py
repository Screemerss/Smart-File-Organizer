import os
import shutil
import time
import locale
import tkinter as tk
from tkinter import filedialog, messagebox
import threading

# --- INTERNAZIONALIZZAZIONE (i18n) ---
# 1. Imposta la lingua in base alle impostazioni predefinite dell'utente e rilevala
try:
    locale.setlocale(locale.LC_ALL, '')
    lang = locale.getlocale()[0][:2]
except (IndexError, TypeError):
    lang = 'en' # Imposta l'inglese come lingua di default se non riesce a rilevarla o impostarla

# 2. Dizionario delle traduzioni
TRANSLATIONS = {
    'it': {
        "window_title": "Smart File Organizer",
        "folder_label": "Cartella da Organizzare:",
        "browse_button": "Sfoglia...",
        "start_button": "Avvia Organizzazione",
        "stop_button": "Ferma Organizzazione",
        "status_waiting": "Stato: In attesa. Seleziona una cartella e avvia.",
        "status_running": "Servizio avviato. Monitoraggio in corso...",
        "status_stopped": "Servizio fermato. Seleziona una cartella e avvia.",
        "status_moved": "Spostato: {filename} -> {folder}/",
        "status_error": "Errore: {error}",
        "warn_title": "Attenzione",
        "warn_no_folder": "Per favore, seleziona prima una cartella da organizzare.",
        "quit_title": "Esci",
        "quit_message": "Il servizio di organizzazione è attivo. Vuoi fermarlo e uscire?"
    },
    'en': {
        "window_title": "Smart File Organizer",
        "folder_label": "Folder to Organize:",
        "browse_button": "Browse...",
        "start_button": "Start Organizing",
        "stop_button": "Stop Organizing",
        "status_waiting": "Status: Waiting. Select a folder and start.",
        "status_running": "Service started. Monitoring in progress...",
        "status_stopped": "Service stopped. Select a folder and start.",
        "status_moved": "Moved: {filename} -> {folder}/",
        "status_error": "Error: {error}",
        "warn_title": "Warning",
        "warn_no_folder": "Please select a folder to organize first.",
        "quit_title": "Quit",
        "quit_message": "The organizing service is running. Do you want to stop it and exit?"
    }
}

# 3. Se la lingua rilevata non è disponibile, usa l'inglese
if lang not in TRANSLATIONS:
    lang = 'en'

T = TRANSLATIONS[lang] # T sarà il nostro dizionario di traduzione da usare

# --- REGOLE PERSONALIZZATE (Esempio) ---
# In futuro, l'utente potrà definire queste regole dall'interfaccia.
# Formato: {'keyword': 'testo_da_cercare', 'folder': 'Cartella_Destinazione'}
CUSTOM_RULES = [
    {'keyword': 'fattura', 'folder': 'Documenti/Fatture'},
    {'keyword': 'screenshot', 'folder': 'Immagini/Screenshots'},
]

# Dizionario che mappa le estensioni dei file alle cartelle di destinazione
# Puoi personalizzarlo e ampliarlo facilmente!
FILE_TYPES = {
    "Immagini": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
    "Documenti": [".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx"],
    "Archivi": [".zip", ".rar", ".7z", ".tar.gz"],
    "Audio": [".mp3", ".wav", ".aac"],
    "Video": [".mp4", ".mov", ".avi", ".mkv"],
    "Eseguibili": [".exe", ".msi"],
}

class SmartOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(T["window_title"])
        self.root.geometry("500x350")
        self.root.iconbitmap("icon.ico") # Riattiviamo l'icona della finestra

        self.source_dir = tk.StringVar()
        self.is_running = False
        self.worker_thread = None

        # --- Interfaccia Grafica ---
        
        # Frame principale
        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Selezione cartella
        dir_frame = tk.Frame(main_frame)
        dir_frame.pack(fill=tk.X, pady=10)
        
        dir_label = tk.Label(dir_frame, text=T["folder_label"])
        dir_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.dir_entry = tk.Entry(dir_frame, textvariable=self.source_dir, state='readonly', width=40)
        self.dir_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.browse_button = tk.Button(dir_frame, text=T["browse_button"], command=self.browse_folder)
        self.browse_button.pack(side=tk.LEFT, padx=(5, 0))

        # Pulsanti di controllo
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=20)

        self.start_button = tk.Button(button_frame, text=T["start_button"], command=self.start_organizing, bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"))
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = tk.Button(button_frame, text=T["stop_button"], command=self.stop_organizing, state=tk.DISABLED, bg="#f44336", fg="white", font=("Helvetica", 10, "bold"))
        self.stop_button.pack(side=tk.LEFT, padx=10)

        # Log di stato
        self.status_label = tk.Label(main_frame, text=T["status_waiting"], wraplength=480)
        self.status_label.pack(pady=10)

        # Gestione chiusura finestra
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def browse_folder(self):
        """Apre una finestra di dialogo per selezionare la cartella da monitorare."""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.source_dir.set(folder_selected)
            self.update_status(f"Cartella selezionata: {folder_selected}")

    def start_organizing(self):
        """Avvia il processo di monitoraggio in un thread separato."""
        if not self.source_dir.get():
            messagebox.showwarning(T["warn_title"], T["warn_no_folder"])
            return

        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.browse_button.config(state=tk.DISABLED)
        self.update_status(T["status_running"])

        # Usiamo un thread per non bloccare l'interfaccia grafica
        self.worker_thread = threading.Thread(target=self.organize_worker, daemon=True)
        self.worker_thread.start()

    def stop_organizing(self):
        """Ferma il processo di monitoraggio."""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.browse_button.config(state=tk.NORMAL)
        self.update_status(T["status_stopped"])

    def organize_worker(self):
        """Il worker che esegue la logica di organizzazione in background."""
        source_path = self.source_dir.get()
        while self.is_running:
            try:
                for filename in os.listdir(source_path):
                    file_path = os.path.join(source_path, filename)
                    
                    # Ignora le cartelle e i file nascosti
                    if os.path.isdir(file_path) or filename.startswith('.'):
                        continue

                    moved = False
                    
                    # --- 1. CONTROLLA LE REGOLE PERSONALIZZATE (HANNO LA PRIORITÀ) ---
                    for rule in CUSTOM_RULES:
                        if rule['keyword'].lower() in filename.lower():
                            dest_folder = os.path.join(source_path, rule['folder'])
                            os.makedirs(dest_folder, exist_ok=True)
                            
                            shutil.move(file_path, os.path.join(dest_folder, filename))
                            self.update_status(T["status_moved"].format(filename=filename, folder=rule['folder']))
                            moved = True
                            break # Trovata una regola, passa al file successivo

                    # --- 2. SE NESSUNA REGOLA CORRISPONDE, USA L'ORGANIZZAZIONE STANDARD PER ESTENSIONE ---
                    if not moved:
                        for folder_name, extensions in FILE_TYPES.items():
                            if any(filename.lower().endswith(ext) for ext in extensions):
                                dest_folder = os.path.join(source_path, folder_name)
                                os.makedirs(dest_folder, exist_ok=True)
                                
                                shutil.move(file_path, os.path.join(dest_folder, filename))
                                self.update_status(T["status_moved"].format(filename=filename, folder=folder_name))
                                moved = True
                                break
                        
                        # Se non trova una corrispondenza, lo sposta in 'Altro'
                        if not moved:
                            dest_folder = os.path.join(source_path, "Altro")
                            os.makedirs(dest_folder, exist_ok=True)
                            shutil.move(file_path, os.path.join(dest_folder, filename))
                            self.update_status(T["status_moved"].format(filename=filename, folder="Altro"))

            except Exception as e:
                self.update_status(T["status_error"].format(error=e))

            # Attendi 10 secondi prima del prossimo controllo
            time.sleep(10)

    def update_status(self, message):
        """Aggiorna l'etichetta di stato in modo sicuro per i thread."""
        self.root.after(0, lambda: self.status_label.config(text=message))

    def on_closing(self):
        """Gestisce la chiusura dell'applicazione."""
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

