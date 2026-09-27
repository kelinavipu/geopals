#!/usr/bin/env python3
"""
GeoPals Server with Real-Time Multi-Device Sync Engine & Auto-Generated SSL
Runs out of the box with `python server.py`.
Supports dual HTTP (port 8000) and HTTPS (port 8443) serving.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import json
import threading

PORT = 8000
HTTPS_PORT = 8443
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
SYNC_CACHE = {}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Enable CORS and disable caching
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/sync' or self.path.startswith('/api/sync?'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            key = None
            if 'key=' in self.path:
                key = self.path.split('key=')[1].split('&')[0]

            val = SYNC_CACHE.get(key) if key else None
            response_data = {
                "key": key,
                "value": val,
                "cache": SYNC_CACHE
            }
            if key and val is not None:
                response_data[key] = val

            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return
        super().do_GET()

    def do_POST(self):
        if self.path == '/api/sync':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode('utf-8'))
                key = data.get('key')
                value = data.get('value')
                if key:
                    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict) and 'id' in value[0]:
                        existing = SYNC_CACHE.get(key, [])
                        if not isinstance(existing, list):
                            existing = []
                        device_map = {d['id']: d for d in existing if isinstance(d, dict) and 'id' in d}
                        for new_d in value:
                            if isinstance(new_d, dict) and 'id' in new_d:
                                device_map[new_d['id']] = new_d
                        SYNC_CACHE[key] = list(device_map.values())
                    else:
                        SYNC_CACHE[key] = value

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok", "syncedKey": key, "value": SYNC_CACHE.get(key)}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return
        self.send_response(404)
        self.end_headers()

def ensure_ssl_certificates():
    cert_path = os.path.join(DIRECTORY, 'cert.pem')
    key_path = os.path.join(DIRECTORY, 'key.pem')
    if os.path.exists(cert_path) and os.path.exists(key_path):
        return cert_path, key_path

    try:
        from datetime import datetime, timedelta, timezone
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import socket, ipaddress

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'GeoPals-Local-Server')])

        alt_names = [x509.DNSName('localhost'), x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            alt_names.append(x509.IPAddress(ipaddress.ip_address(local_ip)))
        except Exception:
            pass

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.now(timezone.utc)
        ).not_valid_after(
            datetime.now(timezone.utc) + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName(alt_names),
            critical=False,
        ).sign(key, hashes.SHA256())

        with open(cert_path, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        with open(key_path, 'wb') as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        return cert_path, key_path
    except Exception as e:
        print(f"Warning: Could not auto-generate SSL certs ({e}). HTTPS mode may be disabled.")
        return None, None

def main():
    os.chdir(DIRECTORY)
    socketserver.TCPServer.allow_reuse_address = True
    
    port = PORT
    httpd = None
    
    for try_port in range(PORT, PORT + 10):
        try:
            httpd = socketserver.TCPServer(("", try_port), Handler)
            port = try_port
            break
        except OSError as e:
            if e.winerror == 10048 or e.errno == 98:
                continue
            raise e

    if not httpd:
        print(f"Error: Could not bind to any port between {PORT} and {PORT + 9}.")
        sys.exit(1)

    httpsd = None
    cert_path, key_path = ensure_ssl_certificates()
    
    if cert_path and key_path:
        import ssl
        try:
            httpsd = socketserver.TCPServer(("", HTTPS_PORT), Handler)
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(certfile=cert_path, keyfile=key_path)
            httpsd.socket = ssl_context.wrap_socket(httpsd.socket, server_side=True)
        except Exception as err:
            print(f"HTTPS Server Init Warning: {err}")
            httpsd = None

    if httpsd:
        https_thread = threading.Thread(target=httpsd.serve_forever, daemon=True)
        https_thread.start()

    with httpd:
        import socket
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            local_ip = "192.168.x.x"

        print("=" * 70)
        print(" GEOPALS: Real-Time Multi-Device Live GPS Tracker Server")
        print("=" * 70)
        print(f" 🌐 HTTP Local Server:    http://localhost:{port}")
        print(f" 📱 HTTP Mobile Link:    http://{local_ip}:{port}")
        if httpsd:
            print(f" 🔒 HTTPS Secure Server:  https://localhost:{HTTPS_PORT}")
            print(f" 🚀 HTTPS MOBILE GPS:   https://{local_ip}:{HTTPS_PORT}")
            print("    (Use HTTPS link on mobile phones to enable native hardware GPS!)")
        print("=" * 70)
        print(" Press Ctrl+C to terminate the server.\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server. Goodbye!")
            sys.exit(0)

if __name__ == '__main__':
    main()
