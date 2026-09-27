# 📍 GeoPals - Real-Time Multi-Device Live GPS Tracker

**GeoPals** is a lightweight, zero-dependency, real-time multi-device live location tracking web application. It allows $N$ connected smartphones, tablets, and laptops to broadcast their live GPS coordinates and view everyone tagged on a shared interactive map in real-time—just like Instagram Maps or Find My.

---

## 🌟 Key Features

- 📱 **Real-Time Native Mobile GPS Stream**: Captures native hardware GPS coordinates (`lat`, `lng`, accuracy) via `navigator.geolocation.watchPosition`.
- 👥 **Multi-Device Social Map**: Every connected user gets a unique avatar badge (`📱`, `🚀`, `⚡`, `🔥`, `👑`) and pulsing map pin displaying their device name and status.
- 🔒 **Auto-Generated HTTPS Server**: Runs dual HTTP (port `8000`) and HTTPS (port `8443`) servers out of the box to bypass mobile browser security restrictions on HTTP IP addresses.
- 🗺️ **Tap-to-Place Spot Selection**: Allows users to tap anywhere on the map screen or click preset spot buttons (e.g., Lab Bench, Entrance, Gate) to set and broadcast their position manually.
- ⚡ **Zero-Dependency Architecture**: Uses standard Python 3 HTTP/HTTPS server + Vanilla JS + Tailwind CDN + Leaflet Maps. No Node.js build tools required.

---

## 🚀 Quick Start

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/kelinavipu/geopals.git
   cd geopals
   ```

2. **Run the Server**:
   ```bash
   python server.py
   ```

3. **Open on Mobile Phones (Same Wi-Fi Network)**:
   - For **Full Hardware Mobile GPS**, open the **HTTPS link** on your mobile phone:
     👉 `https://<YOUR_LOCAL_IP>:8443/index.html`
   - *(Tap "Proceed / Accept Self-Signed Certificate" on your phone's browser when prompted).*

4. **Open on Laptop / Local Browser**:
   👉 `http://localhost:8000`

---

## 🛠️ Architecture

- **`index.html`**: Main full-bleed interactive social map UI powered by Leaflet.js and Tailwind CSS.
- **`server.py`**: Multi-threaded Python server that manages HTTPS SSL certificates and handles multi-device location merging via `/api/sync`.

---

## 📜 License

MIT License &copy; 2026 GeoPals Team.
