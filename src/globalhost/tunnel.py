import os
import platform
import subprocess
import time
import sys
import urllib.request
import tarfile
import signal
import logging
import base64
import json

logger = logging.getLogger("globalhost.tunnel")

class TunnelManager:
    def __init__(self):
        self.system = platform.system().lower()
        self.machine = platform.machine().lower()
        self.process = None
        self.public_url = None

    def _is_termux(self) -> bool:
        return os.path.exists("/data/data/com.termux")

    def _get_tunnel_id_from_token(self, token: str) -> str | None:
        try:
            if '.' in token:
                payload = token.split('.')[1]
            else:
                payload = token
            padding = '=' * (4 - len(payload) % 4)
            decoded_bytes = base64.urlsafe_b64decode(payload + padding)
            return json.loads(decoded_bytes).get('tun') or json.loads(decoded_bytes).get('t')
        except Exception:
            return None

    def _get_binary_config(self):
        base_url = "https://github.com/cloudflare/cloudflared/releases/latest/download/"
        if "windows" in self.system:
            filename = "cloudflared-windows-amd64.exe"
            return filename, base_url + filename
        elif "linux" in self.system:
            filename = "cloudflared-linux-arm64" if "arm" in self.machine or "aarch64" in self.machine else "cloudflared-linux-amd64"
            return filename, base_url + filename
        elif "darwin" in self.system:
            filename = "cloudflared-darwin-arm64.tgz" if "arm" in self.machine else "cloudflared-darwin-amd64.tgz"
            return filename, base_url + filename
        else:
            raise RuntimeError(f"Unsupported operating system: {self.system}")

    def _ensure_binary_exists(self) -> str:
        if self._is_termux():
            if subprocess.run(["which", "cloudflared"], capture_output=True).returncode != 0:
                logger.info("Installing cloudflared via pkg...")
                subprocess.run(["pkg", "install", "cloudflared", "-y"], check=True)
            return "cloudflared"

        base_dir = os.path.dirname(__file__)
        bin_dir = os.path.join(base_dir, "bin")
        os.makedirs(bin_dir, exist_ok=True)

        filename, download_url = self._get_binary_config()
        binary_path = os.path.join(bin_dir, filename)

        if filename.endswith(".tgz"):
            binary_path = os.path.join(bin_dir, "cloudflared")

        if not os.path.exists(binary_path):
            logger.info("cloudflared binary not found. Downloading...")
            try:
                temp_download = os.path.join(bin_dir, filename)
                urllib.request.urlretrieve(download_url, temp_download)
                if filename.endswith(".tgz"):
                    with tarfile.open(temp_download, "r:gz") as tar:
                        tar.extractall(path=bin_dir)
                    os.remove(temp_download)
                logger.info("Download complete.")
            except Exception as e:
                logger.error(f"Failed to download cloudflared binary: {e}")
                sys.exit(1)

        if "windows" not in self.system:
            os.chmod(binary_path, 0o755)

        return binary_path

    def start(self, port: int, token: str | None = None) -> str:
        binary = self._ensure_binary_exists()

        if self._is_termux():
            logger.info("Acquiring Termux wake lock to prevent Android sleep...")
            subprocess.run(["termux-wake-lock"], check=False)

        if token:
            token = token.strip().split()[-1]
            tunnel_id = self._get_tunnel_id_from_token(token)
            self.public_url = f"https://{tunnel_id}.cfargotunnel.com" if tunnel_id else "https://<your-tunnel-id>.cfargotunnel.com"
            logger.info("Establishing Named Tunnel connection...")
            cmd = [binary, "tunnel", "--no-autoupdate", "run", "--token", token]
            success_indicator = "Registered"
        else:
            logger.info(f"Establishing Quick Tunnel to port {port}...")
            cmd = [binary, "tunnel", "--url", f"http://localhost:{port}"]
            success_indicator = ".trycloudflare.com"

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True
        )

        start_time = time.time()
        while time.time() - start_time < 15:
            line = self.process.stdout.readline()
            if not line:
                if self.process.poll() is not None:
                    break
                continue

            if "1015" in line or "429" in line:
                self.stop()
                if token:
                    raise RuntimeError(f"Cloudflare API rejected the Named Tunnel (Error 1015/429). Raw log: {line.strip()}")
                else:
                    raise RuntimeError("Cloudflare rate limit exceeded (Error 1015).")

            if token and ("ERR" in line and ("token" in line.lower() or "register" in line.lower())):
                self.stop()
                raise RuntimeError(f"Cloudflare rejected the token. Details: {line.strip()}")

            if success_indicator in line:
                if token:
                    # Named tunnel URL was already set above
                    pass
                else:
                    # Extract Quick Tunnel URL
                    for word in line.split():
                        if "trycloudflare.com" in word:
                            url = word.strip()
                            self.public_url = url if url.startswith("https://") else f"https://{url}"
                            break
                break

        if not self.public_url:
            self.stop()
            raise RuntimeError("Failed to connect tunnel. Check your token and Cloudflare dashboard.")

        return self.public_url

    def stop(self):
        if self.process:
            logger.debug("Closing tunnel.")
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass
            self.process = None
