import json
import os
import tempfile
import unittest

from data_processor import DataProcessor
from lineage_view import LineageView


def _write_json(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(payload, file)


def _write_text(path: str, payload: str) -> None:
    with open(path, "w", encoding="utf-8") as file:
        file.write(payload)


def _build_report(select_entries, visual_filters=None) -> dict:
    visual_config = {
        "name": "Visual1",
        "singleVisual": {
            "visualType": "card",
            "prototypeQuery": {
                "From": [{"Name": "s", "Entity": "Sales"}],
                "Select": select_entries,
            },
        },
    }

    visual_payload = {
        "config": json.dumps(visual_config),
        "filters": json.dumps(visual_filters or []),
    }

    return {
        "name": "Unit Test Report",
        "config": "{}",
        "filters": "[]",
        "sections": [
            {
                "displayName": "Page 1",
                "filters": "[]",
                "visualContainers": [visual_payload],
            }
        ],
    }


def _measure_select(prop: str) -> dict:
    return {
        "Measure": {
            "Expression": {"SourceRef": {"Source": "s"}},
            "Property": prop,
        }
    }


def _column_select(prop: str) -> dict:
    return {
        "Column": {
            "Expression": {"SourceRef": {"Source": "s"}},
            "Property": prop,
        }
    }


def _aggregation_select(prop: str) -> dict:
    return {
        "Aggregation": {
            "Expression": {
                "Column": {
                    "Expression": {"SourceRef": {"Source": "s"}},
                    "Property": prop,
                }
            }
        }
    }


class UnusedMeasuresLogicTests(unittest.TestCase):
    def test_qualified_measure_name_is_detected_as_used(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "report.json")
            lineage_path = os.path.join(temp_dir, "MeasureDependencies.tsv")

            _write_json(report_path, _build_report([_measure_select("Total Sales")]))
            _write_text(
                lineage_path,
                "\n".join(
                    [
                        "Measure\tDAXExpression\tParentMeasures\tChildMeasures\tTable\tColumns",
                        "'Sales'[Total Sales]\tSUM('Sales'[Amount])\t\t\tSales\tSales[Amount]",
                    ]
                )
                + "\n",
            )

            dp = DataProcessor(report_path)
            dp.process_json()

            lvp = LineageView(lineage_path)
            lvp.process_lineage_data()

            known_measures = set(lvp.measure_data)
            used_measures = dp.get_used_measures(known_measures)
            expanded_used = lvp.expand_used_measures(used_measures)
            unused_analysis = lvp.get_comprehensive_unused_measures(expanded_used)

            self.assertIn("'Sales'[Total Sales]", used_measures)
            self.assertEqual([], unused_analysis["all_unused"])

    def test_measure_in_filter_condition_is_detected_as_used(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "report.json")

            visual_filters = [
                {
                    "filter": {
                        "Where": [
                            {
                                "Condition": {
                                    "Comparison": {
                                        "Left": {
                                            "Measure": {
                                                "Expression": {"SourceRef": {"Entity": "Sales"}},
                                                "Property": "Threshold",
                                            }
                                        },
                                        "Right": {"Literal": {"Value": "100L"}},
                                    }
                                }
                            }
                        ]
                    }
                }
            ]

            _write_json(
                report_path,
                _build_report(
                    select_entries=[_column_select("Amount")],
                    visual_filters=visual_filters,
                ),
            )

            dp = DataProcessor(report_path)
            dp.process_json()
            used_measures = dp.get_used_measures({"Threshold"})

            self.assertEqual({"Threshold"}, used_measures)

    def test_column_name_collision_does_not_mark_measure_as_used(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = os.path.join(temp_dir, "report.json")
            _write_json(report_path, _build_report([_aggregation_select("Amount")]))

            dp = DataProcessor(report_path)
            dp.process_json()
            used_measures = dp.get_used_measures({"Amount"})

            self.assertEqual(set(), used_measures)


if __name__ == "__main__":
    unittest.main()
