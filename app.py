import os
import json
import csv
import re
import datetime
import collections
import markdown
from typing import List, Set, Dict, Any, Optional
from flask import Flask, render_template, g, current_app, abort, request, jsonify
from data_processor import DataProcessor
from lineage_view import LineageView
from model_processor import ModelProcessor
from config import get_config

def create_app(config_object=None) -> Flask:
    """
    Application factory for creating the Flask app.
    """
    app = Flask(__name__)

    # Load configuration
    if config_object is None:
        # Use function to get appropriate config based on environment
        config_object = get_config()

    app.config.from_object(config_object)

    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    # No need to set default paths - they are already in the config file

    @app.teardown_appcontext
    def teardown(exception: Optional[BaseException] = None) -> None:
        """Clean up resources stored in g."""
        g.pop('data_processor', None)
        g.pop('lineage_view_processor', None)
        g.pop('model_processor', None)

    def get_data_processor() -> DataProcessor:
        """
        Retrieve or create the DataProcessor instance for this request.
        """
        if not hasattr(g, 'data_processor'):
            # Check if required file exists
            if not os.path.exists(app.config['REPORT_JSON_PATH']):
                current_app.logger.error(f"Report JSON file not found: {app.config['REPORT_JSON_PATH']}")
                abort(500, description="Report data file not found. Please check your data directory.")
            
            dp = DataProcessor(app.config['REPORT_JSON_PATH'])
            dp.process_json()
            g.data_processor = dp
        return g.data_processor

    def get_lineage_view_processor() -> LineageView:
        """
        Retrieve or create the LineageView instance for this request.
        """
        if not hasattr(g, 'lineage_view_processor'):
            lvp = LineageView(app.config['MEASURE_DEPENDENCIES_TSV_PATH'])
            lvp.process_lineage_data()
            g.lineage_view_processor = lvp
        return g.lineage_view_processor

    def get_model_processor() -> ModelProcessor:
        """
        Retrieve or create the ModelProcessor instance for this request.
        """
        if not hasattr(g, 'model_processor'):
            if not os.path.exists(app.config['MODEL_JSON_PATH']):
                current_app.logger.error(f"Model JSON file not found: {app.config['MODEL_JSON_PATH']}")
                abort(500, description="Model data file not found. Please check your data directory.")
            mp = ModelProcessor(app.config['MODEL_JSON_PATH'])
            mp.load()
            g.model_processor = mp
        return g.model_processor

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
        """
        Get metrics about the report for the dashboard.
        """
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
        # Use existing methods to get measures
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

    def get_report_name():
        """Extract the report name from the report file."""
        report_path = app.config['REPORT_JSON_PATH']
        report_name = os.path.basename(report_path).replace(".json", "")

        try:
            with open(report_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if 'name' in data:
                    report_name = data['name']
        except:
            pass

        return report_name

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
        metrics = get_report_metrics()  # This already calculates unique pages
        
        # Extract unique pages for the template
        unique_pages = {row[0] for row in dp.visuals_data if row and row[0]}
        
        return render_template(
            'table_view.html', 
            table_data=dp.visuals_data,
            unique_pages=list(unique_pages),
            metrics=metrics  # Optional: pass full metrics if needed elsewhere
        )

    @app.route('/lineage-view')
    def lineage_view_route() -> str:
        # Check if the feature is enabled in config
        if not app.config.get('ENABLE_LINEAGE_VIEW', True):
            abort(404, description="This feature is currently disabled.")

        lvp = get_lineage_view_processor()
        
        # Calculate metrics for the lineage view
        lineage_metrics = calculate_lineage_metrics(lvp)
        
        return render_template(
            'lineage_view.html',
            nodes=lvp.nodes,
            edges=lvp.edges,
            lineage_metrics=lineage_metrics
        )

    @app.route('/dax-expressions')
    def dax_expressions() -> str:
        # Check if the feature is enabled in config
        if not app.config.get('ENABLE_DAX_EXPLORER', True):
            abort(404, description="This feature is currently disabled.")

        lvp = get_lineage_view_processor()
        dax_expr = lvp.extract_dax_expressions()
        return render_template('dax_expressions.html', dax_expressions=dax_expr)

    @app.route('/model-insights')
    def model_insights() -> str:
        if not app.config.get('ENABLE_MODEL_INSIGHTS', True):
            abort(404, description="This feature is currently disabled.")

        mp = get_model_processor()
        metrics = get_report_metrics()

        tables = sorted(mp.get_tables(), key=lambda item: (item.get('name') or '').lower())
        measures = mp.get_measures()
        relationships = sorted(mp.get_relationships(), key=lambda item: ((item.get('fromTable') or '').lower(), (item.get('toTable') or '').lower()))
        roles = sorted(mp.get_roles(), key=lambda item: (item.get('name') or '').lower())
        annotations = mp.get_annotations()
        annotation_items = [{'name': key, 'value': value} for key, value in sorted(annotations.items())]

        column_count = sum(len(table.get('columns', [])) for table in tables)
        hidden_table_count = sum(1 for table in tables if table.get('isHidden'))
        hidden_column_count = sum(1 for table in tables for column in table.get('columns', []) if column.get('isHidden'))

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

    @app.route('/report-insights')
    def report_insights() -> str:
        if not app.config.get('ENABLE_REPORT_INSIGHTS', True):
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
        sorted_layout_records = sorted(layout_records, key=lambda item: ((item.get('page') or ''), item.get('visual_name') or ''))
        sorted_query_details = sorted(query_details, key=lambda item: ((item.get('page') or ''), item.get('visual_name') or ''))

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
            formatting_highlights=sorted(formatting_highlights, key=lambda item: ((item.get('page') or ''), item.get('visual_name') or '')),
            navigation_items=sorted(navigation_items, key=lambda item: ((item.get('page') or ''), item.get('visual_name') or '')),
            navigation_summary=navigation_summary,
            report_summary=report_summary
        )

    @app.route('/source-explorer')
    def source_explorer() -> str:
        # Check if the feature is enabled in config
        if not app.config.get('ENABLE_SOURCE_EXPLORER', True):
            abort(404, description="This feature is currently disabled.")

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

        # Get used measures from visuals
        known_measures = set(lvp.measure_data) or lvp.get_all_measures()
        used_measures = dp.get_used_measures(known_measures)
        used_measures = lvp.expand_used_measures(used_measures)

        # Get comprehensive analysis of all unused measures
        unused_analysis = lvp.get_comprehensive_unused_measures(used_measures)
        metrics = get_report_metrics()

        # Pass both the simple list for the template and the analysis for future use
        return render_template(
            'unused_measures.html',
            unused_measures=unused_analysis['all_unused'],
            unused_analysis=unused_analysis,  # Pass the full analysis for the template
            metrics=metrics
        )

    @app.route('/api/model-json', methods=['GET'])
    def get_model_json():
        """API endpoint to get the current model JSON."""
        try:
            model_data = load_model_data(app.config['MODEL_JSON_PATH'])
            return jsonify(model_data)
        except Exception as e:
            current_app.logger.error(f"Error loading model JSON: {e}")
            return jsonify({"error": str(e)}), 500

    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error=e.description, code=404), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('error.html', error=e.description, code=500), 500

    return app

if __name__ == '__main__':
    # Create the app with default configuration
    app = create_app()
    app.run(debug=app.config.get('DEBUG', True))