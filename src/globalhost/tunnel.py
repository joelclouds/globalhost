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

    def start(self, port: int) -> str:
        binary = self._ensure_binary_exists()
        logger.info(f"Establishing tunnel to port {port}...")

        self.process = subprocess.Popen(
            [binary, "tunnel", "--url", f"http://localhost:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True
        )

        start_time = time.time()
        # Increased timeout slightly to give Cloudflare time to reject bad requests
        while time.time() - start_time < 15: 
            line = self.process.stdout.readline()
            if not line:
                break

            # Catch Cloudflare Rate Limiting explicitly
            if "1015" in line or "429" in line:
                self.stop()
                raise RuntimeError("Cloudflare rate limit exceeded (Error 1015). You created too many tunnels recently. Please wait a few minutes or change networks.")

            if ".trycloudflare.com" in line:
                for word in line.split():
                    if "trycloudflare.com" in word:
                        url = word.strip()
                        self.public_url = url if url.startswith("https://") else f"https://{url}"
                        break
                break

        if not self.public_url:
            self.stop()
            raise RuntimeError("Failed to acquire public URL. Tunnel initialization timed out.")

        return self.public_url

    def stop(self):
        if self.process:
            logger.debug("Closing tunnel.")
            try:
                # Kill the entire process group (cloudflared + any child processes)
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass
            self.process = None
