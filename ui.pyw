import sys
import subprocess
import threading
import os
import json
from tkinter import filedialog, messagebox, scrolledtext

# -------------------------------
# Step 1: Ensure required packages
# -------------------------------
def ensure_package(pkg_name, import_name=None):
    """Check if package is installed, otherwise install it."""
    try:
        __import__(import_name or pkg_name)
    except ImportError:
        print(f"{pkg_name} not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name])
        print(f"{pkg_name} installed!")

# Core UI
ensure_package("customtkinter")

# Google OAuth stack
ensure_package("pandas")
ensure_package("google-api-python-client", "googleapiclient.discovery")
ensure_package("google-auth-httplib2", "google_auth_httplib2")
ensure_package("google-auth-oauthlib", "google_auth_oauthlib")

# Now safe to import
import customtkinter as ctk
from csvlistmaker import import_csv_to_youtube

SETTINGS_FILE = "ui_settings.json"

# ------------------------------
# Main App
# ------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class YouTubeCSVImporter(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎵 YouTube Playlist CSV Importer 🎵")
        self.geometry("800x700")
        self.minsize(750, 650)

        # Variables
        self.client_secret_path_var = ctk.StringVar()
        self.csv_path_var = ctk.StringVar()

        # Layout grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(9, weight=1)  # log grows

        # Playlist ID
        self.label_playlist = ctk.CTkLabel(self, text="YouTube Playlist ID:", font=("Arial", 12))
        self.label_playlist.grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))

        self.entry_playlist = ctk.CTkEntry(self, width=600, font=("Arial", 12))
        self.entry_playlist.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        # Client Secret
        self.label_client = ctk.CTkLabel(self, text="Client Secret JSON:", font=("Arial", 12))
        self.label_client.grid(row=2, column=0, sticky="w", padx=20, pady=(5, 5))

        frame_client = ctk.CTkFrame(self)
        frame_client.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))
        frame_client.grid_columnconfigure(0, weight=1)

        self.entry_client = ctk.CTkEntry(frame_client, textvariable=self.client_secret_path_var, state="readonly")
        self.entry_client.grid(row=0, column=0, sticky="ew", padx=(5, 5), pady=5)

        self.btn_select_client = ctk.CTkButton(frame_client, text="Select Client Secret",
                                               fg_color="#1DB954", hover_color="#16a34a",
                                               command=self.select_client_secret)
        self.btn_select_client.grid(row=0, column=1, padx=(5, 5), pady=5)

        # CSV File
        self.label_csv = ctk.CTkLabel(self, text="CSV File:", font=("Arial", 12))
        self.label_csv.grid(row=4, column=0, sticky="w", padx=20, pady=(5, 5))

        frame_csv = ctk.CTkFrame(self)
        frame_csv.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 10))
        frame_csv.grid_columnconfigure(0, weight=1)

        self.entry_csv = ctk.CTkEntry(frame_csv, textvariable=self.csv_path_var, state="readonly")
        self.entry_csv.grid(row=0, column=0, sticky="ew", padx=(5, 5), pady=5)

        self.btn_select_csv = ctk.CTkButton(frame_csv, text="Select CSV File",
                                            fg_color="#1DB954", hover_color="#16a34a",
                                            command=self.select_csv_file)
        self.btn_select_csv.grid(row=0, column=1, padx=(5, 5), pady=5)

        # Buttons
        frame_buttons = ctk.CTkFrame(self)
        frame_buttons.grid(row=6, column=0, sticky="ew", padx=20, pady=(10, 5))
        frame_buttons.grid_columnconfigure((0, 1), weight=1)

        self.btn_install = ctk.CTkButton(frame_buttons, text="Install Dependencies",
                                         fg_color="#1DB954", hover_color="#16a34a",
                                         command=self.install_dependencies)
        self.btn_install.grid(row=0, column=0, padx=10, pady=5, sticky="ew")

        self.btn_start = ctk.CTkButton(frame_buttons, text="Start Import",
                                       fg_color="#1DB954", hover_color="#16a34a",
                                       command=self.start_import)
        self.btn_start.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # Progress Bar
        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=7, column=0, sticky="ew", padx=20, pady=(5, 5))
        self.progress.set(0)

        # Log
        self.label_log = ctk.CTkLabel(self, text="Log:", font=("Arial", 12))
        self.label_log.grid(row=8, column=0, sticky="w", padx=20, pady=(5, 5))

        self.log_output = scrolledtext.ScrolledText(self, width=90, height=20,
                                                    bg="#1e1e1e", fg="white")
        self.log_output.grid(row=9, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.log_output.configure(state="disabled")

        # Renk tagleri bir kez tanımlandı
        self.log_output.tag_configure("info", foreground="white")
        self.log_output.tag_configure("error", foreground="red")
        self.log_output.tag_configure("success", foreground="lime")

        # Load saved settings
        self.load_settings()

    # ------------------------------
    # Settings persistence
    # ------------------------------
    def save_settings(self):
        settings = {
            "playlist_id": self.entry_playlist.get().strip(),
            "client_secret": self.client_secret_path_var.get(),
            "csv_file": self.csv_path_var.get()
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f)

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                self.entry_playlist.insert(0, settings.get("playlist_id", ""))
                self.client_secret_path_var.set(settings.get("client_secret", ""))
                self.csv_path_var.set(settings.get("csv_file", ""))
            except:
                pass

    # ------------------------------
    # File selection
    # ------------------------------
    def select_client_secret(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            self.client_secret_path_var.set(path)
            self.save_settings()

    def select_csv_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            self.csv_path_var.set(path)
            self.save_settings()

    # ------------------------------
    # Logging
    # ------------------------------
    def log(self, message, error=False):
        self.log_output.configure(state="normal")
        if error:
            self.log_output.insert("end", message + "\n", "error")
        elif "success" in message.lower():
            self.log_output.insert("end", message + "\n", "success")
        else:
            self.log_output.insert("end", message + "\n", "info")
        self.log_output.see("end")
        self.log_output.configure(state="disabled")

    # ------------------------------
    # Dependency installation (manual)
    # ------------------------------
    def install_dependencies(self):
        def run_pip():
            try:
                self.log("Installing dependencies...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade",
                                       "google-api-python-client",
                                       "google-auth-httplib2",
                                       "google-auth-oauthlib",
                                       "pandas",
                                       "customtkinter"])
                self.log("Dependencies installed successfully!")
            except Exception as e:
                self.log(f"Error installing dependencies: {e}", error=True)
        threading.Thread(target=run_pip).start()

    # ------------------------------
    # Start import
    # ------------------------------
    def start_import(self):
        playlist_id = self.entry_playlist.get().strip()
        client_secret = self.client_secret_path_var.get()
        csv_file = self.csv_path_var.get()

        if not playlist_id or not client_secret or not csv_file:
            messagebox.showerror("Error", "All fields are required!")
            return

        self.save_settings()

        def run_import():
            try:
                self.progress.set(0)
                self.log("Starting import...")
                import_csv_to_youtube(
                    playlist_id=playlist_id,
                    csv_file=csv_file,
                    client_secret_path=client_secret,
                    gui=self
                )
                self.progress.set(1)
                self.log("Import finished successfully!")
            except Exception as e:
                self.log(f"Error: {e}", error=True)
        threading.Thread(target=run_import).start()


# ------------------------------
# Run app
# ------------------------------
if __name__ == "__main__":
    app = YouTubeCSVImporter()
    app.mainloop()
