"""
Power BI Analysis Tool - Flask Application Factory

A web application for analyzing Power BI reports and models.
"""

import datetime
import json
import logging
import os
from typing import Optional

from flask import Flask, g, render_template

from config import get_config


def configure_logging(app: Flask) -> None:
    """Configure application logging."""
    log_level = logging.DEBUG if app.config.get('DEBUG') else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    app.logger.setLevel(log_level)


def register_blueprints(app: Flask) -> None:
    """Register all application blueprints."""
    from routes import main_bp, analysis_bp, insights_bp, sources_bp, api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(insights_bp)
    app.register_blueprint(sources_bp)
    app.register_blueprint(api_bp)


def register_error_handlers(app: Flask) -> None:
    """Register error handlers."""

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error=e.description, code=404), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html', error=e.description, code=500), 500


def register_context_processors(app: Flask) -> None:
    """Register template context processors."""

    def get_report_name() -> str:
        """Extract the report name from the report file."""
        report_path = app.config['REPORT_JSON_PATH']
        report_name = os.path.basename(report_path).replace(".json", "")

        try:
            with open(report_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if 'name' in data:
                    report_name = data['name']
        except (json.JSONDecodeError, IOError, KeyError) as e:
            app.logger.warning(f"Could not read report name from file: {e}")

        return report_name

    @app.context_processor
    def inject_common_data():
        """Inject common data into templates."""
        return {
            "current_year": datetime.datetime.now().year,
            "report_name": get_report_name(),
            "app_name": app.config.get('APP_NAME', 'Power BI Analysis Tool'),
            "app_version": app.config.get('APP_VERSION', '1.0.0'),
            "app_author": app.config.get('APP_AUTHOR', '')
        }


def register_teardown(app: Flask) -> None:
    """Register teardown handlers."""

    @app.teardown_appcontext
    def teardown(exception: Optional[BaseException] = None) -> None:
        """Clean up resources stored in g."""
        g.pop('data_processor', None)
        g.pop('lineage_view_processor', None)
        g.pop('model_processor', None)


def register_security_headers(app: Flask) -> None:
    """Register security headers middleware."""

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response


def create_app(config_object=None) -> Flask:
    """
    Application factory for creating the Flask app.

    Args:
        config_object: Optional configuration object. If None, uses get_config().

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # Load configuration
    if config_object is None:
        config_object = get_config()

    app.config.from_object(config_object)

    # Configure logging
    configure_logging(app)

    # Register components
    register_security_headers(app)
    register_teardown(app)
    register_context_processors(app)
    register_blueprints(app)
    register_error_handlers(app)

    app.logger.info(f"Application created with config: {config_object.__class__.__name__}")

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=app.config.get('DEBUG', True))
