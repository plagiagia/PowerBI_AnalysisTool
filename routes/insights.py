"""Insights routes blueprint - report insights."""

from typing import Any, Dict

from flask import Blueprint, abort, current_app, render_template

from utils.processors import (
    get_data_processor,
    get_report_metrics,
)

insights_bp = Blueprint('insights', __name__)


@insights_bp.route('/report-insights')
def report_insights() -> str:
    """Render the report insights page."""
    if not current_app.config.get('ENABLE_REPORT_INSIGHTS', True):
        abort(404, description="This feature is currently disabled.")

    dp = get_data_processor()
    metrics = get_report_metrics()

    theme_info = dp.get_theme_info()
    bookmarks = dp.get_bookmarks()
    layout_records = dp.get_visual_layouts()
    query_details = dp.get_visual_queries()
    formatting_details = dp.get_visual_formatting()
    navigation_items = dp.get_navigation_items()

    layout_by_page: Dict[str, Dict[str, Any]] = {}
    for entry in layout_records:
        page = entry.get('page') or 'Unknown'
        page_metrics = layout_by_page.setdefault(page, {
            'page': page,
            'visual_count': 0,
            'total_width': 0.0,
            'total_height': 0.0,
            'max_z': 0.0
        })
        page_metrics['visual_count'] += 1

        width = entry.get('width')
        height = entry.get('height')
        depth = entry.get('z')

        if isinstance(width, (int, float)):
            page_metrics['total_width'] += float(width)
        if isinstance(height, (int, float)):
            page_metrics['total_height'] += float(height)
        if isinstance(depth, (int, float)):
            page_metrics['max_z'] = max(page_metrics['max_z'], float(depth))

    for entry in layout_by_page.values():
        count = entry['visual_count'] or 1
        entry['avg_width'] = round(entry['total_width'] / count, 2) if entry['total_width'] else 0
        entry['avg_height'] = round(entry['total_height'] / count, 2) if entry['total_height'] else 0

    layout_summary = sorted(layout_by_page.values(), key=lambda item: item['page'].lower())
    sorted_layout_records = sorted(
        layout_records,
        key=lambda item: ((item.get('page') or ''), item.get('visual_name') or '')
    )
    sorted_query_details = sorted(
        query_details,
        key=lambda item: ((item.get('page') or ''), item.get('visual_name') or '')
    )

    formatting_highlights = [
        entry for entry in formatting_details
        if entry['has_custom_tooltip'] or entry['has_custom_title'] or entry['has_background']
        or entry['has_border'] or entry['has_drop_shadow']
    ]

    formatting_stats = {
        'custom_tooltip': sum(1 for entry in formatting_details if entry['has_custom_tooltip']),
        'custom_title': sum(1 for entry in formatting_details if entry['has_custom_title']),
        'custom_background': sum(1 for entry in formatting_details if entry['has_background']),
        'custom_border': sum(1 for entry in formatting_details if entry['has_border']),
        'drop_shadow': sum(1 for entry in formatting_details if entry['has_drop_shadow'])
    }

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
    custom_theme = theme_info.get('customTheme') or {}
    base_theme = theme_info.get('baseTheme') or {}

    report_summary = {
        'bookmark_count': len(bookmarks),
        'navigation_count': len(navigation_items),
        'layout_count': len(layout_records),
        'query_with_order': sum(1 for entry in query_details if entry['order_by']),
        'query_with_filters': sum(1 for entry in query_details if entry['where']),
        'formatting_custom_count': len(formatting_highlights),
        'theme_name': custom_theme.get('name')
            or base_theme.get('name')
            or 'Default'
    }

    return render_template(
        'report_insights.html',
        metrics=metrics,
        theme_info=theme_info,
        bookmarks=bookmarks,
        bookmark_metrics=bookmark_metrics,
        layout_summary=layout_summary,
        layout_records=sorted_layout_records,
        query_details=sorted_query_details,
        formatting_stats=formatting_stats,
        formatting_highlights=sorted(
            formatting_highlights,
            key=lambda item: ((item.get('page') or ''), item.get('visual_name') or '')
        ),
        navigation_items=sorted(
            navigation_items,
            key=lambda item: ((item.get('page') or ''), item.get('visual_name') or '')
        ),
        navigation_summary=navigation_summary,
        report_summary=report_summary
    )
