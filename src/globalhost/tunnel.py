import os
import platform
import subprocess
import time
import sys
import urllib.request
import tarfile
import signal
import logging

logger = logging.getLogger("globalhost.tunnel")

class TunnelManager:
    def __init__(self):
        self.system = platform.system().lower()
        self.machine = platform.machine().lower()
        self.process = None
        self.public_url = None

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
        base_dir = os.path.dirname(__file__)
        bin_dir = os.path.join(base_dir, "bin")
        os.makedirs(bin_dir, exist_ok=True)

        filename, download_url = self._get_binary_config()
        binary_path = os.path.join(bin_dir, filename)

        if filename.endswith(".tgz"):
            binary_path = os.path.join(bin_dir, "cloudflared")

        if not os.path.exists(binary_path):
            logger.info("cloudflared binary not found. Downloading...")
            logger.debug(f"Downloading from URL: {download_url}")
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

        if token:
            # SMART PARSING: If user pasted the whole command, grab the last word (the token).
            token = token.strip().split()[-1]

            logger.info("Establishing Named Tunnel to your Cloudflare domain...")
            cmd = [binary, "tunnel", "--no-autoupdate", "run", "--token", token]
            success_indicator = "Registered" # cloudflared logs "Registered tunnel connection"
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

            # Catch Cloudflare API Errors (Rate limits or invalid tokens)
            if "1015" in line or "429" in line:
                self.stop()
                if token:
                    raise RuntimeError(f"Cloudflare API rejected the Named Tunnel (Error 1015/429). Your account might be rate-limited or the token is invalid. Raw log: {line.strip()}")
                else:
                    raise RuntimeError("Cloudflare rate limit exceeded (Error 1015). You created too many Quick Tunnels recently.")

            # Catch Invalid Token errors (Named Tunnels)
            if token and ("ERR" in line and ("token" in line.lower() or "register" in line.lower())):
                self.stop()
                raise RuntimeError(f"Cloudflare rejected the token. Details: {line.strip()}")

            if success_indicator in line:
                if token:
                    # For named tunnels, the URL is the user's custom domain.
                    self.public_url = "https://<your-configured-domain>"
                else:
                    for word in line.split():
                        if "trycloudflare.com" in word:
                            url = word.strip()
                            self.public_url = url if url.startswith("https://") else f"https://{url}"
                            break
                break

        if not self.public_url:
            self.stop()
            if token:
                raise RuntimeError("Failed to connect Named Tunnel. Check your token and Cloudflare dashboard.")
            else:
                raise RuntimeError("Failed to acquire public URL. Tunnel initialization timed out.")

        return self.public_url

    def stop(self):
        if self.process:
            logger.debug("Closing tunnel.")
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass
            self.process = None
