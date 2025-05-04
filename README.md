# Secure Instant P2P Chat

A Python-based secure instant messaging tool for two peers (Alice & Bob) using:
- AES-128 GCM for authenticated encryption
- PBKDF2 for key derivation (from shared passphrase)
- Per-message nonces for freshness
- Periodic rekey via special control messages
- Tkinter GUI
- TCP sockets with length-prefixed framing

## Setup

1. `pip install -r requirements.txt`
2. Run server:  `python gui.py`
3. Run client:  `python gui.py <server_ip>`
4. Enter **same** passphrase on both sides.
5. Chat securely!

## Files
- `crypto.py`: key derivation, AES‑GCM engine & rekey support
- `network.py`: framing over TCP
- `gui.py`: Tkinter front end with chat & rekey

---
