from flask import Flask, request, jsonify, Response
import threading
import time
import logging
from typing import Optional

# Configure logging for better debugging in production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from bot import BacBoBot
except ImportError as e:
    logger.error(f"Failed to import bot module: {e}")
    BacBoBot = None

app = Flask(__name__)

# Shared bot instance and lock
_bot_lock = threading.Lock()
_bot_thread = None
_bot_instance: Optional[BacBoBot] = None


@app.get("/")
def index() -> Response:
    html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Bac Bo Bot Controller</title>
  <style>
    body { font-family: system-ui, Arial, sans-serif; margin: 24px; background:#0b0f17; color:#e6edf3; }
    .card { background:#121826; border:1px solid #1f2a44; border-radius:12px; padding:20px; max-width:720px; }
    label { display:block; margin:12px 0 6px; font-weight:600; }
    input { width:100%; padding:10px 12px; border-radius:8px; border:1px solid #2a3a60; background:#0f1524; color:#e6edf3; }
    button { padding:10px 14px; border:0; border-radius:8px; margin-right:8px; cursor:pointer; font-weight:600; }
    .start { background:#1a7f37; color:#fff; }
    .stop { background:#b42318; color:#fff; }
    .row { display:flex; gap:12px; align-items:center; margin-top:16px; }
    .status { margin-top:16px; font-family: ui-monospace, Menlo, monospace; white-space:pre-wrap; }
  </style>
</head>
<body>
  <div class="card">
    <h2>🤖 Bac Bo Bot Controller</h2>
    <p>Enter your Telegram bot token and chat ID, then press Start.</p>
    <label>Bot Token</label>
    <input id="token" placeholder="123456:ABC..." />
    <label>Chat ID</label>
    <input id="chat" placeholder="123456789" />
    <div class="row">
      <button class="start" onclick="startBot()">Start</button>
      <button class="stop" onclick="stopBot()">Stop</button>
      <button onclick="refreshStatus()">Refresh Status</button>
    </div>
    <div id="msg" style="margin-top:12px;"></div>
    <div class="status" id="status"></div>
  </div>
  <script>
    async function startBot(){
      const token = document.getElementById('token').value.trim();
      const chat = document.getElementById('chat').value.trim();
      const res = await fetch('/start', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({token, chatId: chat})});
      const data = await res.json();
      document.getElementById('msg').innerText = data.message || JSON.stringify(data);
      refreshStatus();
    }
    async function stopBot(){
      const res = await fetch('/stop', {method:'POST'});
      const data = await res.json();
      document.getElementById('msg').innerText = data.message || JSON.stringify(data);
      refreshStatus();
    }
    async function refreshStatus(){
      const res = await fetch('/status');
      const data = await res.json();
      document.getElementById('status').innerText = JSON.stringify(data, null, 2);
    }
    refreshStatus();
  </script>
</body>
</html>
"""
    return Response(html, mimetype="text/html")


@app.post("/start")
def start_bot():
    if BacBoBot is None:
        return jsonify({"ok": False, "message": "Bot module not available. Check server logs."}), 500
    
    payload = request.get_json(force=True, silent=True) or {}
    token = payload.get("token")
    chat_id = payload.get("chatId")
    if not token or not chat_id:
        return jsonify({"ok": False, "message": "token and chatId are required"}), 400

    global _bot_thread, _bot_instance
    try:
        with _bot_lock:
            if _bot_thread and _bot_thread.is_alive():
                return jsonify({"ok": True, "message": "Bot already running"})
            _bot_instance = BacBoBot(token=token, chat_id=chat_id)
            _bot_instance._stop = False
            _bot_thread = threading.Thread(target=_bot_instance.run, daemon=True)
            _bot_thread.start()
        return jsonify({"ok": True, "message": "Bot starting..."})
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
        return jsonify({"ok": False, "message": f"Failed to start bot: {str(e)}"}), 500


@app.post("/stop")
def stop_bot():
    global _bot_thread, _bot_instance
    with _bot_lock:
        if _bot_instance is None:
            return jsonify({"ok": True, "message": "Bot not running"})
        try:
            # Send stop message to Telegram before stopping
            try:
                if _bot_instance.telegram_bot:
                    _bot_instance.telegram_bot.send_message("🛑 Bot stopped by user via web interface")
                    time.sleep(0.5)  # Give message time to send
            except Exception as e:
                print(f"Error sending stop message: {e}")
            
            _bot_instance.stop()
            time.sleep(1)
        finally:
            _bot_thread = None
            _bot_instance = None
    return jsonify({"ok": True, "message": "Bot stopping..."})


@app.get("/status")
def status():
    if _bot_instance is None:
        return jsonify({"running": False})
    return jsonify(_bot_instance.status())


@app.get("/health")
def health():
    """Health check endpoint for Railway"""
    return jsonify({"status": "ok", "service": "bac-bo-bot"}), 200


if __name__ == "__main__":
    # For local dev: python app_ui.py
    # For production: Railway/Heroku will set PORT environment variable
    import os
    import socket
    import sys
    
    def find_free_port(start_port=5000, max_attempts=10):
        """Find a free port starting from start_port"""
        for i in range(max_attempts):
            test_port = start_port + i
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', test_port))
                    return test_port
            except OSError:
                continue
        raise RuntimeError(f"Could not find a free port starting from {start_port}")
    
    try:
        # Determine if we're in production (Railway/Heroku sets PORT)
        is_production = "PORT" in os.environ
        
        # Use PORT env var if set (Railway/Heroku), otherwise find a free port for local dev
        if is_production:
            port = int(os.environ.get("PORT", 5000))
            host = "0.0.0.0"  # Must bind to 0.0.0.0 for external connections in production
        else:
            port = find_free_port(5000)
            host = "127.0.0.1"  # Localhost for local development
        
        debug = os.environ.get("FLASK_ENV") != "production"
        
        logger.info("=" * 50)
        logger.info("Bac Bo Bot Web UI Starting")
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info(f"Production mode: {is_production}")
        logger.info(f"Debug: {debug}")
        logger.info(f"Bot module available: {BacBoBot is not None}")
        logger.info("=" * 50)
        
        app.run(host=host, port=port, debug=debug, use_reloader=False)
    except OSError as e:
        if "access permissions" in str(e).lower() or "permission denied" in str(e).lower():
            if is_production:
                # In production, we can't try alternative ports - fail fast
                logger.error(f"Error: Port {port} requires elevated permissions or is already in use.")
                logger.error("This is a production deployment issue. Check Railway logs for more details.")
                sys.exit(1)
            else:
                # Local dev: try alternative port
                logger.warning(f"Error: Port {port} requires elevated permissions or is already in use.")
                logger.info("Trying alternative port...")
                try:
                    alt_port = find_free_port(5000)
                    logger.info(f"Starting Flask app on http://{host}:{alt_port}")
                    app.run(host=host, port=alt_port, debug=debug, use_reloader=False)
                except Exception as e2:
                    logger.error(f"Failed to start server: {e2}", exc_info=True)
                    logger.error("Please try running with a different port or check if another process is using the port.")
                    sys.exit(1)
        else:
            logger.error(f"OSError starting server: {e}", exc_info=True)
            sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error starting application: {e}", exc_info=True)
        sys.exit(1)
