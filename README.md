# GlobalHost 🛰️

Turn any machine running your code into a publicly accessible, secure SaaS backend instantly. No `localhost`, no router configuration, and zero cloud deployment setup needed during development.

## Features
* **Zero-Config Public Ingress:** Automatically spawns a secure, temporary public HTTPS tunnel (`.trycloudflare.com`) on startup.
* **Framework Agnostic:** Works flawlessly out-of-the-box with **FastAPI**, **Django**, Flask, or raw Python scripts.
* **Self-Contained & Lightweight:** Auto-provisions the exact native binary for your OS (Mac/Win/Lin) on the fly. No `brew`, `apt`, or manual downloads required, and keeps the pip package tiny.

---

## Architecture

```text
[ Any PC Running Your Code ] ──(Outbound Tunnel)──> [ Global Edge Network ] ──> [ Public Internet URL ]
```

---

## Quick Start

### 1. Installation

```bash
pip install globalhost
```

### 2. Basic Usage (Zero-Config)

Drop this into your project entrypoint. This automatically boots the tunnel and wraps your web framework.

```python
from globalhost import GlobalHostApp
from fastapi import FastAPI

app = FastAPI()

@app.get("/my-algo")
def run_algo():
    return {"status": "Your golden algo is live globally!"}

if __name__ == "__main__":
    # Boots tunnel and starts the server
    GlobalHostApp.launch(framework="fastapi", app="main:app", port=8000)
```

### 3. Programmatic Usage (Advanced)

Need to inject the live public URL into a database, webhook, or frontend config at runtime? Use the programmatic API:

```python
from globalhost import GlobalHostApp

gh = GlobalHostApp()

# Start the tunnel and grab the endpoint string
public_endpoint = gh.tunnel.start(port=9000)

print(f"🔗 Live Hyperlink: {public_endpoint}")
print(f"📦 Stored Attribute: {gh.tunnel.public_url}")

# Keep tunnel alive while your app runs...
```

---

## How It Works Under the Hood

1. **OS Detection:** On execution, the module identifies the hosting machine's operating system and architecture.
2. **Auto-Provisioning:** It silently downloads and caches the exact lightweight network binary required for that specific system.
3. **Reverse Tunnel Routing:** It executes the binary to establish a secure outbound connection to a global edge router, bypassing local firewalls and printing your public production-ready endpoint straight to the console.

---

## Examples

Ready-to-run implementations are available in the `examples/` directory:
* **FastAPI:** `examples/fastapi/01_json_api.py` & `02_webpage.py`
* **Django:** `examples/django/01_json_api.py` & `02_webpage.py`
* **Runtime URL Extraction:** `examples/runtime_url.py`

---

## Author

**Joel Opoku**
📧 [joelclouds@gmail.com](mailto:joelclouds@gmail.com)
🌐 [joelclouds.pythonanywhere.com](https://joelclouds.pythonanywhere.com)
🐙 [github.com/joelclouds/globalhost](https://github.com/joelclouds/globalhost)

## License

Distributed under the MIT License. See `LICENSE` for more information.
