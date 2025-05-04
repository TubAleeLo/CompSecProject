import socket
import struct
import threading

class FramedSocket:
    """
    Wraps a raw socket to send and receive length-prefixed byte frames.
    Each message is prefixed with a 4-byte big-endian length header.
    """
    def __init__(self, sock: socket.socket):
        self.sock = sock

    def send(self, data: bytes):
        """
        Send a complete message as a length-prefixed frame.
        - Logs the byte count for debugging.
        - Packs the length as a 4-byte big-endian unsigned int.
        - Sends header + payload atomically via sendall.
        """
        print(f"[DEBUG] FramedSocket.send(): {len(data)} bytes")
        # Pack the length header, then append the actual data
        packet = struct.pack('!I', len(data)) + data
        self.sock.sendall(packet)

    def recv(self) -> bytes:
        """
        Receive a single length-prefixed frame.
        - First read 4 bytes for the length header.
        - If header is empty, peer closed connection → return empty bytes.
        - Otherwise, read exactly 'length' bytes for the payload.
        """
        raw = self._recv_n(4)
        if not raw:
            return b''  # Connection closed or error
        length, = struct.unpack('!I', raw)
        return self._recv_n(length)

    def _recv_n(self, n: int) -> bytes:
        """
        Helper to read exactly n bytes from the socket.
        - Continues reading until buffer has n bytes or connection closes.
        - Returns empty bytes if the peer closed the connection mid-read.
        """
        buf = b''
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                return b''  # Connection closed
            buf += chunk
        return buf

class ChatServer:
    """
    Simple single-connection chat server using framed messages.
    Listens for one client, then dispatches incoming frames to a callback.
    """
    def __init__(self, host='0.0.0.0', port=5000):
        # Create a TCP socket and bind to host:port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((host, port))
        self.sock.listen(1)   # Only one pending connection
        self.conn = None      # Will hold the FramedSocket after accept()

    def start(self, on_message):
        """
        Accept a client connection and spawn a listener thread.
        - on_message: callback to handle each received frame.
        """
        print("[Server] Waiting for connection...")
        client_sock, addr = self.sock.accept()
        print(f"[Server] Connected from {addr}")
        # Wrap raw socket with framing protocol
        self.conn = FramedSocket(client_sock)
        # Launch background thread to receive messages
        threading.Thread(target=self._loop, args=(on_message,), daemon=True).start()

    def _loop(self, on_message):
        """
        Continuously receive frames and invoke callback.
        - Stops when connection closes (recv returns empty bytes).
        """
        while True:
            data = self.conn.recv()
            if not data:
                break
            on_message(data)

    def send(self, data: bytes):
        """
        Send a framed message to the connected client.
        - Only works after a client has connected.
        """
        if self.conn:
            self.conn.send(data)

class ChatClient:
    """
    Simple chat client that connects to a ChatServer and communicates via framed messages.
    """
    def __init__(self, host, port=5000):
        # Create and connect socket to the server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        # Wrap raw socket with framing protocol
        self.conn = FramedSocket(sock)

    def start(self, on_message):
        """
        Spawn a listener thread to handle incoming frames.
        - on_message: callback to handle each received frame.
        """
        threading.Thread(target=self._loop, args=(on_message,), daemon=True).start()

    def _loop(self, on_message):
        """
        Continuously receive frames and invoke callback.
        - Stops when server closes connection (recv returns empty bytes).
        """
        while True:
            data = self.conn.recv()
            if not data:
                break
            on_message(data)

    def send(self, data: bytes):
        """
        Send a framed message to the server.
        """
        self.conn.send(data)
