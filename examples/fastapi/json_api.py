import logging
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from globalhost import GlobalHostApp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(title="GlobalHost JSON API")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    # Dynamically grab whatever host/URL the user accessed it from (local or public)
    base_url = str(request.base_url).rstrip("/")
    compute_url = f"{base_url}/api/v1/compute?x=5&y=10"

    return f"""
    <html>
        <body style="font-family: sans-serif; padding: 50px; background: #0f172a; color: #f8fafc;">
            <h2>🛰️ GlobalHost JSON API Engine Active</h2>
            <p><strong>Status:</strong> HEALTHY</p>
            <p><strong>Click to test API Endpoint:</strong> <a style="color: #38bdf8;" href="{compute_url}" target="_blank">{compute_url}</a></p>
            <p><strong>Interactive Docs:</strong> <a style="color: #38bdf8;" href="{base_url}/docs" target="_blank">{base_url}/docs</a></p>
        </body>
    </html>
    """

@app.get("/api/v1/compute")
def compute_metrics(x: float = 1.0, y: float = 1.0):
    result = x + y
    return {
        "status": "success",
        "payload": {"input_x": x, "input_y": y, "computed_result": result}
    }

if __name__ == "__main__":
    gh = GlobalHostApp()
    gh.launch(framework="fastapi", app="json_api:app", port=8000)
