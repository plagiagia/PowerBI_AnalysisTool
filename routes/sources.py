"""Sources routes blueprint - source explorer."""

import re
from typing import Dict, List

from flask import Blueprint, abort, current_app, render_template

from utils.processors import load_model_data, extract_m_queries

sources_bp = Blueprint('sources', __name__)


@sources_bp.route('/source-explorer')
def source_explorer() -> str:
    """Render the source explorer with M query analysis."""
    if not current_app.config.get('ENABLE_SOURCE_EXPLORER', True):
        abort(404, description="This feature is currently disabled.")

    data = load_model_data(current_app.config['MODEL_JSON_PATH'])
    m_queries_info = extract_m_queries(data)

    # Build nodes for visualization
    nodes = [{'id': q['table_name'], 'label': q['table_name']} for q in m_queries_info]

    # Build edges based on references found in the M query text
    edges: List[Dict[str, str]] = []
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

    return render_template(
        'source_explorer.html',
        nodes=nodes,
        edges=edges,
        m_queries_info=m_queries_info
    )
