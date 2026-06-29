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

        # Register OS signals for bulletproof cleanup
        self._register_signal_handlers()

    def _register_signal_handlers(self):
        """Registers OS signals to ensure the tunnel and server are killed on exit."""
        signals_to_catch = [
            signal.SIGINT,   # Ctrl+C
            signal.SIGTERM,  # Standard termination (e.g., 'kill' or system shutdown)
        ]

        # Unix-specific signals (Windows doesn't have these)
        if hasattr(signal, 'SIGHUP'):
            signals_to_catch.append(signal.SIGHUP)   # Terminal window closed
        if hasattr(signal, 'SIGTSTP'):
            signals_to_catch.append(signal.SIGTSTP)  # Ctrl+Z (Suspend)

        for sig in signals_to_catch:
            try:
                # Only the main thread can register signal handlers
                signal.signal(sig, self._handle_shutdown_signal)
            except (ValueError, OSError):
                pass

    def _handle_shutdown_signal(self, signum, frame):
        """Triggered by the OS. Cleans up resources and exits immediately."""
        sig_name = signal.Signals(signum).name
        logger.info(f"Received {sig_name}. Initiating graceful shutdown...")
        self.stop()
        sys.exit(0)

    def _get_framework_cmd(self, framework: str, app: str, port: int):
        """Determines the command, working directory, and environment for the framework."""
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

                # CRITICAL FIX: Run the script directly instead of using --settings
                cmd = [
                    sys.executable, os.path.abspath(app),
                    "runserver", f"127.0.0.1:{port}"
                ]
                return cmd, None, env

        elif framework == "flask":
            env = os.environ.copy()
            if app:
                env["FLASK_APP"] = app
            cmd = [sys.executable, "-m", "flask", "run", "--host", "127.0.0.1", "--port", str(port)]
            return cmd, None, env

        elif framework == "streamlit":
            env = os.environ.copy()
            # Disable Streamlit's email prompt and usage stats
            env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
            cmd = [
                sys.executable, "-m", "streamlit", "run", app,
                "--server.address", "127.0.0.1",
                "--server.port", str(port),
                "--server.headless", "true"
            ]
            return cmd, None, env

        else:
            logger.error(f"Unsupported framework specified: '{framework}'")
            return None, None, None

    def _start_process(self, cmd, cwd, env):
        """Executes the framework command and logs the details."""
        logger.debug(f"Executing command: {' '.join(cmd)}")
        return subprocess.Popen(cmd, cwd=cwd, env=env)

    def launch(self, framework: str, app: str, port: int = 8000):
        """Starts the tunnel and runs the framework in the foreground."""
        try:
            self.url = self.tunnel.start(port=port)
            logger.info(f"Public URL assigned: {self.url}")
            logger.info(f"Starting {framework} server on port {port}...")

            cmd, cwd, env = self._get_framework_cmd(framework, app, port)
            if not cmd:
                self.tunnel.stop()
                sys.exit(1)

            # For foreground, we use subprocess.run to block
            subprocess.run(cmd, cwd=cwd, env=env)

        except KeyboardInterrupt:
            # Fallback in case the signal handler is overridden by the user's script
            self.stop()
            logger.info("GlobalHost shut down by user.")
        except Exception as e:
            self.stop()
            logger.error(f"GlobalHost crashed: {e}")
            sys.exit(1)

    def bg_launch(self, framework: str, app: str, port: int = 8000):
        """Starts the tunnel and runs the framework in the background."""
        try:
            self.url = self.tunnel.start(port=port)
            logger.info(f"Public URL assigned: {self.url}")
            logger.info(f"Starting {framework} server in background on port {port}...")

            cmd, cwd, env = self._get_framework_cmd(framework, app, port)
            if not cmd:
                self.tunnel.stop()
                return False

            self.process = self._start_process(cmd, cwd, env)

            # Give the server a moment to start. If it crashes immediately
            # (e.g., "address already in use"), we need to catch it here.
            time.sleep(1.5)

            if self.process.poll() is not None:
                logger.error(f"Framework process exited immediately with code {self.process.returncode}.")
                logger.error("This usually means the port is already in use or there is a configuration error.")
                self.stop()
                return False

            logger.info(f"Framework running in background (PID: {self.process.pid}).")
            return True

        except Exception as e:
            # CRITICAL: If an error occurs, the spawned process might be left running.
            if self.process:
                logger.debug("Cleaning up orphaned background process due to launch error.")
                self.process.kill()
                self.process = None

            self.tunnel.stop()
            logger.error(f"Failed to start GlobalHost in background: {e}")
            return False

    def stop(self):
        """Terminates the background framework process and closes the tunnel."""
        # Kill framework process first
        if self.process:
            logger.debug("Terminating background framework process.")
            try:
                # Try to kill the entire process group
                os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass
            self.process = None

        # Always kill the tunnel
        if self.tunnel:
            logger.debug("Closing tunnel.")
            self.tunnel.stop()

        self.url = None
        logger.info("GlobalHost shut down successfully.")

    def get_url(self):
        """Returns the current public URL."""
        return self.url
