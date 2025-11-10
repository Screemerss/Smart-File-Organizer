import os
import shutil
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import threading

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
        self.root.title("Smart File Organizer")
        self.root.geometry("500x350")

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
        
        dir_label = tk.Label(dir_frame, text="Cartella da Organizzare:")
        dir_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.dir_entry = tk.Entry(dir_frame, textvariable=self.source_dir, state='readonly', width=40)
        self.dir_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.browse_button = tk.Button(dir_frame, text="Sfoglia...", command=self.browse_folder)
        self.browse_button.pack(side=tk.LEFT, padx=(5, 0))

        # Pulsanti di controllo
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=20)

        self.start_button = tk.Button(button_frame, text="Avvia Organizzazione", command=self.start_organizing, bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"))
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.stop_button = tk.Button(button_frame, text="Ferma Organizzazione", command=self.stop_organizing, state=tk.DISABLED, bg="#f44336", fg="white", font=("Helvetica", 10, "bold"))
        self.stop_button.pack(side=tk.LEFT, padx=10)

        # Log di stato
        self.status_label = tk.Label(main_frame, text="Stato: In attesa. Seleziona una cartella e avvia.", wraplength=480)
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
            messagebox.showwarning("Attenzione", "Per favore, seleziona prima una cartella da organizzare.")
            return

        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.browse_button.config(state=tk.DISABLED)
        self.update_status("Servizio avviato. Monitoraggio in corso...")

        # Usiamo un thread per non bloccare l'interfaccia grafica
        self.worker_thread = threading.Thread(target=self.organize_worker, daemon=True)
        self.worker_thread.start()

    def stop_organizing(self):
        """Ferma il processo di monitoraggio."""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.browse_button.config(state=tk.NORMAL)
        self.update_status("Servizio fermato. Seleziona una cartella e avvia.")

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

                    # Trova la cartella di destinazione
                    moved = False
                    for folder_name, extensions in FILE_TYPES.items():
                        if any(filename.lower().endswith(ext) for ext in extensions):
                            dest_folder = os.path.join(source_path, folder_name)
                            os.makedirs(dest_folder, exist_ok=True) # Crea la cartella se non esiste
                            
                            shutil.move(file_path, os.path.join(dest_folder, filename))
                            self.update_status(f"Spostato: {filename} -> {folder_name}/")
                            moved = True
                            break
                    
                    # Se non trova una corrispondenza, lo sposta in 'Altro'
                    if not moved:
                        dest_folder = os.path.join(source_path, "Altro")
                        os.makedirs(dest_folder, exist_ok=True)
                        shutil.move(file_path, os.path.join(dest_folder, filename))
                        self.update_status(f"Spostato: {filename} -> Altro/")

            except Exception as e:
                self.update_status(f"Errore: {e}")

            # Attendi 10 secondi prima del prossimo controllo
            time.sleep(10)

    def update_status(self, message):
        """Aggiorna l'etichetta di stato in modo sicuro per i thread."""
        self.root.after(0, lambda: self.status_label.config(text=message))

    def on_closing(self):
        """Gestisce la chiusura dell'applicazione."""
        if self.is_running:
            if messagebox.askokcancel("Esci", "Il servizio di organizzazione è attivo. Vuoi fermarlo e uscire?"):
                self.stop_organizing()
                self.root.destroy()
        else:
            self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartOrganizerApp(root)
    root.mainloop()
