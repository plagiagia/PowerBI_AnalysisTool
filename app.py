<<<<<<< Updated upstream
from flask import Flask, render_template, jsonify, request
from QuerySimilarityChecker import QuerySimilarityChecker, QueryFoldingAnalyzer
from gpt import GPTQueryAnalyzer
=======
import os
>>>>>>> Stashed changes
import json
import csv
import re
<<<<<<< Updated upstream
import os


# Define global file paths
REPORT_JSON_PATH = 'GPT_Projects/WebAPP/report.json'
MEASURE_DEPENDENCIES_TSV_PATH = 'GPT_Projects/WebAPP/MeasureDependencies.tsv'
MODEL_JSON_PATH = 'GPT_Projects/WebAPP/model.json'
gpt_analyzer = GPTQueryAnalyzer(os.getenv('OPENAI_API_KEY'))
=======
import datetime
import collections
from typing import List, Set, Dict, Any, Optional
from flask import Flask, render_template, g, current_app, abort, request
from data_processor import DataProcessor
from lineage_view import LineageView
>>>>>>> Stashed changes

def create_app(config_object: str = 'config.Config') -> Flask:
    """
    Application factory for creating the Flask app.
    """
    app = Flask(__name__)
    app.config.from_object(config_object)

<<<<<<< Updated upstream

class DataProcessor:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.visuals_data = []

    def process_json(self):
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except json.JSONDecodeError:
            print("Error reading or parsing the JSON file.")
            return

        page_filters = json.loads(data.get('filters', '[]'))
        if page_filters:
            filter_name = page_filters[0].get('name', '')
            page_filter_fields = self.extract_filter_fields(page_filters)
            if page_filter_fields:
                self.visuals_data.append(
                    ['All Pages', 'Global Level Filters', filter_name, '', page_filter_fields, '', ''])

        # Process each slide of our report
        for section in data.get('sections', []):
            self.process_section(section)

    def process_section(self, section: list):
        # Extract the filters on page level
        section_filters = json.loads(section.get('filters', '[]'))
        page_name = section.get('displayName', '')
        if section_filters:
            filter_name = section_filters[0].get('name', '')
            section_filter_fields = self.extract_filter_fields(section_filters)
            if section_filter_fields:
                self.visuals_data.append(
                    [page_name, 'Page Level Filters', filter_name, '', section_filter_fields, '', ''])

        for visual in section.get('visualContainers', []):
            visual_data = self.extract_visual_data(visual, page_name)
            self.visuals_data.append(visual_data)

    def extract_filter_fields(self, filter_data: list) -> str:
        filter_fields = []
        for f in filter_data:
            if 'expression' in f:
                for key in f['expression']:
                    expr = f['expression'][key]
                    if 'Expression' in expr and 'Property' in expr:
                        entity = expr['Expression'].get(
                            'SourceRef', {}).get('Entity', '')
                        property_name = expr.get('Property', '')
                        if entity and property_name:
                            filter_fields.append(f"{entity}[{property_name}]")
        return "; ".join(filter_fields)

    def extract_visual_data(self, visual: dict, page_name: str):
        config = json.loads(visual['config'])

        # Flexible handling of various visual configuration keys
        visual_config = None
        for key in config:
            if 'visualType' in config[key]:
                visual_config = config[key]
                break
        if not visual_config:
            return [page_name, "Unknown visual type", "", "", "", '', '']

        visual_type = visual_config.get('visualType', '')

        visual_name = config.get('name', '')

        # Handle the case where there's no prototypeQuery
        if 'prototypeQuery' not in visual_config:
            return [page_name, visual_type, visual_name, "", "", '']

        entity_aliases = {item['Name']: item['Entity']
                          for item in visual_config['prototypeQuery']['From']}

        select_fields = self.extract_fields(
            visual_config['prototypeQuery'].get('Select', []), entity_aliases)

        filter_data = visual.get('filters', '[]')
        filter_data = json.loads(filter_data)
        filter_fields = self.extract_filter_fields(filter_data)

        object_data = visual_config.get('objects', {})
        object_fields = self.extract_vc_objects_fields(object_data)

        vc_objects_data = visual_config.get('vcObjects', {})
        vc_objects_fields = self.extract_vc_objects_fields(vc_objects_data)

        # objects_data = visual_type.get('objects', {})
        # object_fields = self.extract_objects_fields(objects_data)

        return [page_name, visual_type, visual_name, select_fields, filter_fields, vc_objects_fields, object_fields]

    def extract_objects_fields(self, objects_data):
        fields = []
        if isinstance(objects_data, dict):
            for key, value in objects_data.items():
                # Look for nested dictionaries and lists
                if isinstance(value, dict):
                    for inner_key, inner_value in value.items():
                        if inner_key == 'expr' and isinstance(inner_value, dict):
                            extracted = self.extract_expression_fields(
                                inner_value)
                            fields.extend(extracted)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and 'expr' in item:
                            extracted = self.extract_expression_fields(
                                item['expr'])
                            fields.extend(extracted)
        return "; ".join(filter(None, fields))

    def extract_expression_fields(self, expr_obj):
        extracted_fields = []
        if isinstance(expr_obj, dict):
            for key, value in expr_obj.items():
                if key in ['Expression', 'Aggregation'] and isinstance(value, dict):
                    if 'Column' in value:
                        column = value['Column']
                        entity = column.get('SourceRef', {}).get('Entity', '')
                        property_name = column.get('Property', '')
                        if entity and property_name:
                            extracted_fields.append(
                                f"{entity}[{property_name}]")
        return extracted_fields

    def extract_vc_objects_fields(self, vc_object, current_entity=None):
        fields = []
        if isinstance(vc_object, dict):
            for key, value in vc_object.items():
                if isinstance(value, dict):
                    # Check for Expression with SourceRef and Property
                    if 'Expression' in value and 'SourceRef' in value['Expression'] and 'Property' in value:
                        entity = value['Expression']['SourceRef'].get(
                            'Entity', current_entity)
                        property_name = value['Property']
                        if entity:
                            fields.append(f"{entity}[{property_name}]")
                    else:
                        fields.extend(self.extract_vc_objects_fields(
                            value, current_entity).split("; "))
                elif isinstance(value, list):
                    for item in value:
                        fields.extend(self.extract_vc_objects_fields(
                            item, current_entity).split("; "))
        return "; ".join(filter(None, fields))  # Filter out empty strings

    def extract_fields(self, fields, entity_aliases):
        extracted_fields = []
        for field in fields:
            if 'Column' in field:
                field_details = field['Column']
            elif 'Aggregation' in field:
                field_details = field['Aggregation']['Expression']['Column']
            elif 'Measure' in field:
                field_details = field['Measure']
            else:
                continue

            entity_alias = field_details['Expression']['SourceRef']['Source']
            entity_name = entity_aliases.get(entity_alias, '')

            property_name = field_details.get('Property', '')

            if entity_name and property_name:
                field_name = f"{entity_name}[{property_name}]"
                extracted_fields.append(field_name)

        return "; ".join(extracted_fields)

    def get_used_measures(self):
        used_measures = set()
        for visual_data in self.visuals_data:
            # Extract fields from select, filters, and vc objects
            # Indices for select fields, filter fields, and vc object fields
            for index in [3, 4, 5, 6]:
                if index < len(visual_data):
                    fields = visual_data[index].split('; ')
                    for field in fields:
                        measure = field.split('[')[-1].replace(']', '').strip()
                        if measure:
                            used_measures.add(measure)
        return used_measures


class LineageView:
    def __init__(self, tsv_file_path):
        self.tsv_file_path = tsv_file_path
        self.nodes = []
        self.edges = []
        self.measures_with_children = set()
        self.unique_edges = set()
        self.unique_columns = set()
        self.MEASURE_INDEX = 0
        self.DAX_EXPRESSION_INDEX = 1
        self.PARENT_INDEX = 2
        self.CHILD_INDEX = 3
        self.COLUMN_INDEX = 5

    def process_lineage_data(self):
        with open(self.tsv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter='\t')
            headers = next(reader)  # Skip the header row
            data = list(reader)  # Read the rest of the data

        # Process lineage data here
        for measure in data:
            measure_name = measure[self.MEASURE_INDEX]
            self.nodes.append(
                {'id': measure_name, 'label': measure_name, 'dax': measure[self.DAX_EXPRESSION_INDEX]})

            parent_measures = measure[self.PARENT_INDEX].split(
                '; ') if measure[self.PARENT_INDEX] else []
            has_parent = bool(parent_measures)

            # Processing for columns
            measure_columns = measure[self.COLUMN_INDEX].split(
                '; ') if measure[self.COLUMN_INDEX] else []
            for column in measure_columns:
                if column and not has_parent:  # Only add column edges for root measures
                    if column not in self.unique_columns:
                        self.nodes.append(
                            {'id': column, 'label': column, 'type': 'column'})
                        self.unique_columns.add(column)

                    edge = (column, measure_name)
                    if edge not in self.unique_edges:
                        self.unique_edges.add(edge)
                        self.edges.append({'from': column, 'to': measure_name})

            # Processing for parent-child relationships (existing logic)
            for parent in parent_measures:
                if parent:
                    edge = (parent, measure_name)
                    if edge not in self.unique_edges:
                        self.unique_edges.add(edge)
                        self.edges.append({'from': parent, 'to': measure_name})

    def extract_dax_expressions(self):
        dax_expressions = []
        for measure in self.nodes:
            if 'label' in measure and measure.get('type') != 'column':
                label = measure['label'].strip()
                if label:
                    dax_expression = measure['dax']
                    if dax_expression:
                        # Replace escape sequences with their corresponding characters
                        dax_expression = dax_expression.replace('\\n', '\n')
                        dax_expression = dax_expression.replace('\\t', '\t')
                        dax_expression = dax_expression.replace('\\r', '\r')
                        dax_expressions.append((label, dax_expression))
        return dax_expressions

    def get_all_measures(self):
        final_measures = set()
        parent_measures = set()

        with open(self.tsv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter='\t')
            next(reader)  # Skip the header row

            for measure in reader:
                measure_name = measure[self.MEASURE_INDEX]
                child_measures = measure[self.CHILD_INDEX].split(
                    '; ') if measure[self.CHILD_INDEX] else []

                # Add to final_measures if it has no children
                if not child_measures:
                    final_measures.add(measure_name)

                # Track all measures that are parents
                if child_measures:
                    parent_measures.add(measure_name)

        # A measure is final if it's in final_measures and not a parent
        return final_measures - parent_measures


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/table-view')
def table_view():
    json_processor = DataProcessor(REPORT_JSON_PATH)
    json_processor.process_json()
    return render_template('table_view.html', table_data=json_processor.visuals_data)


@app.route('/lineage-view')
def lineage_view():
    lineage_view_processor = LineageView(MEASURE_DEPENDENCIES_TSV_PATH)
    lineage_view_processor.process_lineage_data()
    return render_template('lineage_view.html', nodes=lineage_view_processor.nodes, edges=lineage_view_processor.edges)


@app.route('/dax-expressions')
def dax_expressions():
    lineage_view_processor = LineageView(MEASURE_DEPENDENCIES_TSV_PATH)
    lineage_view_processor.process_lineage_data()
    dax_expressions = lineage_view_processor.extract_dax_expressions()
    return render_template('dax_expressions.html', dax_expressions=dax_expressions)


@app.route('/unused-measures')
def unused_measures_view():
    # Process the data
    json_processor = DataProcessor(REPORT_JSON_PATH)
    json_processor.process_json()
    lineage_view_processor = LineageView(MEASURE_DEPENDENCIES_TSV_PATH)
    lineage_view_processor.process_lineage_data()

    # Get the sets of used and all measures
    used_measures = json_processor.get_used_measures()
    all_measures = lineage_view_processor.get_all_measures()

    # Determine the unused measures
    unused_measures = all_measures - used_measures

    # Sort the measures to display them in alphabetical order
    unused_measures = sorted(list(unused_measures))

    return render_template('unused_measures.html', unused_measures=unused_measures)

@app.route('/source-explorer')
def m_queries():
    # Load the JSON data from file
    with open(MODEL_JSON_PATH, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Extract queries
    m_queries_info = []
    # Get queries from tables
    for table in data['model']['tables']:
        for partition in table.get('partitions', []):
            source = partition.get('source', {})
            if source.get('type') == 'm':
                m_query = '\n'.join(source.get('expression', []))
                if m_query.strip().lower().startswith('let'):
=======
    # Set up paths relative to this file's directory
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app.config.setdefault('REPORT_JSON_PATH', os.path.join(base_dir, 'data', 'report.json'))
    app.config.setdefault(
        'MEASURE_DEPENDENCIES_TSV_PATH',
        os.path.join(base_dir, 'data', 'MeasureDependencies.tsv')
    )
    app.config.setdefault('MODEL_JSON_PATH', os.path.join(base_dir, 'data', 'model.json'))

    @app.teardown_appcontext
    def teardown(exception: Exception) -> None:
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
>>>>>>> Stashed changes
                    m_queries_info.append({
                        'table_name': expression['name'],
                        'm_query': m_query
                    })

<<<<<<< Updated upstream
    # Get queries from expressions
    for expression in data['model'].get('expressions', []):
        if expression.get('kind') == 'm':
            m_query = '\n'.join(expression.get('expression', []))
            if m_query.strip().lower().startswith('let'):
                m_queries_info.append({
                    'table_name': expression['name'],
                    'm_query': m_query
                })

    # Initialize similarity checker
    checker = QuerySimilarityChecker(similarity_threshold=0.75)

    # Prepare queries for similarity check
    queries = [(q['table_name'], q['m_query']) for q in m_queries_info]
    similar_pairs = checker.find_similar_queries(queries)

    # Add similarity information to m_queries_info
    for query_info in m_queries_info:
        query_info['similar_queries'] = [
            {
                'table_name': pair['table2'] if pair['table1'] == query_info['table_name'] else pair['table1'],
                'similarity': pair['similarity']
            }
            for pair in similar_pairs
            if query_info['table_name'] in (pair['table1'], pair['table2'])
        ]


    # Initialize analyzers
    folding_analyzer = QueryFoldingAnalyzer()

    # Analyze each query
    for query_info in m_queries_info:
        folding_analysis = folding_analyzer.analyze_query(query_info['m_query'])
        query_info['folding_analysis'] = folding_analysis

    return render_template('source_explorer.html', m_queries_info=m_queries_info)

@app.route('/analyze-query', methods=['POST'])
def analyze_query():
    data = request.json
    query = data.get('query')
    table_name = data.get('table_name')

    if not query or not table_name:
        return jsonify({'success': False, 'error': 'Missing query or table name'}), 400

    analysis = gpt_analyzer.analyze_query(query, table_name)
    return jsonify(analysis)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
=======
        return m_queries_info

    def get_report_metrics() -> Dict[str, Any]:
        """
        Get metrics about the report for the dashboard.
        """
        dp = get_data_processor()
        lvp = get_lineage_view_processor()
        
        # Extract visual types for analysis
        visual_types = []
        for row in dp.visuals_data:
            if len(row) > 1 and row[1]:  # Check if visual type exists in the row
                visual_type = row[1]
                if visual_type and visual_type != "Page Level Filters" and visual_type != "Global Level Filters":
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
        
        # Count measures and unused measures
        all_measures = lvp.get_all_measures()
        used_measures = dp.get_used_measures()
        unused_measures = all_measures - used_measures
        
        # Create metrics dictionary
        metrics = {
            "visual_count": len(visual_types),
            "page_count": len(unique_pages),
            "measure_count": len(all_measures),
            "unused_count": len(unused_measures),
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
>>>>>>> Stashed changes
