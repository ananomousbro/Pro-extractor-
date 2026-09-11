import os
import time
import threading
import urllib.request
from flask import Flask, jsonify

app = Flask(__name__)
PORT = int(os.environ.get("PORT", 8080))

@app.route("/", methods=["GET", "HEAD"])
def home():
    return jsonify({
        "status": "online",
        "service": "DREAM EXTRACTOR BOT",
        "message": "Bot server is running smoothly on Render."
    })

@app.route("/health", methods=["GET", "HEAD"])
@app.route("/ping", methods=["GET", "HEAD"])
@app.route("/status", methods=["GET", "HEAD"])
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()})

def keep_alive_worker():
    """Background thread to ping the web server to keep it active and prevent sleep."""
    time.sleep(15)  # initial delay
    while True:
        try:
            render_url = os.environ.get("RENDER_EXTERNAL_URL")
            target = f"{render_url}/ping" if render_url else f"http://127.0.0.1:{PORT}/ping"
            req = urllib.request.Request(target, headers={"User-Agent": "RenderKeepAlive/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                pass
        except Exception:
            pass
        time.sleep(300)  # Ping every 5 minutes

if __name__ == "__main__":
    t = threading.Thread(target=keep_alive_worker, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=PORT)

