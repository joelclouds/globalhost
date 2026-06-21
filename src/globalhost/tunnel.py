import os
import platform
import subprocess
import time
import sys
import urllib.request
import logging

# Set up a named logger for this module
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
            raise RuntimeError(f"GlobalHost doesn't support your OS yet: {self.system}")

    def _ensure_binary_exists(self) -> str:
        base_dir = os.path.dirname(__file__)
        bin_dir = os.path.join(base_dir, "bin")
        os.makedirs(bin_dir, exist_ok=True)

        filename, download_url = self._get_binary_config()
        binary_path = os.path.join(bin_dir, filename)

        if filename.endswith(".tgz"):
            binary_path = os.path.join(bin_dir, "cloudflared")

        if not os.path.exists(binary_path):
            logger.info("Core networking module missing. Downloading from Cloudflare network...")
            logger.debug(f"Downloading from URL: {download_url}")
            try:
                temp_download = os.path.join(bin_dir, filename)
                urllib.request.urlretrieve(download_url, temp_download)
                if filename.endswith(".tgz"):
                    import tarfile
                    with tarfile.open(temp_download, "r:gz") as tar:
                        tar.extractall(path=bin_dir)
                    os.remove(temp_download)
                logger.info("Download complete.")
            except Exception as e:
                logger.error(f"Failed to download network binary: {e}")
                sys.exit(1)

        if "windows" not in self.system:
            os.chmod(binary_path, 0o755)

        return binary_path

    def start(self, port: int) -> str:
        binary = self._ensure_binary_exists()

        logger.info(f"Establishing secure edge network tunnel to port {port}...")

        self.process = subprocess.Popen(
            [binary, "tunnel", "--url", f"http://localhost:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        start_time = time.time()
        while time.time() - start_time < 10:
            line = self.process.stdout.readline()
            if not line:
                break

            if ".trycloudflare.com" in line:
                for word in line.split():
                    if "trycloudflare.com" in word:
                        url = word.strip()
                        if url.startswith("https://"):
                            self.public_url = url
                        else:
                            self.public_url = f"https://{url}"
                        break
                break

        return self.public_url

    def stop(self):
        if self.process:
            logger.info("Collapsing tunnel, removing machine from public routing...")
            self.process.terminate()
            self.process.wait()
