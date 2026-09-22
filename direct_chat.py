"""
Direct PC-to-PC Chat
---------------------
Chat between two computers with NO internet and NO router — just a direct
physical/wireless link between them. Works over:

  - A direct Ethernet cable between the two PCs (most reliable)
  - One PC's WiFi hotspot, with the other PC connected to it
  - An ad-hoc / peer-to-peer WiFi link
  - A Bluetooth PAN (Personal Area Network) connection

As long as the two PCs can ping each other's IP address, this will work.
See README.md for how to set up the physical link on Windows/Mac/Linux.

No external packages required — pure Python standard library.
"""

import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from datetime import datetime

TCP_PORT = 5050
DISCOVERY_PORT = 5051
DISCOVERY_MAGIC = b"DIRECT_CHAT_DISCOVER_V1"
DISCOVERY_REPLY = b"DIRECT_CHAT_HERE_V1"


class ChatBackend:
    """Handles all networking: discovery, connecting, sending, receiving."""

    def __init__(self, on_message, on_status):
        self.on_message = on_message      # callback(sender, text)
        self.on_status = on_status        # callback(status_text)
        self.conn = None                  # active socket once connected
        self.server_socket = None
        self.running = True
        self.connected = False

        self._start_server_thread()
        self._start_discovery_listener_thread()

    # ---------------- Discovery (finds the other PC automatically) ---------------- #

    def broadcast_discovery(self):
        """Send a UDP broadcast asking 'is anyone else running this app?'"""
        def _run():
            udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            udp.settimeout(3)
            try:
                udp.sendto(DISCOVERY_MAGIC, ("255.255.255.255", DISCOVERY_PORT))
                self.on_status("Searching for peer on the direct link...")
                start = datetime.now()
                while (datetime.now() - start).seconds < 3:
                    try:
                        data, addr = udp.recvfrom(1024)
                        if data == DISCOVERY_REPLY:
                            self.on_status(f"Found peer at {addr[0]}. Connecting...")
                            self.connect_to(addr[0])
                            return
                    except socket.timeout:
                        break
                self.on_status("No peer found automatically. Enter their IP manually.")
            finally:
                udp.close()
        threading.Thread(target=_run, daemon=True).start()

    def _start_discovery_listener_thread(self):
        """Listen for other PCs asking 'is anyone here?' and reply."""
        def _run():
            udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                udp.bind(("", DISCOVERY_PORT))
            except OSError as e:
                self.on_status(f"Discovery listener failed: {e}")
                return
            while self.running:
                try:
                    data, addr = udp.recvfrom(1024)
                    if data == DISCOVERY_MAGIC:
                        udp.sendto(DISCOVERY_REPLY, addr)
                except OSError:
                    break
        threading.Thread(target=_run, daemon=True).start()

    # ---------------- Connecting ---------------- #

    def _start_server_thread(self):
        """Accept an incoming connection from the other PC."""
        def _run():
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                self.server_socket.bind(("", TCP_PORT))
                self.server_socket.listen(1)
            except OSError as e:
                self.on_status(f"Could not open listening port: {e}")
                return
            while self.running:
                try:
                    conn, addr = self.server_socket.accept()
                    if not self.connected:
                        self.conn = conn
                        self.connected = True
                        self.on_status(f"Connected to {addr[0]} (they connected to you)")
                        self._listen_for_messages()
                    else:
                        conn.close()  # already have a peer, reject extras
                except OSError:
                    break
        threading.Thread(target=_run, daemon=True).start()

    def connect_to(self, ip: str):
        """Actively connect out to the other PC's IP."""
        def _run():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect((ip, TCP_PORT))
                s.settimeout(None)
                self.conn = s
                self.connected = True
                self.on_status(f"Connected to {ip}")
                self._listen_for_messages()
            except Exception as e:
                self.on_status(f"Could not connect to {ip}: {e}")
        threading.Thread(target=_run, daemon=True).start()

    def _listen_for_messages(self):
        def _run():
            while self.running and self.connected:
                try:
                    data = self.conn.recv(4096)
                    if not data:
                        break
                    self.on_message("Peer", data.decode("utf-8", errors="replace"))
                except OSError:
                    break
            self.connected = False
            self.on_status("Peer disconnected.")
        threading.Thread(target=_run, daemon=True).start()

    def send(self, text: str) -> bool:
        if not self.connected or not self.conn:
            return False
        try:
            self.conn.sendall(text.encode("utf-8"))
            return True
        except OSError:
            self.connected = False
            self.on_status("Connection lost.")
            return False

    def shutdown(self):
        self.running = False
        for s in (self.conn, self.server_socket):
            try:
                if s:
                    s.close()
            except OSError:
                pass


class ChatUI:
    def __init__(self, root):
        self.root = root
        root.title("Direct PC-to-PC Chat")
        root.geometry("520x600")
        root.configure(bg="#101418")

        self.backend = ChatBackend(self._on_message, self._on_status)

        my_ip = self._get_local_ip()

        top = tk.Frame(root, bg="#101418")
        top.pack(fill="x", padx=10, pady=8)
        tk.Label(
            top, text=f"Your IP: {my_ip}", fg="#7fd8ff", bg="#101418",
            font=("Consolas", 10, "bold")
        ).pack(anchor="w")

        self.status_label = tk.Label(
            top, text="Not connected", fg="#ffb43c", bg="#101418", font=("Consolas", 9)
        )
        self.status_label.pack(anchor="w", pady=(2, 6))

        connect_row = tk.Frame(top, bg="#101418")
        connect_row.pack(fill="x")
        tk.Label(connect_row, text="Peer IP:", fg="white", bg="#101418").pack(side="left")
        self.ip_entry = tk.Entry(connect_row, width=18)
        self.ip_entry.pack(side="left", padx=5)
        tk.Button(connect_row, text="Connect", command=self._manual_connect).pack(side="left")
        tk.Button(connect_row, text="Auto-Discover", command=self.backend.broadcast_discovery).pack(side="left", padx=5)

        self.log = scrolledtext.ScrolledText(
            root, bg="#0c1015", fg="#d8f6ff", font=("Consolas", 10),
            state="disabled", wrap="word"
        )
        self.log.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        bottom = tk.Frame(root, bg="#101418")
        bottom.pack(fill="x", padx=10, pady=(0, 10))
        self.msg_entry = tk.Entry(bottom, font=("Consolas", 11))
        self.msg_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.msg_entry.bind("<Return>", lambda e: self._send())
        tk.Button(bottom, text="Send", command=self._send).pack(side="left")

        root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Try auto-discovery on startup
        root.after(300, self.backend.broadcast_discovery)

    @staticmethod
    def _get_local_ip() -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # doesn't send data, just picks the right interface
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return socket.gethostbyname(socket.gethostname())

    def _manual_connect(self):
        ip = self.ip_entry.get().strip()
        if ip:
            self.backend.connect_to(ip)

    def _send(self):
        text = self.msg_entry.get().strip()
        if not text:
            return
        if self.backend.send(text):
            self._append(f"You: {text}")
            self.msg_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Not connected", "You're not connected to a peer yet.")

    def _on_message(self, sender, text):
        self.root.after(0, lambda: self._append(f"{sender}: {text}"))

    def _on_status(self, text):
        self.root.after(0, lambda: self.status_label.config(text=text))

    def _append(self, line: str):
        self.log.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log.insert(tk.END, f"[{timestamp}] {line}\n")
        self.log.configure(state="disabled")
        self.log.see(tk.END)

    def _on_close(self):
        self.backend.shutdown()
        self.root.destroy()


def main():
    root = tk.Tk()
    ChatUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
