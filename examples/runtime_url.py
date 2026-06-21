import logging
import time
import http.server
import socketserver
from threading import Thread
from globalhost import GlobalHostApp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    PORT = 9000
    gh = GlobalHostApp()

    print("🛠️  Manually booting tunnel layer...")
    # 1. Start the tunnel programmatically
    public_endpoint = gh.tunnel.start(port=PORT)

    print("\n" + "="*60)
    print("🛰️  RUNTIME ATTRIBUTE DETECTION SUCCESSFUL")
    print("="*60)
    print(f"🔗 Live Hyperlink:  \033[4;36m{public_endpoint}\033[0m")
    print(f"📦 Stored Attribute: {gh.tunnel.public_url}")
    print("="*60 + "\n")

    # 2. Start a simple HTTP server in the background
    print(f"🌐 Booting basic Python web server on port {PORT}...")
    handler = http.server.SimpleHTTPRequestHandler

    with socketserver.TCPServer(("", PORT), handler) as httpd:
        server_thread = Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()

        print(f"✅ Server is live! Open this in your browser: {public_endpoint}")
        print("⏱️  Keeping tunnel alive for 15 seconds so you can test it...")

        # Keep the script running so the tunnel stays open
        time.sleep(15)

        print("\n🛑 Shutting down server...")
        httpd.shutdown()

    # 3. Clean up the tunnel
    gh.tunnel.stop()
    print("GlobalHost safely shut down.")

if __name__ == "__main__":
    main()
