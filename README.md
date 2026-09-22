# Direct PC-to-PC Chat (No Internet, No Router)

A single-file Python chat app for two computers to talk directly — no
internet connection, no router, no third-party server. Everything runs
between just the two machines.

**Zero dependencies** — uses only Python's standard library (`socket`,
`threading`, `tkinter`). Same file runs on both PCs.

## Step 1: Create a physical/direct link between the two PCs

Pick ONE of these — you need *some* physical or wireless link so the two
machines can reach each other's IP address. The chat app itself doesn't
care which one you use.

### Option A — Ethernet cable (most reliable, recommended)

1. Plug a single Ethernet cable directly between the two PCs' network ports.
   (Any modern PC's Ethernet port auto-detects a direct link — you don't
   need a special "crossover" cable anymore.)
2. Set static IPs on each PC so they're on the same subnet:

   **PC 1:**
   - IP: `192.168.55.1`
   - Subnet mask: `255.255.255.0`

   **PC 2:**
   - IP: `192.168.55.2`
   - Subnet mask: `255.255.255.0`

   **Windows:** Settings → Network & Internet → Ethernet → your adapter →
   Edit IP settings → Manual → IPv4 on.

   **macOS:** System Settings → Network → Ethernet → Configure IPv4:
   Manually.

   **Linux:** `sudo ip addr add 192.168.55.1/24 dev eth0` (use `.2` on the
   other PC).

3. Test it: on PC 1, run `ping 192.168.55.2` — you should get replies.

### Option B — WiFi Hotspot (no cable needed)

1. On PC 1: turn on "Mobile Hotspot" (Windows) or "Internet Sharing" without
   internet upstream (Mac), or just a normal hotspot — it works even with
   no internet behind it.
2. On PC 2: connect to that hotspot's WiFi network like any other WiFi.
3. Both PCs are now on the same local network with no internet required.

### Option C — Bluetooth PAN

1. Pair the two PCs over Bluetooth.
2. Set up a Bluetooth Personal Area Network (PAN) connection between them
   (both OSes support this in Bluetooth settings — look for "Join
   PAN"/"Network access point").
3. This gives both PCs an IP address over the Bluetooth link.

## Step 2: Run the chat app on both PCs

```bash
python direct_chat.py
```

(Requires Python 3. On Linux, if you get a tkinter import error:
`sudo apt install python3-tk`.)

## Step 3: Connect

- The app automatically shows **your IP address** at the top.
- On startup it also tries **Auto-Discover** — it broadcasts on the direct
  link to find the other PC running the app and connects automatically.
  If both PCs are on the same direct link, this usually just works with no
  typing required.
- If auto-discovery doesn't find it (some hotspot/router configs block
  broadcasts), type the other PC's IP address (shown in their window) into
  the **Peer IP** box and click **Connect**.

## Step 4: Chat

Type a message, hit Enter or click Send. Messages go straight over the
direct TCP connection between the two machines — nothing is relayed
anywhere else.

## How it works (technical summary)

- **Discovery**: UDP broadcast on port `5051` — each PC listens for a
  "who's out there?" packet and replies with "I'm here," so peers can find
  each other automatically without typing IPs.
- **Chat connection**: once a peer is found (or entered manually), a plain
  TCP socket is opened on port `5050` and used for actual message traffic.
- **No server, no cloud, no internet needed at any point** — as long as the
  two machines have IP addresses on the same physical/wireless link.

## Turning this into a double-click app (.exe) — no Python needed

If you'd rather not run this from a command line and don't want to install
Python on both machines, package it once into a standalone `.exe`:

1. Make sure Python is installed on ONE of the two PCs (the "build" PC).
   Get it from https://www.python.org/downloads/ — during install, check
   **"Add python.exe to PATH"**.
2. Put `direct_chat.py` and `build_exe.bat` in the same folder.
3. Double-click `build_exe.bat`. It installs PyInstaller and builds the app.
4. When it finishes, you'll find `DirectChat.exe` inside the new `dist`
   folder it created.
5. Copy `DirectChat.exe` to a folder on **both** PCs (e.g. Desktop). It's a
   single self-contained file — the other PC does **not** need Python
   installed at all.
6. Double-click `DirectChat.exe` on both PCs to launch the app, same as
   before — connect via Mobile Hotspot as described above and start
   chatting.

Windows may show a "Windows protected your PC" SmartScreen warning the
first time you run an unsigned .exe like this — click **More info** →
**Run anyway**. This happens because the app isn't digitally signed by a
paid certificate, not because anything is wrong with it.

## Troubleshooting

- **Auto-discover finds nothing**: Some networks (especially phone
  hotspots) block broadcast traffic between clients. Use manual IP connect
  instead — check each PC's IP in the app's top label.
- **Firewall blocks it**: Windows/Mac firewalls may prompt to allow the app
  through on first run — click Allow. If using Linux with `ufw`:
  `sudo ufw allow 5050/tcp` and `sudo ufw allow 5051/udp`.
- **"Could not open listening port"**: something else is using port 5050 —
  close other instances of the app, or change `TCP_PORT` in the script on
  both machines to the same new value.
"# direct-chat-app" 
