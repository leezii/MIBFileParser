"""
Desktop application launcher for MIB Parser using PyWebView.

This script starts the Flask application in a background thread and
creates a native desktop window using the system's WebView.
"""
import webview
import threading
import time
import sys
import socket
import logging
from pathlib import Path
from typing import Dict, Any

# Add project root to Python path
if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle
    # Set working directory to the bundle's Resources directory
    RESOURCE_DIR = Path(sys._MEIPASS)
    PROJECT_ROOT = RESOURCE_DIR.parent
else:
    # Running in development
    PROJECT_ROOT = Path(__file__).parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
import tempfile

# Create log file in temp directory
if getattr(sys, 'frozen', False):
    log_file = Path.home() / '.mibparser' / 'desktop.log'
    log_file.parent.mkdir(parents=True, exist_ok=True)
else:
    log_file = Path(__file__).parent / 'desktop.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info(f'Log file: {log_file}')
logger.info(f'Working directory: {Path.cwd()}')
logger.info(f'Executable: {sys.executable}')
logger.info(f'Frozen: {getattr(sys, "frozen", False)}')
if getattr(sys, 'frozen', False):
    logger.info(f'MEIPASS: {sys._MEIPASS}')


def find_available_port(start_port: int = 49152, end_port: int = 65535) -> int:
    """
    Find an available port on localhost.

    Args:
        start_port: Starting port number (default: 49152, dynamic/private port range)
        end_port: Ending port number (default: 65535)

    Returns:
        Available port number
    """
    for port in range(start_port, end_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise OSError("No available ports found")


class DesktopAPI:
    """
    API exposed to the frontend via PyWebView's JavaScript bridge.

    This class provides methods that can be called from the web frontend
    to access desktop-specific features.
    """

    def get_app_info(self) -> Dict[str, Any]:
        """
        Get application information.

        Returns:
            Dict containing app version, platform, and mode info
        """
        return {
            'version': '1.0.0',
            'platform': webview.platform,
            'desktop_mode': True,
            'python_version': f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'
        }

    def select_file(self) -> list[str] | None:
        """
        Open native file dialog for selecting MIB files.

        Returns:
            List of selected file paths, or None if cancelled
        """
        try:
            result = webview.windows[0].create_file_dialog(
                webview.OPEN_DIALOG,
                file_types=(
                    'MIB Files (*.mib)',
                    'MY Files (*.my)',
                    'Text Files (*.txt)',
                    'All Files (*.*)'
                ),
                allow_multiple=True
            )
            if result:
                logger.info(f'User selected {len(result)} file(s)')
            return result
        except Exception as e:
            logger.error(f'File dialog error: {e}')
            return None

    def show_notification(self, title: str, message: str) -> None:
        """
        Display a system notification.

        Args:
            title: Notification title
            message: Notification message body
        """
        try:
            # Get the main window
            if webview.windows:
                window = webview.windows[0]
                # PyWebView's notification support varies by platform
                # This is a basic implementation
                logger.info(f'Notification: {title} - {message}')
                # Note: Full notification support depends on platform
        except Exception as e:
            logger.error(f'Notification error: {e}')


def start_flask(host: str = '127.0.0.1', port: int = 5000) -> None:
    """
    Start Flask application in a background thread.

    Args:
        host: Flask host (default: 127.0.0.1)
        port: Flask port (default: 5000)
    """
    try:
        # Import Flask app here to avoid import errors in packaged app
        logger.info('Importing Flask app...')
        from src.flask_app.app import create_app

        logger.info('Creating Flask app instance...')
        app = create_app()

        logger.info(f'Starting Flask server on {host}:{port}...')
        # Run Flask without reloader (reloader doesn't work in threads)
        app.run(
            host=host,
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        logger.error(f'Flask startup error: {e}', exc_info=True)
        raise


def main() -> None:
    """
    Main entry point for desktop application.

    Orchestrates the startup sequence:
    1. Find an available port
    2. Start Flask in background thread
    3. Wait for Flask to initialize
    4. Create PyWebView window
    5. Start PyWebView event loop
    """
    # Find available port dynamically
    logger.info('Finding available port...')
    try:
        FLASK_PORT = find_available_port()
        logger.info(f'Found available port: {FLASK_PORT}')
    except OSError as e:
        logger.error(f'Failed to find available port: {e}')
        sys.exit(1)

    FLASK_HOST = '127.0.0.1'
    FLASK_URL = f'http://{FLASK_HOST}:{FLASK_PORT}'

    logger.info('Starting MIB Parser Desktop Application...')

    # Start Flask in background thread
    logger.info(f'Starting Flask server on {FLASK_URL}...')
    logger.info(f'Using dynamically allocated port: {FLASK_PORT}')
    flask_thread = threading.Thread(
        target=start_flask,
        args=(FLASK_HOST, FLASK_PORT),
        daemon=True  # Daemon thread will exit when main thread exits
    )
    flask_thread.start()

    # Wait for Flask to initialize
    # In production, you might want to add a health check endpoint
    logger.info('Waiting for Flask to initialize...')
    time.sleep(2)

    # Create desktop window
    logger.info('Creating desktop window...')

    api = DesktopAPI()

    window = webview.create_window(
        title='MIB Parser & Viewer',
        url=FLASK_URL,
        js_api=api,
        width=1400,
        height=900,
        min_size=(1000, 600),
        resizable=True,
        fullscreen=False,
        # Note: icon parameter will be added after creating icon files
        # icon=str(PROJECT_ROOT / 'desktop' / 'icons' / 'icon.png'),
    )

    logger.info('Desktop application started successfully')
    # Note: Platform info will be available after webview.start()
    logger.info('Press Ctrl+C to exit (or close the window)')

    # Start PyWebView event loop (blocking call)
    try:
        webview.start(debug=False)
    except KeyboardInterrupt:
        logger.info('Application interrupted by user')
    except Exception as e:
        logger.error(f'Application error: {e}')
        raise
    finally:
        logger.info('Application shutdown complete')


if __name__ == '__main__':
    main()
