from __future__ import annotations
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

class HandoffController:
    def __init__(self, evidence_dir: Path, port: int = 9010):
        self.evidence_dir = evidence_dir
        self.port = port
        self.resume_event = threading.Event()
        self.server: ThreadingHTTPServer | None = None

    def request(self, context: dict):
        (self.evidence_dir / "intervention.json").write_text(json.dumps(context, indent=2), encoding="utf-8")
        controller = self
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/resume":
                    controller.resume_event.set()
                    self.send_response(200); self.end_headers(); self.wfile.write(b"Resuming automation")
                    return
                shot = "failure.png" if (controller.evidence_dir / "failure.png").exists() else "latest.png"
                html = f"""<html><body><h2>Human intervention requested</h2><pre>{json.dumps(context, indent=2)}</pre>
                <p>Operate the already-open headed browser window. When finished, click resume.</p>
                <p>Screenshot: {shot}</p><a href='/resume'><button>Resume automation</button></a></body></html>"""
                self.send_response(200); self.send_header("Content-Type", "text/html"); self.end_headers(); self.wfile.write(html.encode())
            def log_message(self, format, *args):
                pass
        self.server = ThreadingHTTPServer(("127.0.0.1", self.port), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def wait(self, timeout_s: int = 300) -> bool:
        ok = self.resume_event.wait(timeout_s)
        if self.server:
            self.server.shutdown()
        return ok
