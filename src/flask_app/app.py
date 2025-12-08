"""
Flask application for MIB tree visualization.
"""

from flask import Flask, request
from flask_cors import CORS
import os
from pathlib import Path


def create_app(config_name='development'):
    """Application factory pattern."""
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['OUTPUT_DIR'] = Path(__file__).parent.parent.parent / 'output'
    app.config['MIB_DIR'] = Path(__file__).parent.parent.parent / 'MIB'
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