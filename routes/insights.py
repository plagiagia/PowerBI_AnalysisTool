"""Insights routes blueprint - model and report insights."""

from typing import Any, Dict

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
    annotations = mp.get_annotations()
    annotation_items = [{'name': key, 'value': value} for key, value in sorted(annotations.items())]

    column_count = sum(len(table.get('columns', [])) for table in tables)
    hidden_table_count = sum(1 for table in tables if table.get('isHidden'))
    hidden_column_count = sum(
        1 for table in tables
        for column in table.get('columns', [])
        if column.get('isHidden')
    )

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

    column_gaps = [
        {
            'table': table.get('name'),
            'name': column.get('name'),
            'data_type': column.get('dataType'),
            'data_category': column.get('dataCategory'),
            'is_hidden': column.get('isHidden', False)
        }
        for table in tables
        for column in table.get('columns', [])
        if not (column.get('dataCategory') or '').strip()
    ]

    model_summary = {
        'table_count': len(tables),
        'column_count': column_count,
        'measure_count': len(measures),
        'relationship_count': len(relationships),
        'role_count': len(roles),
        'annotations_count': len(annotation_items),
        'hidden_table_count': hidden_table_count,
        'hidden_column_count': hidden_column_count,
        'measures_without_description': sum(1 for item in measure_gaps if item['missing_description']),
        'measures_without_format': sum(1 for item in measure_gaps if item['missing_format']),
        'columns_without_category': len(column_gaps)
    }

    return render_template(
        'model_insights.html',
        metrics=metrics,
        model_summary=model_summary,
        tables=tables,
        relationships=relationships,
        roles=roles,
        annotation_items=annotation_items,
        measure_gaps=sorted(measure_gaps, key=lambda item: ((item['table'] or ''), item['name'] or '')),
        column_gaps=sorted(column_gaps, key=lambda item: ((item['table'] or ''), item['name'] or ''))
    )


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

    report_summary = {
        'bookmark_count': len(bookmarks),
        'navigation_count': len(navigation_items),
        'layout_count': len(layout_records),
        'query_with_order': sum(1 for entry in query_details if entry['order_by']),
        'query_with_filters': sum(1 for entry in query_details if entry['where']),
        'formatting_custom_count': len(formatting_highlights),
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
