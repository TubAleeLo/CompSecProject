# Secure Instant P2P Chat

A lightweight, Python-based secure instant messaging tool for two peers (Alice & Bob).
It combines authenticated encryption, passphrase-based key derivation, and a simple GUI for ease of use.

---

## 🔒 Features

- **AES-128 GCM** for authenticated encryption
- **PBKDF2** (HMAC-SHA256, 200 000 iterations) to derive keys from a shared passphrase
- **Per-message nonces** to ensure freshness
- **Automatic & manual rekey** via special control messages
- **Length-prefixed framing** over TCP for robust message boundaries
- **Tkinter GUI** with message history, input box, and rekey button

---

## ⚙️ Prerequisites

- Python **3.8+**
- Works on Windows, macOS, and Linux

---

## ⚙️ Dependencies

- Pycryptodome, command to install in bash:
    ```bash
    pip install -r requirements.txt

---

## 📦 Installation

1. Clone or download this repository
2. Create a virtual environment (recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # on Windows: venv\Scripts\activate

---

## 🚀 Usage
- Start the server (Alice):
    ```bash
    python gui.py
- Start the client (Bob), replacing <server_ip> with Alice's address:
    ```bash
    python gui.py <server_ip>
- Enter the same passphrase on both sides when prompted.
- Type a message and press Enter or cclick Send
- Click Rekey Now (or let it auto-rekey every 20 messages) to rotate the encyption key.

---

## 📁 File Overview
- crypto.py: Key-derivation (PBKDF2), AES-GCM encrypt/decrypt, and salt-based rekeying.
- network.py: FramedSocket, ChatServer, and ChatClient classes for length-prefixed TCP messaging.
- gui.py: Tkinter-based graphical interface: passphrase prompt, chat window, entry box, and buttons.
-requirements.txt: Third-party libraries (PyCryptodome, etc.).

---

## 🔐 Security Notes
- Keep your passphrase secret: the same passphrase and salt derive your encryption key.
- Never reuse nonces: the tool generates a fresh 12-byte nonce per message.
- Rekey regularly: rotating the salt limits the impact of any key compromise.
