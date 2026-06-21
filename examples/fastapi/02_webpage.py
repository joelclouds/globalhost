import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from globalhost import GlobalHostApp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="GlobalHost UI Server")

@app.get("/api/health")
def health_check():
    return {"status": "all systems normal", "node": "local-edge-tunnel"}

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    base_url = str(request.base_url).rstrip("/")
    health_url = f"{base_url}/api/health"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>GlobalHost Live Node</title>
        <style>
            body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
            .card {{ border: 1px solid #334155; padding: 2.5rem; border-radius: 12px; background: #1e293b; text-align: center; max-width: 450px; }}
            h1 {{ color: #38bdf8; margin-top: 0; }}
            span {{ font-family: monospace; background: #0f172a; padding: 0.2rem 0.5rem; border-radius: 4px; color: #4ade80; }}
            a {{ color: #38bdf8; text-decoration: none; font-weight: bold; }}
            a:hover {{ text-decoration: underline; }}
            .endpoint-box {{ margin-top: 20px; padding: 15px; background: #0f172a; border-radius: 8px; border: 1px solid #1e293b; text-align: left; font-size: 0.9rem; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🛰️ GlobalHost Node Active</h1>
            <p>Rendered live from your local environment.</p>
            <p>Status: <span>ONLINE</span></p>

            <div class="endpoint-box">
                <strong>🔗 Navigable Endpoint:</strong><br>
                <a href="{health_url}" target="_blank">{health_url}</a>
            </div>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    gh = GlobalHostApp()
    gh.launch(framework="fastapi", app="webpage:app", port=8000)
