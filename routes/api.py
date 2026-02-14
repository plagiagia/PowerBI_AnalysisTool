"""API routes blueprint - REST API endpoints."""

import json
import os

from flask import Blueprint, current_app, jsonify, request

from utils.processors import get_lineage_view_processor, load_model_data

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/model-json', methods=['GET'])
def get_model_json():
    """API endpoint to get the current model JSON."""
    try:
        model_path = current_app.config['MODEL_JSON_PATH']
        if not os.path.exists(model_path):
            current_app.logger.error(f"Model file not found: {model_path}")
            return jsonify({"error": "Model file not found"}), 404

        model_data = load_model_data(model_path)
        return jsonify(model_data)
    except json.JSONDecodeError as e:
        current_app.logger.error(f"Invalid JSON in model file: {e}")
        return jsonify({"error": "Invalid model file format"}), 500
    except IOError as e:
        current_app.logger.error(f"Error reading model file: {e}")
        return jsonify({"error": "Error reading model file"}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error loading model JSON: {e}")
        return jsonify({"error": "Internal server error"}), 500


@api_bp.route('/lineage-node', methods=['GET'])
def get_lineage_node_details():
    """API endpoint to fetch lineage detail for a specific node."""
    node_name = (request.args.get('name') or '').strip()
    if not node_name:
        return jsonify({"error": "Missing node name"}), 400

    try:
        lvp = get_lineage_view_processor()
        if node_name in lvp.measure_data:
            details = lvp.get_measure_dependencies(node_name)
            dax = lvp.measure_data.get(node_name, {}).get('dax', '')
            return jsonify({
                "name": node_name,
                "node_type": details.get('type', 'unknown'),
                "parent_measures": details.get('parent_measures', []),
                "child_measures": details.get('child_measures', []),
                "columns": details.get('columns', []),
                "dax": dax
            })

        # Columns and unknown nodes do not have measure metadata
        return jsonify({
            "name": node_name,
            "node_type": "column",
            "parent_measures": [],
            "child_measures": [],
            "columns": [],
            "dax": ""
        })
    except Exception as e:
        current_app.logger.error(f"Unexpected error loading lineage node '{node_name}': {e}")
        return jsonify({"error": "Internal server error"}), 500
