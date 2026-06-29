import time
from flask import Flask, jsonify
from globalhost import GlobalHostApp

app = Flask(__name__)

@app.route("/")
def root():
    return jsonify({
        "status": "success",
        "message": "Flask JSON endpoint is live!"
    })

if __name__ == "__main__":
    host = GlobalHostApp()

    # Pass __file__ so Flask knows exactly where this module lives
    if host.bg_launch("flask", __file__, port=8004):
        print(f"\nFlask is live in the background!")
        print(f"Public URL: {host.get_url()}")
        print("Press Ctrl+C to shut down.\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            host.stop()
