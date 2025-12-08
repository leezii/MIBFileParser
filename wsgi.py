"""WSGI entry point for the Flask application."""

from src.flask_app.app import create_app

# Create the Flask application instance
app = create_app()