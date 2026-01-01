"""
Flask application for MIB tree visualization.
"""

from flask import Flask, request
from flask_cors import CORS
import os
import sys
from pathlib import Path


def get_bundle_dir():
    """
    Get the base directory for resource files.

    In PyInstaller bundles, this returns sys._MEIPASS.
    In development, this returns the project root.
    """
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        return Path(sys._MEIPASS)
    else:
        # Running in development
        return Path(__file__).parent.parent.parent


def create_app(config_name='development'):
    """Application factory pattern."""
    # Determine base directory for templates and static files
    bundle_dir = get_bundle_dir()

    # For PyInstaller bundles, we need to set template and static folder paths
    if getattr(sys, 'frozen', False):
        # In PyInstaller bundle, resources are in sys._MEIPASS
        template_folder = bundle_dir / 'src' / 'flask_app' / 'templates'
        static_folder = bundle_dir / 'src' / 'flask_app' / 'static'
        app = Flask(__name__, template_folder=str(template_folder), static_folder=str(static_folder))
    else:
        # In development, use default paths
        app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Set output and MIB directories based on environment
    if getattr(sys, 'frozen', False):
        # In PyInstaller bundle, use user home directory for all writable data
        output_dir = Path.home() / '.mibparser' / 'output'
        mib_dir = Path.home() / '.mibparser' / 'mib'
        storage_dir = Path.home() / '.mibparser' / 'storage'

        # Copy storage files from bundle to user directory if needed
        bundle_storage = bundle_dir / 'storage'
        if bundle_storage.exists() and not storage_dir.exists():
            import shutil
            shutil.copytree(bundle_storage, storage_dir)
    else:
        # In development, use project directories
        output_dir = Path(__file__).parent.parent.parent / 'output'
        mib_dir = Path(__file__).parent.parent.parent / 'MIB'
        storage_dir = Path(__file__).parent.parent.parent / 'storage'

    # Create directories if they don't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    mib_dir.mkdir(parents=True, exist_ok=True)
    storage_dir.mkdir(parents=True, exist_ok=True)

    app.config['OUTPUT_DIR'] = output_dir
    app.config['MIB_DIR'] = mib_dir
    app.config['STORAGE_DIR'] = storage_dir
    app.config['JSON_SORT_KEYS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload size

    # Static file cache configuration
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year for production

    # Enable CORS for all routes
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/*": {"origins": "*"}
    })

    # Register blueprints
    from .routes.main import main_bp
    from .routes.api import api_bp
    from .routes.upload import upload_bp
    from .routes.oid_lookup import oid_lookup_bp
    from .routes.annotation import annotation_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(upload_bp)
    app.register_blueprint(oid_lookup_bp)
    app.register_blueprint(annotation_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Resource not found'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500

    @app.errorhandler(FileNotFoundError)
    def file_not_found_error(error):
        return {'error': 'File not found'}, 404

    # Add cache headers for static files
    @app.after_request
    def add_cache_headers(response):
        if request.endpoint and 'static' in request.endpoint:
            # Long cache for vendor assets (1 year)
            if 'vendor' in request.path:
                response.cache_control.max_age = 31536000
                response.cache_control.immutable = True
            # Shorter cache for custom static files (1 hour)
            else:
                response.cache_control.max_age = 3600
        return response

    return app


if __name__ == '__main__':
    app = create_app()
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 8080))
    app.run(debug=True, host=host, port=port)