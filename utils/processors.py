"""Processor utilities for data, lineage, and model processing."""

import collections
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from flask import abort, current_app, g

from data_processor import DataProcessor
from lineage_view import LineageView
from model_processor import ModelProcessor

# Application-level cache for expensive processors
_app_cache: Dict[str, Any] = {
    'lineage': None,
    'lineage_mtime': 0.0,
    'data': None,
    'data_mtime': 0.0,
    'model': None,
    'model_mtime': 0.0,
}


def _get_file_mtime(path: str) -> float:
    """Get file modification time, returns 0 if file doesn't exist."""
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0.0


def get_data_processor() -> DataProcessor:
    """Retrieve or create the DataProcessor instance with app-level caching."""
    report_path = current_app.config['REPORT_JSON_PATH']

    if not os.path.exists(report_path):
        current_app.logger.error(f"Report JSON file not found: {report_path}")
        abort(500, description="Report data file not found. Please check your data directory.")

    current_mtime = _get_file_mtime(report_path)

    # Check if cache is valid
    if _app_cache['data'] is not None and _app_cache['data_mtime'] == current_mtime:
        return _app_cache['data']

    # Rebuild cache
    dp = DataProcessor(report_path)
    dp.process_json()
    _app_cache['data'] = dp
    _app_cache['data_mtime'] = current_mtime
    current_app.logger.debug(f"DataProcessor cache rebuilt for {report_path}")
    return dp


def get_lineage_view_processor() -> LineageView:
    """Retrieve or create the LineageView instance with app-level caching."""
    tsv_path = current_app.config['MEASURE_DEPENDENCIES_TSV_PATH']

    if not os.path.exists(tsv_path):
        current_app.logger.error(f"Lineage TSV file not found: {tsv_path}")
        abort(500, description="Lineage data file not found. Please check your data directory.")

    current_mtime = _get_file_mtime(tsv_path)

    # Check if cache is valid
    if _app_cache['lineage'] is not None and _app_cache['lineage_mtime'] == current_mtime:
        return _app_cache['lineage']

    # Rebuild cache
    lvp = LineageView(tsv_path)
    lvp.process_lineage_data()
    _app_cache['lineage'] = lvp
    _app_cache['lineage_mtime'] = current_mtime
    current_app.logger.debug(f"LineageView cache rebuilt for {tsv_path}")
    return lvp


def get_model_processor() -> ModelProcessor:
    """Retrieve or create the ModelProcessor instance with app-level caching."""
    model_path = current_app.config['MODEL_JSON_PATH']

    if not os.path.exists(model_path):
        current_app.logger.error(f"Model JSON file not found: {model_path}")
        abort(500, description="Model data file not found. Please check your data directory.")

    current_mtime = _get_file_mtime(model_path)

    # Check if cache is valid
    if _app_cache['model'] is not None and _app_cache['model_mtime'] == current_mtime:
        return _app_cache['model']

    # Rebuild cache
    mp = ModelProcessor(model_path)
    mp.load()
    _app_cache['model'] = mp
    _app_cache['model_mtime'] = current_mtime
    current_app.logger.debug(f"ModelProcessor cache rebuilt for {model_path}")
    return mp


def load_model_data(model_json_path: str) -> Dict[str, Any]:
    """Load model data from a JSON file."""
    try:
        with open(model_json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except (json.JSONDecodeError, IOError) as e:
        current_app.logger.error(f"Error reading or parsing the model JSON file: {e}")
        abort(500, description="Error loading model data.")


def extract_m_queries(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Extract M queries from the model data.

    Returns a list of dictionaries with keys 'table_name' and 'm_query'.
    """
    m_queries_info: List[Dict[str, str]] = []
    model = data.get('model', {})

    def process_query(name: str, expression_list: List[str]) -> None:
        """Process a query if it starts with 'let'"""
        m_query = '\n'.join(expression_list)
        if m_query.strip().lower().startswith('let'):
            m_queries_info.append({
                'table_name': name,
                'm_query': m_query
            })

    # Process tables
    for table in model.get('tables', []):
        table_name = table.get('name', '')
        for partition in table.get('partitions', []):
            source = partition.get('source', {})
            if source.get('type') == 'm':
                process_query(table_name, source.get('expression', []))

    # Process expressions
    for expression in model.get('expressions', []):
        if expression.get('kind') == 'm':
            process_query(expression.get('name', ''), expression.get('expression', []))

    return m_queries_info


def get_report_metrics() -> Dict[str, Any]:
    """Get metrics about the report for the dashboard."""
    dp = get_data_processor()
    lvp = get_lineage_view_processor()
    mp = get_model_processor()

    excluded_types = {"Page Level Filters", "Global Level Filters"}
    valid_visuals = [
        row for row in dp.visuals_data
        if len(row) > 3 and row[3] and row[1] and row[1] not in excluded_types
    ]

    visual_types = [row[1] for row in valid_visuals]
    visual_count = len(visual_types)
    counter = collections.Counter(visual_types)
    most_common_visual = counter.most_common(1)[0][0] if counter else "None"
    visual_distribution = counter.most_common(5)

    unique_pages = {row[0] for row in dp.visuals_data if row and row[0]}

    all_measures = lvp.get_all_measures()
    used_measures = dp.get_used_measures(all_measures)
    used_measures = lvp.expand_used_measures(used_measures)
    final_measures = lvp.get_final_measures()
    unused_analysis = lvp.get_comprehensive_unused_measures(used_measures)
    unused_final_measures = final_measures - used_measures

    tables = mp.get_tables()
    relationships = mp.get_relationships()
    roles = mp.get_roles()
    annotations = mp.get_annotations()
    measures_detail = mp.get_measures() or []

    column_count = sum(len(table.get('columns', [])) for table in tables)
    hidden_measure_count = sum(1 for measure in measures_detail if measure.get('isHidden'))
    hidden_table_count = sum(1 for table in tables if table.get('isHidden'))
    hidden_column_count = sum(
        1
        for table in tables
        for column in table.get('columns', [])
        if column.get('isHidden')
    )

    model_summary = {
        'table_count': len(tables),
        'column_count': column_count,
        'measure_count': len(measures_detail) if measures_detail else len(all_measures),
        'relationship_count': len(relationships),
        'role_count': len(roles),
        'hidden_table_count': hidden_table_count,
        'hidden_column_count': hidden_column_count,
        'hidden_measure_count': hidden_measure_count,
        'annotation_count': len(annotations),
    }

    theme_info = dp.get_theme_info() or {}
    bookmarks = dp.get_bookmarks()
    navigation_items = dp.get_navigation_items()
    formatting_details = dp.get_visual_formatting()

    bookmark_filters = sum(bookmark.get('filter_count', 0) for bookmark in bookmarks)
    bookmark_targets = sum(len(bookmark.get('target_visuals', [])) for bookmark in bookmarks)

    custom_tooltips = sum(1 for entry in formatting_details if entry.get('has_custom_tooltip'))
    custom_titles = sum(1 for entry in formatting_details if entry.get('has_custom_title'))
    custom_backgrounds = sum(1 for entry in formatting_details if entry.get('has_background'))
    custom_borders = sum(1 for entry in formatting_details if entry.get('has_border'))
    drop_shadows = sum(1 for entry in formatting_details if entry.get('has_drop_shadow'))
    formatting_highlights = sum(
        1
        for entry in formatting_details
        if entry.get('has_custom_tooltip')
        or entry.get('has_custom_title')
        or entry.get('has_background')
        or entry.get('has_border')
        or entry.get('has_drop_shadow')
    )

    navigation_counts = collections.Counter((item.get('visual_type') or 'Other') for item in navigation_items)

    report_summary = {
        'theme_name': theme_info.get('customTheme', {}).get('name')
        or theme_info.get('baseTheme', {}).get('name')
        or 'Power BI Default',
        'bookmark_count': len(bookmarks),
        'bookmark_filters': bookmark_filters,
        'bookmark_targets': bookmark_targets,
        'navigation_count': len(navigation_items),
        'formatting_highlights': formatting_highlights,
        'navigation_types': navigation_counts.most_common(3),
        'custom_tooltips': custom_tooltips,
        'custom_titles': custom_titles,
        'custom_backgrounds': custom_backgrounds,
        'custom_borders': custom_borders,
        'drop_shadows': drop_shadows,
    }

    return {
        'visual_count': visual_count,
        'page_count': len(unique_pages),
        'measure_count': len(all_measures),
        'unused_count': unused_analysis.get('total_unused', len(unused_final_measures)),
        'unused_breakdown': {
            'immediate': unused_analysis.get('immediate_unused', len(unused_final_measures)),
            'cascade': unused_analysis.get('cascade_unused', 0)
        },
        'most_common_visual': most_common_visual,
        'visual_distribution': visual_distribution,
        'model_summary': model_summary,
        'report_summary': report_summary
    }


def calculate_lineage_metrics(lineage_view_processor: LineageView) -> Dict[str, int]:
    """
    Calculate metrics for the lineage view page.

    Returns:
        Dict with parent_measures_count, final_measures_count, and columns_count
    """
    all_measures = lineage_view_processor.get_all_measures()
    final_measures = lineage_view_processor.get_final_measures()

    # Count columns from nodes
    columns_count = sum(1 for node in lineage_view_processor.nodes if node.get('type') == 'column')

    # Parent measures are those that have children (total - final)
    parent_measures_count = len(all_measures) - len(final_measures)

    return {
        'parent_measures_count': parent_measures_count,
        'final_measures_count': len(final_measures),
        'columns_count': columns_count,
        'total_measures': len(all_measures),
        'total_relationships': len(lineage_view_processor.edges)
    }


def build_source_graph(m_queries_info: List[Dict[str, str]]) -> tuple:
    """Build nodes and edges for source explorer visualization."""
    nodes = [{'id': q['table_name'], 'label': q['table_name']} for q in m_queries_info]

    edges = []
    for query_info in m_queries_info:
        m_query_text = query_info['m_query']
        for other_query_info in m_queries_info:
            if other_query_info['table_name'] != query_info['table_name']:
                pattern = re.compile(rf'"{re.escape(other_query_info["table_name"])}"')
                if pattern.search(m_query_text):
                    edges.append({
                        'from': query_info['table_name'],
                        'to': other_query_info['table_name']
                    })

    return nodes, edges
