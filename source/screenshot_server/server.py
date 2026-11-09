from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote
import html
import time

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

class ScreenshotHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/":
            images = sorted(
                UPLOAD_DIR.glob("*.png"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            gallery = "".join(
                f'<div><p>{html.escape(p.name)}</p>'
                f'<img src="/images/{p.name}" width="550"></div>'
                for p in images
            )

            page = f"""
            <html>
            <head>
                <meta http-equiv="refresh" content="30">
                <title>Screenshot Gallery</title>
            </head>
            <body>
                <h1>Received Images</h1>
                <p>This gallery refreshes every 30 seconds.</p>
                {gallery if gallery else "No screenshots received yet."}
            </body>
            </html>
            """

            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(page.encode())

        elif self.path.startswith("/images/"):
            filename = Path(unquote(self.path.split("/")[-1])).name
            image_path = UPLOAD_DIR / filename

            if image_path.is_file() and image_path.suffix == ".png":
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.end_headers()
                self.wfile.write(image_path.read_bytes())
            else:
                self.send_error(404)

        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/upload":
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", 0))

        if length <= 0 or length > 10 * 1024 * 1024:
            self.send_error(400, "Invalid image size")
            return

        data = self.rfile.read(length)

        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            self.send_error(400, "PNG images only")
            return

        filename = f"screenshot_{int(time.time() * 1000)}.png"
        (UPLOAD_DIR / filename).write_bytes(data)

        self.send_response(201)
        self.end_headers()
        self.wfile.write(b"Screenshot received")

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), ScreenshotHandler)
    print("Gallery running at http://127.0.0.1:8000")
    server.serve_forever()