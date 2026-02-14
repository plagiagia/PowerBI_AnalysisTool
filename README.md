# Power BI Analysis Tool

Power BI Analysis Tool is a Flask application for offline analysis of exported Power BI artifacts. It helps you inspect report structure, semantic model quality, DAX dependencies, and source-query lineage in one local web interface.

## Highlights

- Report and model health dashboard with prioritized issues
- File readiness and validation checks
- Visual field inventory with filtering and export
- Measure lineage graph and dependency drill-down
- DAX expression explorer
- Source (M) query explorer with table-reference mapping
- Unused-measure analysis with cascade impact simulation
- Model insights for tables, relationships, roles, and metadata gaps
- Report insights for bookmarks, layout, query patterns, and formatting
- Lightweight JSON API for model and lineage node details

## Technology Stack

- Python 3.9+
- Flask 3.1
- Jinja2 templates
- Vanilla JavaScript/CSS frontend

## Required Input Files

Place these files in the `data/` directory:

1. `data/report.json`
2. `data/MeasureDependencies.tsv`
3. `data/model.json`

`MeasureDependencies.tsv` must include this header row:

```tsv
Measure	DAXExpression	ParentMeasures	ChildMeasures	Table	Columns
```

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/plagiagia/PowerBI_AnalysisTool.git
cd PowerBI_AnalysisTool
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Add required Power BI export files to `data/`.

5. Run the application:
```bash
python app.py
```

6. Open:
```text
http://localhost:5000
```

## Application Routes

### Main Workflow

- `/`: Workbench health dashboard
- `/upload-validate`: Input file checks and parse validation
- `/explore`: Tool navigation hub
- `/impact-simulator`: Simulated measure cleanup impact
- `/exports`: Export handoff center

### Analysis

- `/table-view`: Visual fields explorer
- `/lineage-view`: Measure lineage graph
- `/dax-expressions`: DAX expression browser
- `/unused-measures`: Unused-measure analysis

### Insights

- `/report-insights`: Report structure and UX insights

### Sources

- `/source-explorer`: M-query inventory and dependency mapping

### API

- `GET /api/model-json`: Returns the current `model.json` payload
- `GET /api/lineage-node?name=<node>`: Returns lineage details for a node/measure

## Configuration

Configuration is defined in `config.py`.

- `FLASK_DEBUG=1` enables development mode.
- `FLASK_ENV=production` selects production config.
- `SECRET_KEY` is required in production and validated at startup.
- Input file paths are configured through:
  - `REPORT_JSON_PATH`
  - `MEASURE_DEPENDENCIES_TSV_PATH`
  - `MODEL_JSON_PATH`
- Feature flags are available in config classes:
  - `ENABLE_REPORT_INSIGHTS`
  - `ENABLE_SOURCE_EXPLORER`
  - `ENABLE_DAX_EXPLORER`
  - `ENABLE_LINEAGE_VIEW`

## Project Structure

```text
PowerBI_AnalysisTool/
|-- app.py
|-- config.py
|-- data_processor.py
|-- lineage_view.py
|-- model_processor.py
|-- routes/
|-- templates/
|-- static/
|-- tests/
|-- data/
|-- requirements.txt
`-- README.md
```

## Running Tests

```bash
python -m unittest discover -s tests
```

## Troubleshooting

- Missing-file errors:
  - Confirm `report.json`, `MeasureDependencies.tsv`, and `model.json` exist in `data/`.
- Empty results on analysis pages:
  - Verify exported files are valid JSON/TSV and contain expected content.
- Production startup failure:
  - Set `SECRET_KEY` before launching with production configuration.

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Implement and test changes.
4. Open a pull request with a clear description.

## License

This project is licensed under a custom non-commercial license. See `LICENSE` for full terms.
