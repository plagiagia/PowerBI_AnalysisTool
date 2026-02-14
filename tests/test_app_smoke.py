import json
import os
import tempfile
import unittest
from unittest.mock import patch

from app import create_app
from config import DevelopmentConfig, ProductionConfig, get_config


def _write_json(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file)


def _write_text(path: str, payload: str) -> None:
    with open(path, "w", encoding="utf-8") as file:
        file.write(payload)


class ConfigRegressionTests(unittest.TestCase):
    def test_get_config_returns_instance(self) -> None:
        with patch.dict(os.environ, {"FLASK_ENV": "", "FLASK_DEBUG": ""}, clear=False):
            cfg = get_config()
        self.assertIsInstance(cfg, DevelopmentConfig)

    def test_production_requires_secret_key(self) -> None:
        with patch.dict(
            os.environ,
            {"FLASK_ENV": "production", "FLASK_DEBUG": "", "SECRET_KEY": ""},
            clear=False,
        ):
            with self.assertRaises(ValueError):
                get_config()

    def test_create_app_instantiates_config_classes(self) -> None:
        with patch.dict(os.environ, {"SECRET_KEY": ""}, clear=False):
            with self.assertRaises(ValueError):
                create_app(ProductionConfig)


class RouteSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = self.temp_dir.name

        report_path = os.path.join(self.data_dir, "report.json")
        model_path = os.path.join(self.data_dir, "model.json")
        lineage_path = os.path.join(self.data_dir, "MeasureDependencies.tsv")

        _write_json(
            report_path,
            {
                "name": "Smoke Test Report",
                "config": "{}",
                "filters": "[]",
                "sections": [],
            },
        )

        _write_json(
            model_path,
            {
                "model": {
                    "tables": [
                        {
                            "name": "Sales",
                            "columns": [{"name": "Amount", "dataType": "double"}],
                            "measures": [
                                {
                                    "name": "Total Sales",
                                    "expression": ["SUM(Sales[Amount])"],
                                    "formatString": "$#,0.00",
                                }
                            ],
                            "partitions": [
                                {
                                    "name": "Sales",
                                    "source": {
                                        "type": "m",
                                        "expression": [
                                            "let",
                                            "    Source = #table({\"Amount\"}, {{1}})",
                                            "in",
                                            "    Source",
                                        ],
                                    },
                                }
                            ],
                        }
                    ],
                    "relationships": [],
                    "roles": [],
                    "annotations": [],
                }
            },
        )

        _write_text(
            lineage_path,
            "\n".join(
                [
                    "Measure\tDAXExpression\tParentMeasures\tChildMeasures\tTable\tColumns",
                    "Total Sales\tSUM(Sales[Amount])\t\t\tSales\tSales[Amount]",
                ]
            )
            + "\n",
        )

        class TempConfig(DevelopmentConfig):
            DEBUG = False
            TESTING = True
            REPORT_JSON_PATH = report_path
            MODEL_JSON_PATH = model_path
            MEASURE_DEPENDENCIES_TSV_PATH = lineage_path

        self.app = create_app(TempConfig())
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_primary_routes_return_success(self) -> None:
        routes = [
            "/",
            "/upload-validate",
            "/explore",
            "/table-view",
            "/lineage-view",
            "/dax-expressions",
            "/unused-measures",
            "/impact-simulator",
            "/exports",
            "/report-insights",
            "/source-explorer",
            "/api/model-json",
            "/api/lineage-node?name=Total%20Sales",
        ]
        for route in routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)

    def test_removed_action_center_route_returns_404(self) -> None:
        removed_routes = [
            "/issues",
            "/model-insights",
        ]
        for route in removed_routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
