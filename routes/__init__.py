"""Route blueprints for the Power BI Analysis Tool."""

from routes.main import main_bp
from routes.analysis import analysis_bp
from routes.insights import insights_bp
from routes.sources import sources_bp
from routes.api import api_bp

__all__ = ['main_bp', 'analysis_bp', 'insights_bp', 'sources_bp', 'api_bp']
