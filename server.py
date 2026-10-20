#!/usr/bin/env python3
"""Multi-Threaded HTTP Server for the LEGO Microduck Interactive 3D Web Assembly Studio & Deliverable Hub.

Serves:
  - `/` and static assets from `web/`
  - `/output/*` CAD deliverables, PDF manual, BrickLink XML, BOM CSV, LDraw MPD/LDR, and JSON reports
  - `/favicon.ico` inline SVG icon (prevents 404 console errors)
  - `/api/health` JSON health check with live verification metrics
Bound to `0.0.0.0:8765` with `ThreadingHTTPServer` (`daemon_threads = True`) for Cloudtop-to-Mac hybrid access.
"""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import sys
from urllib.parse import unquote, urlparse

PROJECT_ROOT = Path(__file__).resolve().parent
WEB_DIR = PROJECT_ROOT / "web"
OUTPUT_DIR = PROJECT_ROOT / "output"

FAVICON_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
    b'<rect width="32" height="32" fill="#1B2A34"/>'
    b'<circle cx="16" cy="16" r="10" fill="#F2CD37"/>'
    b'<circle cx="16" cy="16" r="5" fill="#1B2A34"/>'
    b'</svg>'
)

# Ensure custom CAD MIME types are registered
mimetypes.add_type("application/pdf", ".pdf")
mimetypes.add_type("application/xml", ".xml")
mimetypes.add_type("text/csv", ".csv")
mimetypes.add_type("text/plain", ".mpd")
mimetypes.add_type("text/plain", ".ldr")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")


class ThreadedMicroduckServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class MicroduckStudioHandler(SimpleHTTPRequestHandler):
    """Custom request handler mapping `/` -> `web/` and `/output/*` -> `output/`."""

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        super().end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        req_path = unquote(parsed.path)

        if req_path == "/favicon.ico":
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(FAVICON_SVG)))
            self.end_headers()
            self.wfile.write(FAVICON_SVG)
            return

        if req_path == "/api/health":
            report_path = OUTPUT_DIR / "verification_report.json"
            pdf_path = OUTPUT_DIR / "microduck_instruction_manual.pdf"
            model_path = OUTPUT_DIR / "microduck_model.json"
            payload = {
                "status": "ok",
                "service": "LEGO Microduck 3D Assembly Studio (Rev 3.2)",
                "pdf_exists": pdf_path.exists(),
                "pdf_size_bytes": pdf_path.stat().st_size if pdf_path.exists() else 0,
                "report_exists": report_path.exists(),
                "model_exists": model_path.exists(),
                "model_size_bytes": model_path.stat().st_size if model_path.exists() else 0,
            }
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        super().do_GET()

    def translate_path(self, path: str) -> str:
        parsed = urlparse(path)
        req_path = unquote(parsed.path).lstrip("/")

        if req_path.startswith("output/"):
            rel = req_path[len("output/") :]
            target = (OUTPUT_DIR / rel).resolve()
            if str(target).startswith(str(OUTPUT_DIR.resolve())):
                return str(target)

        if req_path == "" or req_path == "/":
            return str((WEB_DIR / "index.html").resolve())

        target = (WEB_DIR / req_path).resolve()
        if str(target).startswith(str(WEB_DIR.resolve())):
            return str(target)

        return str((WEB_DIR / "index.html").resolve())

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[MicroduckStudio] {self.address_string()} - {fmt % args}\n")
        sys.stderr.flush()


def run_server(host: str = "0.0.0.0", port: int = 8765) -> None:
    server = ThreadedMicroduckServer((host, port), MicroduckStudioHandler)
    print(f"LEGO Microduck 3D Studio (Multi-Threaded) serving on http://{host}:{port}")
    sys.stdout.flush()
    server.serve_forever()


if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    run_server(host="0.0.0.0", port=port_arg)
