import sys
import tkinter as tk
from tkinter import simpledialog, scrolledtext

from crypto import CryptoEngine       # Handles key derivation, encryption, decryption
from network import ChatServer, ChatClient   # Provides peer-to-peer messaging sockets

# Special tag to signal a rekey request
REKEY_TAG = b"__REKEY__"

class ChatGUI:
    """
    A secure peer-to-peer chat GUI using Tkinter.
    Performs a Diffie-Hellman–style salt exchange over a simple TCP connection,
    then encrypts/decrypts messages with CryptoEngine.
    """

    def __init__(self, master, is_server=False, peer_host=None):
        self.master = master
        master.title("Secure P2P Chat")

        # 1) Prompt user for a shared passphrase to derive the symmetric key
        passphrase = simpledialog.askstring(
            "Passphrase", "Enter shared passphrase:", show='*'
        )
        # If no passphrase given, exit cleanly
        if not passphrase:
            sys.exit(0)

        if is_server:
            # === SERVER SIDE ===
            # Create and start listening server
            self.net = ChatServer()
            self.net.start(self.on_receive)

            # Generate a fresh 16-byte salt and send it raw to the client
            salt = CryptoEngine.generate_salt()
            self.net.conn.sock.sendall(salt)
        else:
            # === CLIENT SIDE ===
            # Connect to the server address, then receive the 16-byte salt
            self.net = ChatClient(peer_host)
            salt = self.net.conn._recv_n(16)
            self.net.start(self.on_receive)

        # Derive the encryption/decryption key from passphrase + salt
        self.crypto = CryptoEngine(passphrase, salt)

        # Count messages to trigger automatic rekey
        self.msg_count = 0

        # ---- Build the GUI layout ----

        # A read-only scrolling text area for chat history
        self.txt = scrolledtext.ScrolledText(master, state='disabled', height=15)
        self.txt.pack(fill='both', expand=True)

        # Frame to hold entry box and buttons
        frame = tk.Frame(master)
        frame.pack(fill='x')

        # Text entry field for typing messages
        self.entry = tk.Entry(frame)
        self.entry.pack(side='left', fill='x', expand=True)
        # Bind Enter key to send()
        self.entry.bind('<Return>', lambda e: self.send())

        # Send button
        tk.Button(frame, text='Send', command=self.send).pack(side='left')
        # Rekey button to manually rotate the symmetric key
        tk.Button(frame, text='Rekey Now', command=self.request_rekey).pack(side='left')

    def on_receive(self, data: bytes):
        """
        Callback invoked by the network layer when raw bytes arrive.
        Handles both rekey requests and encrypted messages.
        """
        print(f"[DEBUG] GUI.on_receive(): got raw {len(data)} bytes → {data[:16].hex()}…")

        # Check for a peer-initiated rekey tag
        if data.startswith(REKEY_TAG):
            # Extract the new salt from after the tag, reinitialize CryptoEngine
            new_salt = data[len(REKEY_TAG):]
            self.crypto = CryptoEngine(self.crypto.passphrase, new_salt)
            # Log to GUI
            self.master.after(0, lambda: self._log("--- Rekeyed with peer ---"))
            return

        # Otherwise, decrypt the incoming ciphertext
        try:
            pt = self.crypto.decrypt(data).decode('utf-8')
        except Exception as e:
            pt = f"[Decryption Error: {e}]"

        # Append the plaintext to chat history
        self.master.after(0, lambda: self._log(f"Peer ▶ {pt}"))

    def send(self):
        """
        Encrypts the text in the entry box and sends it to the peer.
        Auto-rekeys after every 20 messages.
        """
        text = self.entry.get().strip()
        if not text:
            return

        # Encrypt the plaintext
        ct = self.crypto.encrypt(text.encode())
        print(f"[DEBUG] GUI.send(): sending {len(ct)} bytes → {ct[:16].hex()}…")

        # Log ciphertext and plaintext in GUI
        self._log(f"You ▶ {text}   [ct: {ct.hex()}]")

        # Send encrypted bytes over the network
        self.net.send(ct)
        # Clear the entry field
        self.entry.delete(0, 'end')

        # Track message count for automatic rekey
        self.msg_count += 1
        if self.msg_count >= 20:
            self.request_rekey()

    def request_rekey(self):
        """
        Derives a fresh salt locally, reinitializes CryptoEngine,
        and sends a REKEY_TAG + new salt to the peer.
        """
        new_salt = self.crypto.rekey()
        # Send the rekey tag and new salt
        self.net.send(REKEY_TAG + new_salt)
        self._log('--- Rekeyed locally ---')
        self.msg_count = 0

    def _log(self, msg: str):
        """
        Helper to append a line of text to the ScrolledText widget.
        """
        self.txt.configure(state='normal')
        self.txt.insert('end', msg + '\n')
        self.txt.configure(state='disabled')
        self.txt.yview('end')

if __name__ == '__main__':
    root = tk.Tk()
    # If no command-line args, run in server mode; otherwise treat first arg as peer_host
    if len(sys.argv) == 1:
        ChatGUI(root, is_server=True)
    else:
        ChatGUI(root, is_server=False, peer_host=sys.argv[1])
    root.mainloop()
