import time
from fastapi import FastAPI
from globalhost import GlobalHostApp

app = FastAPI()

@app.get("/")
def root():
    return {"status": "success", "message": "FastAPI JSON endpoint is live!"}

if __name__ == "__main__":
    host = GlobalHostApp()

    # Launch in background. Uvicorn expects 'module_name:app_instance'
    if host.bg_launch("fastapi", "01_json_api:app", port=8000):
        print(f"\nFastAPI is live in the background!")
        print(f"Public URL: {host.get_url()}")
        print("Press Ctrl+C to shut down.\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            host.stop()
