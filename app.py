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
from config import get_config
from ai_utils import get_ai_service

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
    
    # No need to set default paths - they are already in the config file

    @app.teardown_appcontext
    def teardown(exception: Optional[BaseException] = None) -> None:
        """Clean up resources stored in g."""
        g.pop('data_processor', None)
        g.pop('lineage_view_processor', None)

    def get_data_processor() -> DataProcessor:
        """
        Retrieve or create the DataProcessor instance for this request.
        """
        if not hasattr(g, 'data_processor'):
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
        
        # Filter visuals that have fields and are not filter visuals
        excluded_types = {"Page Level Filters", "Global Level Filters"}
        valid_visuals = [
            row for row in dp.visuals_data 
            if len(row) > 3 and row[3] and row[1] and row[1] not in excluded_types
        ]
        
        # Extract visual types and count
        visual_types = [row[1] for row in valid_visuals]
        visual_count = len(visual_types)
        
        # Find most common visual type
        most_common_visual = "None"
        if visual_types:
            counter = collections.Counter(visual_types)
            most_common_visual = counter.most_common(1)[0][0]
        
        # Extract unique pages
        unique_pages = {row[0] for row in dp.visuals_data if row and row[0]}
        
        # Get measures
        all_measures = lvp.get_all_measures()
        used_measures = dp.get_used_measures()
        final_measures = lvp.get_final_measures()
        unused_final_measures = final_measures - used_measures
        
        return {
            "visual_count": visual_count,
            "page_count": len(unique_pages),
            "measure_count": len(all_measures),
            "unused_count": len(unused_final_measures),
            "most_common_visual": most_common_visual
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
        return render_template('table_view.html', table_data=dp.visuals_data)

    @app.route('/lineage-view')
    def lineage_view_route() -> str:
        # Check if the feature is enabled in config
        if not app.config.get('ENABLE_LINEAGE_VIEW', True):
            abort(404, description="This feature is currently disabled.")
            
        lvp = get_lineage_view_processor()
        return render_template(
            'lineage_view.html',
            nodes=lvp.nodes,
            edges=lvp.edges
        )

    @app.route('/dax-expressions')
    def dax_expressions() -> str:
        # Check if the feature is enabled in config
        if not app.config.get('ENABLE_DAX_EXPLORER', True):
            abort(404, description="This feature is currently disabled.")
            
        lvp = get_lineage_view_processor()
        dax_expr = lvp.extract_dax_expressions()
        return render_template('dax_expressions.html', dax_expressions=dax_expr)

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

        # Get used measures
        used_measures = dp.get_used_measures()
        
        # Get final measures
        final_measures = lvp.get_final_measures()
        
        # Calculate unused final measures
        unused_final_measures = sorted(list(final_measures - used_measures))

        return render_template('unused_measures.html', unused_measures=unused_final_measures)
        
    # AI Analysis Routes
    @app.route('/ai-analysis')
    def ai_analysis() -> str:
        """Render the AI analysis page."""
        # Check if AI features are enabled in config
        if not app.config.get('ENABLE_AI_FEATURES', True):
            abort(404, description="AI features are currently disabled.")
            
        return render_template('ai_analysis.html')
    
    @app.route('/ai-analysis/dax', methods=['POST'])
    def analyze_dax() -> str:
        """Analyze a DAX expression using AI."""
        # Check if AI features are enabled in config
        if not app.config.get('ENABLE_AI_FEATURES', True):
            abort(404, description="AI features are currently disabled.")
            
        dax_expression = request.form.get('daxExpression', '')
        if not dax_expression:
            return render_template('ai_analysis.html', 
                                  dax_analysis_result="Please provide a DAX expression to analyze.")
        
        try:
            ai_service = get_ai_service()
            result = ai_service.analyze_dax(dax_expression)
            # Convert markdown to HTML for better formatting (ensure result is a string)
            result_html = markdown.markdown(str(result))
            return render_template('ai_analysis.html', dax_analysis_result=result_html)
        except Exception as e:
            current_app.logger.error(f"Error analyzing DAX expression: {e}")
            return render_template('ai_analysis.html', 
                                  dax_analysis_result=f"Error analyzing DAX expression: {str(e)}")
    
    @app.route('/ai-analysis/suggest-measures', methods=['POST'])
    def suggest_measures() -> str:
        """Suggest DAX measures based on a business question."""
        # Check if AI features are enabled in config
        if not app.config.get('ENABLE_AI_FEATURES', True):
            abort(404, description="AI features are currently disabled.")
            
        table_schema = request.form.get('tableSchema', '')
        business_question = request.form.get('businessQuestion', '')
        
        if not table_schema or not business_question:
            return render_template('ai_analysis.html', 
                                  measure_suggestion_result="Please provide both table schema and business question.")
        
        try:
            ai_service = get_ai_service()
            result = ai_service.suggest_measures(table_schema, business_question)
            # Convert markdown to HTML for better formatting (ensure result is a string)
            result_html = markdown.markdown(str(result))
            return render_template('ai_analysis.html', measure_suggestion_result=result_html)
        except Exception as e:
            current_app.logger.error(f"Error suggesting measures: {e}")
            return render_template('ai_analysis.html', 
                                  measure_suggestion_result=f"Error suggesting measures: {str(e)}")
    
    @app.route('/ai-analysis/model-relationships', methods=['POST'])
    def analyze_model_relationships() -> str:
        """Analyze model relationships using AI."""
        # Check if AI features are enabled in config
        if not app.config.get('ENABLE_AI_FEATURES', True):
            abort(404, description="AI features are currently disabled.")
            
        model_json = request.form.get('modelJson', '')
        
        if not model_json:
            return render_template('ai_analysis.html', 
                                  model_analysis_result="Please provide model JSON to analyze.")
        
        try:
            ai_service = get_ai_service()
            result = ai_service.explain_model_relationships(model_json)
            # Convert markdown to HTML for better formatting (ensure result is a string)
            result_html = markdown.markdown(str(result))
            return render_template('ai_analysis.html', model_analysis_result=result_html)
        except Exception as e:
            current_app.logger.error(f"Error analyzing model relationships: {e}")
            return render_template('ai_analysis.html', 
                                  model_analysis_result=f"Error analyzing model relationships: {str(e)}")
    
    @app.route('/ai-analysis/assistant', methods=['POST'])
    def ai_assistant() -> str:
        """General Power BI assistant using AI."""
        # Check if AI features are enabled in config
        if not app.config.get('ENABLE_AI_FEATURES', True):
            abort(404, description="AI features are currently disabled.")
            
        question = request.form.get('question', '')
        
        if not question:
            return render_template('ai_analysis.html', 
                                  assistant_result="Please provide a question to answer.")
        
        try:
            ai_service = get_ai_service()
            system_prompt = """
            You are a Power BI expert assistant. Provide helpful, accurate, and concise answers 
            to questions about Power BI. Include examples where appropriate and focus on best practices.
            """
            result = ai_service.generate_text(question, system_prompt=system_prompt)
            # Convert markdown to HTML for better formatting (ensure result is a string)
            result_html = markdown.markdown(str(result))
            return render_template('ai_analysis.html', assistant_result=result_html)
        except Exception as e:
            current_app.logger.error(f"Error with AI assistant: {e}")
            return render_template('ai_analysis.html', 
                                  assistant_result=f"Error with AI assistant: {str(e)}")
    
    @app.route('/api/analyze-m-query', methods=['POST'])
    def analyze_m_query():
        """API endpoint to analyze an M query using AI."""
        # Check if AI features are enabled in config
        if not app.config.get('ENABLE_AI_FEATURES', True):
            return jsonify({"error": "AI features are currently disabled."}), 404
            
        try:
            data = request.json
            if not data or 'query' not in data:
                return jsonify({"error": "No query provided"}), 400
                
            m_query = data['query']
            table_name = data.get('tableName', 'Unknown Table')
            
            ai_service = get_ai_service()
            result = ai_service.analyze_m_query(m_query)
            
            # Add table name to the result
            result['tableName'] = table_name
            
            return jsonify(result)
        except Exception as e:
            current_app.logger.error(f"Error analyzing M query: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/optimize-dax', methods=['POST'])
    def optimize_dax():
        """API endpoint to optimize a DAX measure using AI."""
        # Check if AI features are enabled in config
        if not app.config.get('ENABLE_AI_FEATURES', True):
            return jsonify({"error": "AI features are currently disabled."}), 404
            
        try:
            data = request.json
            if not data or 'dax' not in data:
                return jsonify({"error": "No DAX expression provided"}), 400
                
            dax_expression = data['dax']
            measure_name = data.get('measureName', '')
            
            ai_service = get_ai_service()
            result = ai_service.optimize_dax_measure(dax_expression, measure_name)
            
            return jsonify({"optimized_dax": result})
        except Exception as e:
            current_app.logger.error(f"Error optimizing DAX measure: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/explain-dax', methods=['POST'])
    def explain_dax():
        """API endpoint to explain a DAX measure using AI."""
        # Check if AI features are enabled in config
        if not app.config.get('ENABLE_AI_FEATURES', True):
            return jsonify({"error": "AI features are currently disabled."}), 404
            
        try:
            data = request.json
            if not data or 'dax' not in data:
                return jsonify({"error": "No DAX expression provided"}), 400
                
            dax_expression = data['dax']
            measure_name = data.get('measureName', '')
            
            ai_service = get_ai_service()
            result = ai_service.explain_dax_measure(dax_expression, measure_name)
            
            return jsonify({"explanation": result})
        except Exception as e:
            current_app.logger.error(f"Error explaining DAX measure: {e}")
            return jsonify({"error": str(e)}), 500
    
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
