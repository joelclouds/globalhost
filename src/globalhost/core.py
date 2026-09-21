import sys
import os
import subprocess
import time
import signal
import logging
from .tunnel import TunnelManager

logger = logging.getLogger("globalhost")

class GlobalHostApp:
    def __init__(self):
        self.tunnel = TunnelManager()
        self.url = None
        self.process = None
        self._register_signal_handlers()

    def _register_signal_handlers(self):
        signals_to_catch = [signal.SIGINT, signal.SIGTERM]
        if hasattr(signal, 'SIGHUP'):
            signals_to_catch.append(signal.SIGHUP)
        if hasattr(signal, 'SIGTSTP'):
            signals_to_catch.append(signal.SIGTSTP)

        for sig in signals_to_catch:
            try:
                signal.signal(sig, self._handle_shutdown_signal)
            except (ValueError, OSError):
                pass

    def _handle_shutdown_signal(self, signum, frame):
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}. Initiating graceful shutdown...")
        self.stop()
        sys.exit(0)

    def _get_framework_cmd(self, framework: str, app: str, port: int):
        framework = framework.lower()
        if framework == "fastapi":
            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            cmd = [sys.executable, "-m", "uvicorn", app, "--host", "127.0.0.1", "--port", str(port)]
            return cmd, script_dir, None
        elif framework == "django":
            if os.path.exists("manage.py"):
                cmd = [sys.executable, "manage.py", "runserver", f"127.0.0.1:{port}"]
                return cmd, None, None
            else:
                logger.debug("manage.py not found. Initializing Django in standalone mode.")
                clean_app = app.replace("\\", "/").rstrip(".py")
                if "/" in clean_app:
                    module_dir = os.path.dirname(os.path.abspath(clean_app))
                else:
                    module_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                env = os.environ.copy()
                env["PYTHONPATH"] = module_dir + os.pathsep + env.get("PYTHONPATH", "")
                cmd = [sys.executable, os.path.abspath(app), "runserver", f"127.0.0.1:{port}"]
                return cmd, None, env
        elif framework == "flask":
            env = os.environ.copy()
            if app:
                env["FLASK_APP"] = app
            cmd = [sys.executable, "-m", "flask", "run", "--host", "127.0.0.1", "--port", str(port)]
            return cmd, None, env
        elif framework == "streamlit":
            env = os.environ.copy()
            env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
            cmd = [sys.executable, "-m", "streamlit", "run", app, "--server.address", "127.0.0.1", "--server.port", str(port), "--server.headless", "true"]
            return cmd, None, env
        else:
            logger.error(f"Unsupported framework specified: '{framework}'")
            return None, None, None

    def _start_process(self, cmd, cwd, env):
        logger.debug(f"Executing command: {' '.join(cmd)}")
        return subprocess.Popen(cmd, cwd=cwd, env=env)

    def launch(self, framework: str, app: str, port: int = 8000, token: str | None = None):
        try:
            self.url = self.tunnel.start(port=port, token=token)
            logger.info(f"Public URL assigned: {self.url}")
            logger.info(f"Starting {framework} server on port {port}...")
            cmd, cwd, env = self._get_framework_cmd(framework, app, port)
            if not cmd:
                self.tunnel.stop()
                sys.exit(1)
            subprocess.run(cmd, cwd=cwd, env=env)
        except KeyboardInterrupt:
            self.stop()
            logger.info("GlobalHost shut down by user.")
        except Exception as e:
            self.stop()
            logger.error(f"GlobalHost crashed: {e}")
            sys.exit(1)

    def bg_launch(self, framework: str, app: str, port: int = 8000, token: str | None = None):
        try:
            self.url = self.tunnel.start(port=port, token=token)
            logger.info(f"Public URL assigned: {self.url}")
            logger.info(f"Starting {framework} server in background on port {port}...")
            cmd, cwd, env = self._get_framework_cmd(framework, app, port)
            if not cmd:
                self.tunnel.stop()
                return False
            self.process = self._start_process(cmd, cwd, env)
            time.sleep(1.5)
            if self.process.poll() is not None:
                logger.error(f"Framework process exited immediately with code {self.process.returncode}.")
                logger.error("This usually means the port is already in use or there is a configuration error.")
                self.stop()
                return False
            logger.info(f"Framework running in background (PID: {self.process.pid}).")
            return True
        except Exception as e:
            if self.process:
                logger.debug("Cleaning up orphaned background process due to launch error.")
                self.process.kill()
                self.process = None
            self.tunnel.stop()
            logger.error(f"Failed to start GlobalHost in background: {e}")
            return False

    def stop(self):
        if self.process:
            logger.debug("Terminating background framework process.")
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass
            self.process = None
        if self.tunnel:
            logger.debug("Closing tunnel.")
            self.tunnel.stop()
        self.url = None
        logger.info("GlobalHost shut down successfully.")

    def get_url(self):
        return self.url
