"""Analysis routes blueprint - table view, lineage, DAX, unused measures."""

import collections
from typing import Any, Dict, List, Set, Tuple

from flask import Blueprint, abort, current_app, render_template

from utils.processors import (
    get_data_processor,
    get_lineage_view_processor,
    get_model_processor,
    get_report_metrics,
    calculate_lineage_metrics,
)

analysis_bp = Blueprint('analysis', __name__)


@analysis_bp.route('/table-view')
def table_view() -> str:
    """Render the table view with visual field analysis."""
    dp = get_data_processor()
    mp = get_model_processor()
    metrics = get_report_metrics()

    tables = mp.get_tables()
    measures_detail = mp.get_measures() or []

    field_metadata_map: Dict[str, Dict[str, Any]] = {}
    field_metadata_lower: Dict[str, Dict[str, Any]] = {}

    def register_field(key: str, meta: Dict[str, Any]) -> None:
        if not key:
            return
        meta_copy = dict(meta)
        meta_copy.setdefault('full', key)
        meta_copy.setdefault('display', meta_copy.get('name', key))
        field_metadata_map[key] = meta_copy
        field_metadata_lower[key.lower()] = meta_copy

    for table in tables:
        table_name = (table.get('name') or '').strip()
        if not table_name:
            continue

        for column in table.get('columns', []):
            column_name = (column.get('name') or '').strip()
            if not column_name:
                continue
            key = f"{table_name}[{column_name}]"
            register_field(key, {
                'table': table_name,
                'name': column_name,
                'kind': 'column',
                'data_type': column.get('dataType'),
                'data_category': column.get('dataCategory'),
                'format_string': column.get('formatString'),
                'description': column.get('description'),
                'summarize_by': column.get('summarizeBy')
            })

        for measure in table.get('measures', []):
            measure_name = (measure.get('name') or '').strip()
            if not measure_name:
                continue
            key = f"{table_name}[{measure_name}]"
            register_field(key, {
                'table': table_name,
                'name': measure_name,
                'kind': 'measure',
                'data_type': None,
                'data_category': None,
                'format_string': measure.get('formatString'),
                'description': measure.get('description')
            })

    for measure in measures_detail:
        table_name = (measure.get('table') or '').strip()
        measure_name = (measure.get('name') or '').strip()
        if not table_name or not measure_name:
            continue
        key = f"{table_name}[{measure_name}]"
        if key not in field_metadata_map:
            register_field(key, {
                'table': table_name,
                'name': measure_name,
                'kind': 'measure',
                'data_type': None,
                'data_category': None,
                'format_string': measure.get('formatString'),
                'description': measure.get('description')
            })

    def parse_field_reference(field_name: str) -> Tuple[str, str]:
        if '[' in field_name and field_name.endswith(']'):
            prefix, suffix = field_name.split('[', 1)
            return prefix.strip(), suffix[:-1].strip()
        return '', field_name.strip()

    def build_field_metadata(field_name: str) -> Dict[str, Any]:
        if not field_name:
            return {
                'full': '',
                'table': '',
                'name': '',
                'display': '',
                'kind': 'unknown',
                'data_type': None,
                'data_category': None,
                'format_string': None,
                'description': None
            }

        base = field_metadata_map.get(field_name)
        if not base:
            base = field_metadata_lower.get(field_name.lower())

        table_part, simple_name = parse_field_reference(field_name)

        if base:
            result = dict(base)
            result['full'] = field_name
            result.setdefault('table', table_part)
            result.setdefault('name', simple_name)
            result.setdefault('display', base.get('display', simple_name))
            return result

        return {
            'full': field_name,
            'table': table_part,
            'name': simple_name,
            'display': simple_name,
            'kind': 'unknown',
            'data_type': None,
            'data_category': None,
            'format_string': None,
            'description': None
        }

    def split_fields(raw_value: Any) -> List[str]:
        if not raw_value:
            return []
        if isinstance(raw_value, list):
            return [str(value).strip() for value in raw_value if str(value).strip()]
        return [segment.strip() for segment in str(raw_value).split(';') if segment.strip()]

    visual_rows: List[Dict[str, Any]] = []
    page_stats: Dict[str, Dict[str, Any]] = {}
    field_usage: Dict[str, Dict[str, Any]] = {}
    unique_pages: Set[str] = set()

    total_field_assignments = 0
    visuals_with_filters = 0
    visuals_with_vc = 0
    visuals_with_objects = 0

    def build_field_list(field_names: List[str], usage_key: str, page: str, visual_identifier: str) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for field_name in field_names:
            metadata = build_field_metadata(field_name)
            usage_entry = field_usage.setdefault(metadata['full'], {
                'field': metadata['full'],
                'table': metadata.get('table', ''),
                'name': metadata.get('name', metadata['full']),
                'kind': metadata.get('kind', 'unknown'),
                'data_type': metadata.get('data_type'),
                'data_category': metadata.get('data_category'),
                'format_string': metadata.get('format_string'),
                'description': metadata.get('description'),
                'count': 0,
                'filter_count': 0,
                'vc_count': 0,
                'object_count': 0,
                'pages': set(),
                'visuals': set()
            })

            if usage_key == 'fields':
                usage_entry['count'] += 1
            elif usage_key == 'filters':
                usage_entry['filter_count'] += 1
            elif usage_key == 'vc':
                usage_entry['vc_count'] += 1
            elif usage_key == 'objects':
                usage_entry['object_count'] += 1

            if page:
                usage_entry['pages'].add(page)
            usage_entry['visuals'].add(visual_identifier)

            items.append({
                'full': metadata['full'],
                'table': metadata.get('table', ''),
                'name': metadata.get('name', metadata['full']),
                'display': metadata.get('display', metadata.get('name', metadata['full'])),
                'kind': metadata.get('kind', 'unknown'),
                'data_type': metadata.get('data_type'),
                'data_category': metadata.get('data_category'),
                'format_string': metadata.get('format_string'),
                'description': metadata.get('description')
            })
        return items

    for row in dp.visuals_data:
        if not row or len(row) < 4:
            continue

        page = (row[0] or 'Unassigned').strip()
        visual_type = (row[1] or 'Unknown Visual').strip()
        visual_name = (row[2] or '').strip() or visual_type
        raw_fields = split_fields(row[3])
        if not raw_fields:
            continue

        filter_fields_raw = split_fields(row[4] if len(row) > 4 else '')
        vc_fields_raw = split_fields(row[5] if len(row) > 5 else '')
        object_fields_raw = split_fields(row[6] if len(row) > 6 else '')

        visual_identifier = f"{page}:{visual_name}"

        fields = build_field_list(raw_fields, 'fields', page, visual_identifier)
        filter_fields = build_field_list(filter_fields_raw, 'filters', page, visual_identifier)
        vc_fields = build_field_list(vc_fields_raw, 'vc', page, visual_identifier)
        object_fields = build_field_list(object_fields_raw, 'objects', page, visual_identifier)

        total_field_assignments += len(fields)
        if filter_fields:
            visuals_with_filters += 1
        if vc_fields:
            visuals_with_vc += 1
        if object_fields:
            visuals_with_objects += 1

        unique_pages.add(page)

        summary = page_stats.setdefault(page, {
            'visual_count': 0,
            'field_set': set(),
            'measure_set': set(),
            'column_set': set(),
            'filter_fields': set(),
            'filter_visuals': 0,
            'visual_types': collections.Counter(),
            'field_frequency': collections.Counter()
        })

        summary['visual_count'] += 1
        summary['visual_types'][visual_type] += 1

        for field_entry in fields:
            field_name = field_entry['full']
            summary['field_set'].add(field_name)
            summary['field_frequency'][field_name] += 1
            if field_entry['kind'] == 'measure':
                summary['measure_set'].add(field_name)
            elif field_entry['kind'] == 'column':
                summary['column_set'].add(field_name)

        for field_entry in filter_fields:
            field_name = field_entry['full']
            summary['field_set'].add(field_name)
            summary['filter_fields'].add(field_name)
            summary['field_frequency'][field_name] += 1

        if filter_fields:
            summary['filter_visuals'] += 1

        visual_rows.append({
            'page': page,
            'visual_type': visual_type,
            'visual_name': visual_name,
            'fields': fields,
            'filter_fields': filter_fields,
            'vc_fields': vc_fields,
            'object_fields': object_fields,
            'has_filters': bool(filter_fields),
            'has_vc': bool(vc_fields),
            'has_objects': bool(object_fields),
            'field_count': len(fields),
            'filter_count': len(filter_fields)
        })

    visual_rows.sort(key=lambda item: (item['page'].lower(), item['visual_type'].lower(), item['visual_name'].lower()))

    field_usage_lookup: Dict[str, Dict[str, Any]] = {}
    field_usage_summary: List[Dict[str, Any]] = []
    field_kind_counter: collections.Counter = collections.Counter()

    for field_name, usage in field_usage.items():
        total_occurrences = usage['count'] + usage['filter_count'] + usage['vc_count'] + usage['object_count']
        field_kind_counter[usage.get('kind', 'unknown')] += 1
        pages_list = sorted(usage['pages'])
        visuals_list = sorted(usage['visuals'])

        summary_entry = {
            'field': field_name,
            'table': usage.get('table', ''),
            'name': usage.get('name', field_name),
            'kind': usage.get('kind', 'unknown'),
            'data_type': usage.get('data_type'),
            'data_category': usage.get('data_category'),
            'format_string': usage.get('format_string'),
            'description': usage.get('description'),
            'count': usage['count'],
            'filter_count': usage['filter_count'],
            'vc_count': usage['vc_count'],
            'object_count': usage['object_count'],
            'total': total_occurrences,
            'pages': pages_list,
            'page_count': len(pages_list),
            'visuals': visuals_list,
            'visual_count': len(visuals_list)
        }

        tooltip_parts = []
        if summary_entry['table']:
            tooltip_parts.append(f"Table: {summary_entry['table']}")
        kind_label = summary_entry.get('kind', 'unknown').replace('_', ' ').title()
        tooltip_parts.append(f"Type: {kind_label}")
        if summary_entry.get('data_type'):
            tooltip_parts.append(f"Data type: {summary_entry['data_type']}")
        if summary_entry.get('data_category'):
            tooltip_parts.append(f"Category: {summary_entry['data_category']}")
        tooltip_parts.append(f"Visuals: {summary_entry['visual_count']}")
        if summary_entry.get('filter_count'):
            tooltip_parts.append(f"Filters: {summary_entry['filter_count']}")
        if summary_entry.get('page_count'):
            tooltip_parts.append(f"Pages: {summary_entry['page_count']}")
        summary_entry['tooltip'] = ' • '.join(tooltip_parts)
        summary_entry['kind_label'] = kind_label

        field_usage_lookup[field_name] = summary_entry
        field_usage_summary.append(summary_entry)

    field_usage_summary.sort(key=lambda item: (-item['total'], item['field'].lower()))
    top_field_usage = field_usage_summary[:12]

    page_summaries: List[Dict[str, Any]] = []
    for page, data in page_stats.items():
        visual_types = [
            {'type': visual_type, 'count': count}
            for visual_type, count in data['visual_types'].most_common()
        ]

        top_fields = []
        for field_name, frequency in data['field_frequency'].most_common(3):
            usage_info = field_usage_lookup.get(field_name, {})
            top_fields.append({
                'field': field_name,
                'frequency': frequency,
                'kind': usage_info.get('kind', 'unknown'),
                'table': usage_info.get('table', ''),
                'name': usage_info.get('name', field_name),
                'data_type': usage_info.get('data_type'),
                'data_category': usage_info.get('data_category')
            })

        page_summaries.append({
            'page': page,
            'visual_count': data['visual_count'],
            'field_count': len(data['field_set']),
            'measure_count': len(data['measure_set']),
            'column_count': len(data['column_set']),
            'filter_visuals': data['filter_visuals'],
            'filter_field_count': len(data['filter_fields']),
            'visual_types': visual_types,
            'top_fields': top_fields
        })

    page_summaries.sort(key=lambda item: item['page'].lower())

    total_visuals = len(visual_rows)
    total_unique_fields = len(field_usage_lookup)
    field_overview = {
        'total_visuals': total_visuals,
        'unique_fields': total_unique_fields,
        'unique_measures': field_kind_counter.get('measure', 0),
        'unique_columns': field_kind_counter.get('column', 0),
        'unique_unknown': field_kind_counter.get('unknown', 0),
        'visuals_with_filters': visuals_with_filters,
        'visuals_with_vc': visuals_with_vc,
        'visuals_with_objects': visuals_with_objects,
        'avg_fields_per_visual': round(total_field_assignments / total_visuals, 1) if total_visuals else 0,
        'filter_ratio': round((visuals_with_filters / total_visuals) * 100, 1) if total_visuals else 0.0
    }

    unique_pages_sorted = sorted(unique_pages, key=lambda value: value.lower())

    return render_template(
        'table_view.html',
        visual_rows=visual_rows,
        unique_pages=unique_pages_sorted,
        metrics=metrics,
        page_summaries=page_summaries,
        field_usage_summary=top_field_usage,
        field_usage_lookup=field_usage_lookup,
        field_overview=field_overview,
        field_kind_counts=dict(field_kind_counter)
    )


@analysis_bp.route('/lineage-view')
def lineage_view_route() -> str:
    """Render the lineage view with measure dependencies."""
    if not current_app.config.get('ENABLE_LINEAGE_VIEW', True):
        abort(404, description="This feature is currently disabled.")

    lvp = get_lineage_view_processor()
    lineage_metrics = calculate_lineage_metrics(lvp)

    return render_template(
        'lineage_view.html',
        nodes=lvp.nodes,
        edges=lvp.edges,
        lineage_metrics=lineage_metrics
    )


@analysis_bp.route('/dax-expressions')
def dax_expressions() -> str:
    """Render the DAX expressions explorer."""
    if not current_app.config.get('ENABLE_DAX_EXPLORER', True):
        abort(404, description="This feature is currently disabled.")

    lvp = get_lineage_view_processor()
    dax_expr = lvp.extract_dax_expressions()
    return render_template('dax_expressions.html', dax_expressions=dax_expr)


@analysis_bp.route('/unused-measures')
def unused_measures_view() -> str:
    """Render the unused measures analysis."""
    dp = get_data_processor()
    lvp = get_lineage_view_processor()

    known_measures = set(lvp.measure_data) or lvp.get_all_measures()
    used_measures = dp.get_used_measures(known_measures)
    used_measures = lvp.expand_used_measures(used_measures)

    unused_analysis = lvp.get_comprehensive_unused_measures(used_measures)
    metrics = get_report_metrics()

    return render_template(
        'unused_measures.html',
        unused_measures=unused_analysis['all_unused'],
        unused_analysis=unused_analysis,
        metrics=metrics
    )
