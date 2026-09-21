# GlobalHost 🛰️

Turn any machine running your code into a publicly accessible, secure SaaS backend instantly. No `localhost`, no router configuration, and zero cloud deployment setup needed during development.

## Features
* **Zero-Config Public Ingress:** Automatically spawns a secure, temporary public HTTPS tunnel (`.trycloudflare.com`) on startup.
* **Framework Agnostic:** Works flawlessly out-of-the-box with **FastAPI**, **Django**, **Flask**, **Streamlit**, or raw Python scripts.
* **Self-Contained & Lightweight:** Auto-provisions the exact native binary for your OS (Mac/Win/Lin) on the fly. No `brew`, `apt`, or manual downloads required, and keeps the pip package tiny.
* **Zero Dependencies:** The core package uses only Python's standard library. No external packages required for tunneling.
* **Bulletproof Process Management:** Automatic signal handling (Ctrl+C, Ctrl+Z, terminal close) ensures zero zombie processes and instant port cleanup.
* **Background Launch Mode:** Run your app in the background while maintaining full control over the tunnel lifecycle.

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

### 2. Basic Usage (Background Mode)

Drop this into your project entrypoint. This automatically boots the tunnel and wraps your web framework in the background.

```python
import time
from globalhost import GlobalHostApp
from fastapi import FastAPI

app = FastAPI()

@app.get("/my-algo")
def run_algo():
    return {"status": "Your golden algo is live globally!"}

if __name__ == "__main__":
    host = GlobalHostApp()
    
    # Launch tunnel and server in background
    if host.bg_launch(framework="fastapi", app="main:app", port=8000):
        print(f"Public URL: {host.get_url()}")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            host.stop()
```

### 3. Programmatic Usage (Slighty Advanced)

Need to inject the live public URL into a database, webhook, or frontend config at runtime? Use the programmatic API:

```python
from globalhost import GlobalHostApp

host = GlobalHostApp()

# Start the tunnel and server in background
if host.bg_launch(framework="fastapi", app="main:app", port=9000):
    # Get the public endpoint string
    public_endpoint = host.get_url()
    
    print(f"🔗 Live Hyperlink: {public_endpoint}")
    
    # Inject into your config, database, or webhook
    # register_webhook(public_endpoint)
    
    # Keep alive
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        host.stop()
```

---

### 4. Advanced: Using Your Own Domain (Named Tunnels)

By default, GlobalHost uses temporary Quick Tunnels (`.trycloudflare.com`). For a permanent, custom domain, you can use Cloudflare Named Tunnels (100% free).

**Step 1: Get your Tunnel Token and ID**
1. In your Cloudflare Zero Trust Dashboard, go to **Networks** > **Tunnels**.
2. Note your **Tunnel ID** (a UUID like `a1b2c3d4-1234-5678-90ab-cdef12345678`).
3. Click **Configure** on your tunnel. Under "Install and run a connector", copy the **entire manual command** (e.g., `cloudflared tunnel run --token eyJh...`).

**Step 2: Point your Domain's DNS to the Tunnel**
1. Go to the main Cloudflare Dashboard and select your domain.
2. Navigate to **DNS** > **Records** and click **Add record**.
3. Create a `CNAME` record:
   - **Type**: `CNAME`
   - **Name**: `api` (or your desired subdomain, e.g., `gamebot`)
   - **Target**: `<YOUR_TUNNEL_ID>.cfargotunnel.com` (replace with your actual Tunnel ID)
   - **Proxy status**: **Proxied** (Orange cloud icon)
4. Click **Save**.

**Step 3: Launch GlobalHost with the Token**
Pass the command or token to GlobalHost. It will automatically extract the token for you.
```python
import os
from globalhost import GlobalHostApp

host = GlobalHostApp()
# Paste the entire command from Cloudflare, or just the 'eyJ...' token
token = os.getenv("CLOUDFLARE_TUNNEL_TOKEN", "cloudflared tunnel run --token YOUR_TOKEN")

host.bg_launch("fastapi", "main:app", port=8000, token=token)
```

**Step 4: Configure the Route (Fixes 502 Bad Gateway)**
The tunnel is now connected, but you must tell Cloudflare which local port to send the traffic to.
1. In the Cloudflare Zero Trust Dashboard, go to **Networks** > **Tunnels**.
2. Click your tunnel's name, then click the **Routes** tab.
3. Click **Add a public hostname** (or "Add a route").
4. Fill it out:
   - **Subdomain**: `api` (must match the DNS record Name from Step 2)
   - **Domain**: `yourdomain.com`
   - **Service**: `HTTP`
   - **URL**: `localhost:8000` (must match your app's port)
5. Click **Save**. 

Your custom domain is now permanently live and routing to your local machine!

---

## How It Works Under the Hood

1. **OS Detection:** On execution, the module identifies the hosting machine's operating system and architecture.
2. **Auto-Provisioning:** It silently downloads and caches the exact lightweight network binary required for that specific system.
3. **Reverse Tunnel Routing:** It executes the binary to establish a secure outbound connection to a global edge router, bypassing local firewalls and printing your public production-ready endpoint straight to the console.
4. **Process Isolation:** Framework servers run in isolated subprocesses with their own environment variables, preventing conflicts with your main application.
5. **Signal Handling:** The package registers OS-level signal handlers to ensure graceful shutdown on Ctrl+C, Ctrl+Z, or terminal close, preventing zombie processes.

---

## Examples

Ready-to-run implementations are available in the `examples/` directory:
* **FastAPI:** `examples/fastapi/01_json_api.py` & `02_webpage.py`
* **Django:** `examples/django/01_json_api.py` & `02_webpage.py`
* **Flask:** `examples/flask/01_json_api.py` & `02_webpage.py`
* **Streamlit:** `examples/streamlit/01_json_api.py` & `02_webpage.py`

Run any example:
```bash
python examples/fastapi/01_json_api.py
```

---

## Author

**Joel Opoku**
📧 [joelclouds@gmail.com](mailto:joelclouds@gmail.com)
🌐 [joelclouds.pythonanywhere.com](https://joelclouds.pythonanywhere.com)
🐙 [github.com/joelclouds/globalhost](https://github.com/joelclouds/globalhost)

## License

Distributed under the MIT License. See `LICENSE` for more information.

