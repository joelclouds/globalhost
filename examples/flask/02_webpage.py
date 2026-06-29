import time
from flask import Flask
from globalhost import GlobalHostApp

app = Flask(__name__)

@app.route("/")
def root():
    return """
    <html>
        <head><title>GlobalHost Flask</title></head>
        <body>
            <h1>Hello from Flask!</h1>
            <p>Served via Cloudflare Tunnel.</p>
        </body>
    </html>
    """

if __name__ == "__main__":
    host = GlobalHostApp()
    if host.bg_launch("flask", __file__, port=8005):
        print(f"\nFlask Webpage is live!")
        print(f"Public URL: {host.get_url()}")
        print("Press Ctrl+C to shut down.\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            host.stop()
