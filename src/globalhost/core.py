import sys
import os
import subprocess
import logging
from .tunnel import TunnelManager

# Root logger configuration for the globalhost package
logger = logging.getLogger("globalhost")

class GlobalHostApp:
    def __init__(self):
        self.tunnel = TunnelManager()
        self.url = None

    def launch(self, framework: str, app: str, port: int = 8000):
        framework = framework.lower()

        try:
            # 1. Start tunnel and grab URL
            self.url = self.tunnel.start(port=port)

            logger.info(f"\n🚀 GLOBALHOST IS LIVE!\n👉 YOUR PUBLIC URL: {self.url} 👈\n")

            # 2. Spin up framework
            if framework == "fastapi":
                logger.info(f"Launching FastAPI backend via Uvicorn on port {port}...")

                # Get the directory of the currently running script
                script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

                subprocess.run(
                    [sys.executable, "-m", "uvicorn", app, "--host", "127.0.0.1", "--port", str(port)],
                    cwd=script_dir  # 👈 Run Uvicorn from the script's directory
                )
            elif framework == "django":
                logger.info(f"Launching Django server on port {port}...")

                if os.path.exists("manage.py"):
                    subprocess.run([sys.executable, "manage.py", "runserver", f"127.0.0.1:{port}"])
                else:
                    logger.info("No manage.py detected. Booting Django in standalone mode...")

                    # Clean up file paths or standard dot notation signatures
                    clean_app = app.replace("\\", "/").rstrip(".py")

                    if "/" in clean_app:
                        module_dir = os.path.dirname(os.path.abspath(clean_app))
                        module_name = os.path.basename(clean_app)
                    else:
                        module_dir = os.getcwd()
                        module_name = clean_app

                    # Inject the target example directory directly into the python process environment map
                    env = os.environ.copy()
                    env["PYTHONPATH"] = module_dir + os.pathsep + env.get("PYTHONPATH", "")

                    subprocess.run([
                        sys.executable, "-m", "django",
                        "runserver", f"127.0.0.1:{port}",
                        f"--settings={module_name}"
                    ], env=env)
            else:
                logger.error(f"Unknown framework '{framework}'")
                self.tunnel.stop()
                sys.exit(1)

        except KeyboardInterrupt:
            self.tunnel.stop()
            logger.info("GlobalHost safely shut down.")
        except Exception as e:
            self.tunnel.stop()
            logger.error(f"GlobalHost unexpected crash: {e}")
            sys.exit(1)
