"""Insights routes blueprint - model and report insights."""

from typing import Any, Dict, List

from flask import Blueprint, abort, current_app, render_template

from utils.processors import (
    get_data_processor,
    get_model_processor,
    get_report_metrics,
)

insights_bp = Blueprint('insights', __name__)


@insights_bp.route('/model-insights')
def model_insights() -> str:
    """Render the model insights page."""
    if not current_app.config.get('ENABLE_MODEL_INSIGHTS', True):
        abort(404, description="This feature is currently disabled.")

    mp = get_model_processor()
    metrics = get_report_metrics()

    tables = sorted(mp.get_tables(), key=lambda item: (item.get('name') or '').lower())
    measures = mp.get_measures()
    relationships = sorted(
        mp.get_relationships(),
        key=lambda item: ((item.get('fromTable') or '').lower(), (item.get('toTable') or '').lower())
    )
    roles = sorted(mp.get_roles(), key=lambda item: (item.get('name') or '').lower())

    column_count = sum(len(table.get('columns', [])) for table in tables)
    hidden_table_count = sum(1 for table in tables if table.get('isHidden'))
    hidden_column_count = sum(
        1 for table in tables
        for column in table.get('columns', [])
        if column.get('isHidden')
    )
    hidden_measure_count = sum(1 for m in measures if m.get('isHidden'))

    # Measures missing descriptions or format strings
    measure_gaps = [
        {
            'table': measure.get('table'),
            'name': measure.get('name'),
            'missing_format': not (measure.get('formatString') or '').strip(),
            'missing_description': not (measure.get('description') or '').strip(),
            'display_folder': measure.get('displayFolder'),
            'is_hidden': measure.get('isHidden', False)
        }
        for measure in measures
        if not (measure.get('formatString') or '').strip() or not (measure.get('description') or '').strip()
    ]

    model_summary = {
        'table_count': len(tables),
        'column_count': column_count,
        'measure_count': len(measures),
        'relationship_count': len(relationships),
        'role_count': len(roles),
        'hidden_table_count': hidden_table_count,
        'hidden_column_count': hidden_column_count,
        'hidden_measure_count': hidden_measure_count,
        'measures_without_description': sum(1 for item in measure_gaps if item['missing_description']),
        'measures_without_format': sum(1 for item in measure_gaps if item['missing_format']),
    }

    return render_template(
        'model_insights.html',
        metrics=metrics,
        model_summary=model_summary,
        tables=tables,
        relationships=relationships,
        roles=roles,
        measure_gaps=sorted(measure_gaps, key=lambda item: ((item['table'] or ''), item['name'] or '')),
    )


@insights_bp.route('/report-insights')
def report_insights() -> str:
    """Render the report insights page - focused on actionable info."""
    if not current_app.config.get('ENABLE_REPORT_INSIGHTS', True):
        abort(404, description="This feature is currently disabled.")

    dp = get_data_processor()
    metrics = get_report_metrics()

    # Only keep useful information
    theme_info = dp.get_theme_info()
    bookmarks = dp.get_bookmarks()
    navigation_items = dp.get_navigation_items()

    # Navigation summary
    navigation_counts: Dict[str, int] = {}
    for item in navigation_items:
        nav_type = item.get('visual_type') or 'Unknown'
        navigation_counts[nav_type] = navigation_counts.get(nav_type, 0) + 1

    navigation_summary = sorted(
        [{'visual_type': key, 'count': value} for key, value in navigation_counts.items()],
        key=lambda item: item['visual_type'].lower()
    )

    bookmark_metrics = {
        'count': len(bookmarks),
        'filters': sum(bookmark['filter_count'] for bookmark in bookmarks),
        'targets': sum(len(bookmark['target_visuals']) for bookmark in bookmarks)
    }

    report_summary = {
        'bookmark_count': len(bookmarks),
        'navigation_count': len(navigation_items),
        'theme_name': theme_info.get('customTheme', {}).get('name')
            or theme_info.get('baseTheme', {}).get('name')
            or 'Default'
    }

    return render_template(
        'report_insights.html',
        metrics=metrics,
        theme_info=theme_info,
        bookmarks=bookmarks,
        bookmark_metrics=bookmark_metrics,
        navigation_items=sorted(
            navigation_items,
            key=lambda item: ((item.get('page') or ''), item.get('visual_name') or '')
        ),
        navigation_summary=navigation_summary,
        report_summary=report_summary
    )
