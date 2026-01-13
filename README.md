# 🕵️ Python Keylogger & RAT Builder (Educational)

A powerful, standalone Keylogger and Remote Access Tool (RAT) generator written in Python. This tool allows you to create a fully functional, executable payload that sends keystrokes and logs to a Telegram Bot.

> [!WARNING]
> **Disclaimer**: This tool is for **EDUCATIONAL PURPOSES ONLY**. I am not responsible for any misuse of this software. Do not use this on any computer without explicit permission.

## ✨ Features

- **⌨️ Keylogging**: Captures all keystrokes including special keys.
- **🤖 Telegram Integration**: Sends logs directly to your Telegram Bot.
- **📧 Email Reporting**: (Optional) Supports Gmail SMTP for email logs.
- **🏗️ Standalone Builder**: Includes a GUI Builder to generate unique `.exe` payloads for each target.
- **🔌 No Python Required**: The generated payload runs on any Windows machine without Python installed.
- **🛠️ Auto-Discovery**: Automatically detects Chat ID on first run.

## 🚀 How to Use

1.  **Clone the Repo**:
    ```bash
    git clone https://github.com/Prakashwijesingha/Keylogger_V1.git
    cd Keylogger_V1
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(If you don't have a requirements file yet, just install `pyTelegramBotAPI`, `pynput`, `pyinstaller`)*

3.  **Run the Builder**:
    ```bash
    python Builder.py
    ```

4.  **Generate Payload**:
    - Enter your **Telegram Bot Token**.
    - (Optional) Enter Email details.
    - Click **Generate Payload**.
    - The output `.exe` will be in the `Generated_Payloads` folder.

## 📦 Requirements

- Python 3.x
- Windows OS (for Builder)

## 🤝 Contributing

This project is open for educational enhancements. Feel free to open issues or pull requests to add new features like Screenshot capture or Remote Shell.

## 📜 License

This project is open-source. Use responsibly.
