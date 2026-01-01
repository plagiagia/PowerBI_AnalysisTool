"""API routes blueprint - REST API endpoints."""

import json
import os

from flask import Blueprint, current_app, jsonify

from utils.processors import load_model_data

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
