import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk

import paramiko

import nas_control

STATUS_REFRESH_MS = 5000

if getattr(sys, "frozen", False):
    ICON_PATH = Path(sys._MEIPASS) / "icon.ico"
else:
    ICON_PATH = Path(__file__).parent / "icon.ico"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.resizable(False, False)

        self.config_data = nas_control.load_config()
        self.title(f"{self.config_data['nas_name']} - Contrôle à distance")
        try:
            self.iconbitmap(ICON_PATH)
        except tk.TclError:
            # Le format .ico n'est pas supporté par Tk sous Linux/macOS.
            pass

        pad = {"padx": 10, "pady": 6}
        row = 0

        # --- Statut ---
        status_frame = ttk.Frame(self)
        status_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 10))
        self.status_dot = tk.Label(status_frame, text="●", fg="#999", font=("Segoe UI", 24))
        self.status_dot.pack(side="left")
        self.online_var = tk.StringVar(value="Vérification...")
        ttk.Label(status_frame, textvariable=self.online_var, font=("Segoe UI", 14, "bold")).pack(
            side="left", padx=(8, 0)
        )
        row += 1

        self.on_button = ttk.Button(self, text="Allumer le NAS", command=self.on_wake)
        self.on_button.grid(row=row, column=0, columnspan=2, sticky="ew", **pad)
        row += 1

        ttk.Separator(self, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", padx=10)
        row += 1

        # --- Configuration ---
        ttk.Label(self, text="Configuration", font=("Segoe UI", 9, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", **pad
        )
        row += 1

        self.name_var = tk.StringVar(value=self.config_data["nas_name"])
        self.ip_var = tk.StringVar(value=self.config_data["nas_ip"])
        self.mac_var = tk.StringVar(value=self.config_data["nas_mac"])
        self.port_var = tk.StringVar(value=str(self.config_data["ssh_port"]))
        self.user_var = tk.StringVar(value=self.config_data["ssh_user"])

        for label, var in (
            ("Nom du NAS :", self.name_var),
            ("Adresse IP :", self.ip_var),
            ("Adresse MAC :", self.mac_var),
            ("Port SSH :", self.port_var),
            ("Utilisateur SSH :", self.user_var),
        ):
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", **pad)
            ttk.Entry(self, textvariable=var, width=25).grid(row=row, column=1, sticky="ew", **pad)
            row += 1

        self.save_button = ttk.Button(self, text="Enregistrer la configuration", command=self.on_save_config)
        self.save_button.grid(row=row, column=0, columnspan=2, sticky="ew", **pad)
        row += 1

        ttk.Separator(self, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", padx=10)
        row += 1

        # --- Extinction ---
        ttk.Label(self, text="Mot de passe SSH :").grid(row=row, column=0, sticky="w", **pad)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(self, textvariable=self.password_var, show="•", width=25)
        self.password_entry.grid(row=row, column=1, sticky="ew", **pad)
        self.password_entry.bind("<Return>", lambda _event: self.on_shutdown())
        row += 1

        self.off_button = ttk.Button(self, text="Éteindre le NAS", command=self.on_shutdown)
        self.off_button.grid(row=row, column=0, columnspan=2, sticky="ew", **pad)
        row += 1

        self.status_var = tk.StringVar(value="Prêt.")
        ttk.Label(self, textvariable=self.status_var, foreground="#555").grid(
            row=row, column=0, columnspan=2, sticky="w", **pad
        )
        row += 1

        ttk.Separator(self, orient="horizontal").grid(row=row, column=0, columnspan=2, sticky="ew", padx=10)
        row += 1

        # --- Rapport ---
        ttk.Label(self, text="Rapport :").grid(row=row, column=0, sticky="w", **pad)
        row += 1

        report_frame = ttk.Frame(self)
        report_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))
        row += 1

        self.report_text = tk.Text(report_frame, height=10, width=48, wrap="word", state="disabled")
        self.report_text.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(report_frame, orient="vertical", command=self.report_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.report_text.config(yscrollcommand=scrollbar.set)

        self.copy_button = ttk.Button(self, text="Copier le rapport", command=self.copy_report)
        self.copy_button.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))

        self.log("Prêt.")
        self.refresh_status()

    # --- Rapport / statut texte ---
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.report_text.config(state="normal")
        self.report_text.insert("end", f"[{timestamp}] {message}\n")
        self.report_text.see("end")
        self.report_text.config(state="disabled")

    def copy_report(self):
        content = self.report_text.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(content)
        self.set_status("Rapport copié dans le presse-papiers.")

    def set_status(self, text):
        self.status_var.set(text)
        self.log(text)

    def set_buttons_state(self, state):
        self.on_button.config(state=state)
        self.off_button.config(state=state)

    # --- Statut en ligne / hors ligne ---
    def refresh_status(self):
        config = self.config_data

        def task():
            online = nas_control.is_online(config)
            self.after(0, lambda: self.apply_status(online))

        threading.Thread(target=task, daemon=True).start()
        self.after(STATUS_REFRESH_MS, self.refresh_status)

    def apply_status(self, online):
        name = self.config_data["nas_name"]
        if online:
            self.status_dot.config(fg="#2e7d32")
            self.online_var.set(f"{name} en ligne")
        else:
            self.status_dot.config(fg="#c62828")
            self.online_var.set(f"{name} hors ligne")

    # --- Configuration ---
    def on_save_config(self):
        port_text = self.port_var.get().strip()
        if not port_text.isdigit():
            self.set_status("Le port SSH doit être un nombre.")
            return

        self.config_data = {
            "nas_name": self.name_var.get().strip() or "NAS",
            "nas_ip": self.ip_var.get().strip(),
            "nas_mac": self.mac_var.get().strip(),
            "ssh_port": int(port_text),
            "ssh_user": self.user_var.get().strip(),
        }
        nas_control.save_config(self.config_data)
        self.title(f"{self.config_data['nas_name']} - Contrôle à distance")
        self.set_status("Configuration enregistrée.")
        self.status_dot.config(fg="#999")
        self.online_var.set("Vérification...")

    # --- Actions ---
    def on_wake(self):
        config = self.config_data
        self.set_buttons_state("disabled")
        self.set_status("Envoi du paquet Wake-on-LAN...")

        def task():
            try:
                nas_control.wake(config)
                message = f"Paquet magique envoyé à {config['nas_mac']}."
            except Exception as exc:
                message = f"Erreur : {exc}"
            self.after(0, lambda: (self.set_status(message), self.set_buttons_state("normal")))

        threading.Thread(target=task, daemon=True).start()

    def on_shutdown(self):
        config = self.config_data
        password = self.password_var.get()
        if not password:
            self.set_status("Entre le mot de passe SSH avant d'éteindre le NAS.")
            return

        self.set_buttons_state("disabled")
        self.set_status("Connexion SSH et extinction en cours...")

        def task():
            try:
                nas_control.shutdown(config, password)
                message = "Commande d'extinction envoyée avec succès."
            except paramiko.AuthenticationException:
                message = "Échec d'authentification SSH. Vérifie le mot de passe."
            except Exception as exc:
                message = f"Erreur : {exc}"
            self.after(0, lambda: (self.set_status(message), self.set_buttons_state("normal")))
            self.after(0, lambda: self.password_var.set(""))

        threading.Thread(target=task, daemon=True).start()


if __name__ == "__main__":
    App().mainloop()
