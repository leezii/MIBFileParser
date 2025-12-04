#!/usr/bin/env python3
"""
Flask application launcher for MIB Viewer.
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def main():
    """Run the Flask application."""
    from flask_app.app import create_app

    # Create Flask app
    app = create_app()

    # Get configuration
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

    print(f"Starting MIB Viewer on http://{host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Output directory: {app.config.get('OUTPUT_DIR')}")

    # Run the app
    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\nShutting down MIB Viewer...")
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())