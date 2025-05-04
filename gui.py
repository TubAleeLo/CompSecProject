import sys
import tkinter as tk
from tkinter import simpledialog, scrolledtext
from crypto import CryptoEngine
from network import ChatServer, ChatClient

REKEY_TAG = b"__REKEY__"

class ChatGUI:
    def __init__(self, master, is_server=False, peer_host=None, port=5000):
        self.master = master
        master.title("Secure P2P Chat")

        passphrase = simpledialog.askstring("Passphrase", "Enter shared passphrase:", show='*')
        if not passphrase:
            sys.exit(0)

        if is_server:
            self.net = ChatServer(host='127.0.0.1', port=port)
            self.net.start(self.on_receive)
            salt = CryptoEngine.generate_salt()
            self.net.conn.sock.sendall(salt)
        else:
            self.net = ChatClient(peer_host or '127.0.0.1', port=port)
            salt = self.net.conn._recv_n(16)
            self.net.start(self.on_receive)

        self.crypto = CryptoEngine(passphrase, salt)
        self.msg_count = 0

        self.txt = scrolledtext.ScrolledText(master, state='disabled', height=15)
        self.txt.pack(fill='both', expand=True)

        frame = tk.Frame(master)
        frame.pack(fill='x')
        self.entry = tk.Entry(frame)
        self.entry.pack(side='left', fill='x', expand=True)
        self.entry.bind('<Return>', lambda e: self.send())

        tk.Button(frame, text='Send', command=self.send).pack(side='left')
        tk.Button(frame, text='Rekey Now', command=self.request_rekey).pack(side='left')

    def on_receive(self, data: bytes):
        print(f"[DEBUG] GUI.on_receive(): got {len(data)} bytes → {data[:16].hex()}…")
        if data.startswith(REKEY_TAG):
            new_salt = data[len(REKEY_TAG):]
            self.crypto = CryptoEngine(self.crypto.passphrase, new_salt)
            self.master.after(0, lambda: self._log("--- Rekeyed with peer ---"))
            return

        try:
            pt = self.crypto.decrypt(data).decode('utf-8')
        except Exception as e:
            pt = f"[Decryption Error: {e}]"

        self.master.after(0, lambda: self._log(f"Peer ▶ {pt}"))

    def send(self):
        text = self.entry.get().strip()
        if not text:
            return
        ct = self.crypto.encrypt(text.encode())
        print(f"[DEBUG] GUI.send(): sending {len(ct)} bytes → {ct[:16].hex()}…")
        self._log(f"You ▶ {text}   [ct: {ct.hex()}]")
        self.net.send(ct)
        self.entry.delete(0, 'end')
        self.msg_count += 1
        if self.msg_count >= 20:
            self.request_rekey()

    def request_rekey(self):
        new_salt = self.crypto.rekey()
        self.net.send(REKEY_TAG + new_salt)
        self._log('--- Rekeyed locally ---')
        self.msg_count = 0

    def _log(self, msg: str):
        self.txt.configure(state='normal')
        self.txt.insert('end', msg + '\n')
        self.txt.configure(state='disabled')
        self.txt.yview('end')


if __name__ == '__main__':
    root = tk.Tk()

    if len(sys.argv) == 1:
        ChatGUI(root, is_server=True, port=5000)
    elif len(sys.argv) == 2:
        ChatGUI(root, is_server=False, peer_host='127.0.0.1', port=int(sys.argv[1]))
    else:
        print("Usage:\n  Server: python chat_gui.py\n  Client: python chat_gui.py <port>")
        sys.exit(1)

    root.mainloop()
