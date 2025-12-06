"""
Flask application for MIB tree visualization.
"""

from flask import Flask
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

    # Enable CORS for all routes
    CORS(app, resources={
        r"/api/*": {"origins": "*"},
        r"/*": {"origins": "*"}
    })

    # Register blueprints
    from .routes.main import main_bp
    from .routes.api import api_bp
    from .routes.upload import upload_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(upload_bp)

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

    return app


if __name__ == '__main__':
    app = create_app()
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 8080))
    app.run(debug=True, host=host, port=port)