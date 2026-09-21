import os
import time
from fastapi import FastAPI
from globalhost import GlobalHostApp

app = FastAPI()

@app.get("/")
def root():
    return {
        "status": "success",
        "message": "FastAPI is live on a permanent Named Tunnel!"
    }

if __name__ == "__main__":
    host = GlobalHostApp()

    # PRO TIP: You can paste the ENTIRE manual command from Cloudflare here!
    # Example: "cloudflared tunnel run --token eyJhIjoi..."
    # The code will automatically extract just the token for you.
    token = os.getenv("CLOUDFLARE_TUNNEL_TOKEN", "cloudflared tunnel run --token YOUR_TOKEN_HERE")

    if host.bg_launch("fastapi", "03_named_tunnel:app", port=8000, token=token):
        print(f"\nFastAPI is live on your custom domain!")
        print(f"URL: {host.get_url()}")
        print("Press Ctrl+C to shut down.\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            host.stop()
