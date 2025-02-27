import os
import json
import csv
import re
import datetime
import collections
from typing import List, Set, Dict, Any, Optional
from flask import Flask, render_template, g, current_app, abort, request
from data_processor import DataProcessor
from lineage_view import LineageView

def create_app(config_object: str = 'config.Config') -> Flask:
    """
    Application factory for creating the Flask app.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)

    # Set up paths relative to this file's directory
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app.config.setdefault('REPORT_JSON_PATH', os.path.join(base_dir, 'data', 'report.json'))
    app.config.setdefault(
        'MEASURE_DEPENDENCIES_TSV_PATH',
        os.path.join(base_dir, 'data', 'MeasureDependencies.tsv')
    )
    app.config.setdefault('MODEL_JSON_PATH', os.path.join(base_dir, 'data', 'model.json'))

    @app.teardown_appcontext
    def teardown(exception: Optional[BaseException] = None) -> None:
        """Clean up resources stored in g."""
        g.pop('data_processor', None)
        g.pop('lineage_view_processor', None)

    def get_data_processor() -> DataProcessor:
        """
        Retrieve or create the DataProcessor instance for this request.
        """
        if 'data_processor' not in g:
            dp = DataProcessor(app.config['REPORT_JSON_PATH'])
            dp.process_json()
            g.data_processor = dp
        return g.data_processor

    def get_lineage_view_processor() -> LineageView:
        """
        Retrieve or create the LineageView instance for this request.
        """
        if 'lineage_view_processor' not in g:
            lvp = LineageView(app.config['MEASURE_DEPENDENCIES_TSV_PATH'])
            lvp.process_lineage_data()
            g.lineage_view_processor = lvp
        return g.lineage_view_processor

    def load_model_data(model_json_path: str) -> Dict[str, Any]:
        """
        Load model data from a JSON file.
        """
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
        tables = data.get('model', {}).get('tables', [])
        expressions = data.get('model', {}).get('expressions', [])
        m_queries_info: List[Dict[str, str]] = []

        def starts_with_let(query: str) -> bool:
            return query.strip().lower().startswith('let')

        for table in tables:
            for partition in table.get('partitions', []):
                source = partition.get('source', {})
                if source.get('type') == 'm':
                    m_query = '\n'.join(source.get('expression', []))
                    if starts_with_let(m_query):
                        m_queries_info.append({
                            'table_name': table['name'],
                            'm_query': m_query
                        })

        for expression in expressions:
            if expression.get('kind') == 'm':
                m_query = '\n'.join(expression.get('expression', []))
                if starts_with_let(m_query):
                    m_queries_info.append({
                        'table_name': expression['name'],
                        'm_query': m_query
                    })

        return m_queries_info

    def get_report_metrics() -> Dict[str, Any]:
        """
        Get metrics about the report for the dashboard.
        """
        dp = get_data_processor()
        lvp = get_lineage_view_processor()
        
        # Extract visual types for analysis - FIXED to only count visuals with fields
        visual_count = 0
        visual_types = []
        for row in dp.visuals_data:
            if len(row) > 3 and row[3] and len(row) > 1 and row[1]:  # Only count visuals with fields
                visual_type = row[1]
                if visual_type and visual_type != "Page Level Filters" and visual_type != "Global Level Filters":
                    visual_count += 1
                    visual_types.append(visual_type)
        
        # Find most common visual type
        most_common_visual = "None"
        if visual_types:
            counter = collections.Counter(visual_types)
            most_common_visual = counter.most_common(1)[0][0]
        
        # Count unique pages
        unique_pages = set()
        for row in dp.visuals_data:
            if row and row[0]:  # Check if page name exists
                unique_pages.add(row[0])
        
        # Get all measures for total count
        all_measures = lvp.get_all_measures()
        
        # Get used measures
        used_measures = dp.get_used_measures()
        
        # Get final measures (measures that don't have children)
        final_measures = lvp.get_final_measures()
        
        # Calculate unused final measures - THIS IS THE KEY FIX
        unused_final_measures = final_measures - used_measures
        
        # Create metrics dictionary
        metrics = {
            "visual_count": visual_count,
            "page_count": len(unique_pages),
            "measure_count": len(all_measures),
            "unused_count": len(unused_final_measures),
            "most_common_visual": most_common_visual
        }
        
        return metrics

    @app.context_processor
    def inject_current_year():
        """Inject the current year into templates."""
        return {"current_year": datetime.datetime.now().year}

    @app.context_processor
    def inject_report_name():
        """Inject the report name into templates."""
        # Use the filename as the report name, or get from report data if available
        report_path = app.config['REPORT_JSON_PATH']
        report_name = os.path.basename(report_path).replace(".json", "")
        
        # Try to get a better name from the report data if possible
        try:
            with open(report_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if 'name' in data:
                    report_name = data['name']
        except:
            pass
            
        return {"report_name": report_name}

    @app.route('/')
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

    @app.route('/table-view')
    def table_view() -> str:
        dp = get_data_processor()
        return render_template('table_view.html', table_data=dp.visuals_data)

    @app.route('/lineage-view')
    def lineage_view_route() -> str:
        lvp = get_lineage_view_processor()
        return render_template(
            'lineage_view.html',
            nodes=lvp.nodes,
            edges=lvp.edges
        )

    @app.route('/dax-expressions')
    def dax_expressions() -> str:
        lvp = get_lineage_view_processor()
        dax_expr = lvp.extract_dax_expressions()
        return render_template('dax_expressions.html', dax_expressions=dax_expr)

    @app.route('/source-explorer')
    def source_explorer() -> str:
        data = load_model_data(app.config['MODEL_JSON_PATH'])
        m_queries_info = extract_m_queries(data)

        # Build nodes for visualization
        nodes = [{'id': q['table_name'], 'label': q['table_name']} for q in m_queries_info]

        # Build edges based on references found in the M query text
        edges = []
        for query_info in m_queries_info:
            m_query_text = query_info['m_query']
            for other_query_info in m_queries_info:
                if other_query_info['table_name'] != query_info['table_name']:
                    # Look for the other table's name in quotes
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

    @app.route('/unused-measures')
    def unused_measures_view() -> str:
        dp = get_data_processor()
        lvp = get_lineage_view_processor()

        used_measures = dp.get_used_measures()
        all_measures = lvp.get_all_measures()
        unused_measures = sorted(list(all_measures - used_measures))

        return render_template('unused_measures.html', unused_measures=unused_measures)

    @app.errorhandler(404)
    def page_not_found(e):
        """Handle 404 errors with a custom page."""
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        """Handle 500 errors with a custom page."""
        return render_template('errors/500.html'), 500

    return app

if __name__ == '__main__':
    # Create the app and run with debug mode enabled by default if not set.
    app = create_app()
    app.run(debug=app.config.get('DEBUG', True))