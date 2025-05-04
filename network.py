import socket
import struct
import threading

class FramedSocket:
    def __init__(self, sock: socket.socket):
        self.sock = sock

    def send(self, data: bytes):
        print(f"[DEBUG] FramedSocket.send(): {len(data)} bytes")
        packet = struct.pack('!I', len(data)) + data
        self.sock.sendall(packet)

    def recv(self) -> bytes:
        raw = self._recv_n(4)
        if not raw:
            return b''
        length, = struct.unpack('!I', raw)
        return self._recv_n(length)

    def _recv_n(self, n: int) -> bytes:
        buf = b''
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                return b''
            buf += chunk
        return buf

class ChatServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(1)
        self.conn = None

    def start(self, on_message):
        print("[Server] Waiting for connection...")
        client_sock, addr = self.sock.accept()
        print(f"[Server] Connected from {addr}")
        self.conn = FramedSocket(client_sock)
        threading.Thread(target=self._loop, args=(on_message,), daemon=True).start()

    def _loop(self, on_message):
        while True:
            data = self.conn.recv()
            if not data:
                break
            on_message(data)

    def send(self, data: bytes):
        if self.conn:
            self.conn.send(data)

class ChatClient:
    def __init__(self, host, port=5000):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        self.conn = FramedSocket(sock)

    def start(self, on_message):
        threading.Thread(target=self._loop, args=(on_message,), daemon=True).start()

    def _loop(self, on_message):
        while True:
            data = self.conn.recv()
            if not data:
                break
            on_message(data)

    def send(self, data: bytes):
        self.conn.send(data)
