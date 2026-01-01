"""Main routes blueprint - dashboard and index."""

import datetime

from flask import Blueprint, render_template

from utils.processors import get_report_metrics

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index() -> str:
    """Render the dashboard with report metrics."""
    metrics = get_report_metrics()
    time_loaded = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")

    return render_template(
        'index.html',
        metrics=metrics,
        time_loaded=time_loaded,
        most_common_visual=metrics.get("most_common_visual")
    )
