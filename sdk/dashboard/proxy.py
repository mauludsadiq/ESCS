#!/usr/bin/env python3
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.request, json, os

ADAPTER = "http://localhost:7710"
ANKA    = "http://localhost:18080"

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(self.path, args[1] if len(args) > 1 else '')

    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")

    def do_OPTIONS(self):
        self.send_response(200)
        self.cors()
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/adapter"):
            self._proxy(ADAPTER, self.path[8:] or "/", None)
        elif self.path.startswith("/anka"):
            self._proxy(ANKA, self.path[5:] or "/", None)
        else:
            # Strip query string for static files
            path = self.path.split('?')[0]
            self.path = path
            super().do_GET()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else None
        if self.path.startswith("/adapter"):
            self._proxy(ADAPTER, self.path[8:] or "/", body)
        elif self.path.startswith("/anka"):
            self._proxy(ANKA, self.path[5:] or "/", body)

    def _proxy(self, target, path, body):
        try:
            req = urllib.request.Request(
                target + path, data=body,
                method="POST" if body else "GET",
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = r.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.cors()
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.cors()
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "err": str(e)}).encode())

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("ESCS proxy+server on http://localhost:8080")
HTTPServer(("", 8080), Handler).serve_forever()
