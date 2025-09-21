import json
from typing import Any, Dict, List, Optional


class ModelProcessor:
    def __init__(self, json_file_path: str) -> None:
        self.json_file_path = json_file_path
        self._raw_model: Dict[str, Any] = {}
        self._processed = False
        self._tables: List[Dict[str, Any]] = []
        self._relationships: List[Dict[str, Any]] = []
        self._roles: List[Dict[str, Any]] = []
        self._annotations: Dict[str, Any] = {}
        self._measures: List[Dict[str, Any]] = []

    def load(self) -> None:
        if self._processed:
            return

        with open(self.json_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        self._raw_model = data.get("model", {})
        self._extract_annotations()
        self._extract_tables()
        self._extract_relationships()
        self._extract_roles()
        self._processed = True

    def get_tables(self) -> List[Dict[str, Any]]:
        self.load()
        return self._tables

    def get_relationships(self) -> List[Dict[str, Any]]:
        self.load()
        return self._relationships

    def get_roles(self) -> List[Dict[str, Any]]:
        self.load()
        return self._roles

    def get_annotations(self) -> Dict[str, Any]:
        self.load()
        return self._annotations

    def get_measures(self) -> List[Dict[str, Any]]:
        self.load()
        return self._measures

    def _extract_annotations(self) -> None:
        annotations = self._raw_model.get("annotations", [])
        annotation_map: Dict[str, Any] = {}
        for annotation in annotations:
            name = annotation.get("name")
            if not name:
                continue
            annotation_map[name] = annotation.get("value")
        self._annotations = annotation_map

    def _extract_tables(self) -> None:
        tables = self._raw_model.get("tables", [])
        extracted_tables: List[Dict[str, Any]] = []
        all_measures: List[Dict[str, Any]] = []

        for table in tables:
            table_name = table.get("name") or ""
            table_info: Dict[str, Any] = {
                "name": table_name,
                "isHidden": table.get("isHidden", False),
                "description": table.get("description", ""),
                "annotations": self._list_to_annotation_map(table.get("annotations", [])),
                "columns": [],
                "measures": [],
                "partitions": [],
            }

            columns = table.get("columns", [])
            table_info["columns"] = self._extract_columns(columns)

            measures = table.get("measures", [])
            extracted_measures = self._extract_measures(measures, table_name)
            table_info["measures"] = extracted_measures
            all_measures.extend(extracted_measures)

            partitions = table.get("partitions", [])
            table_info["partitions"] = self._extract_partitions(partitions)

            extracted_tables.append(table_info)

        self._tables = extracted_tables
        self._measures = all_measures

    def _extract_relationships(self) -> None:
        relationships = self._raw_model.get("relationships", [])
        extracted: List[Dict[str, Any]] = []
        for rel in relationships:
            rel_info = {
                "name": rel.get("name"),
                "fromTable": rel.get("fromTable"),
                "fromColumn": rel.get("fromColumn"),
                "fromCardinality": rel.get("fromCardinality"),
                "toTable": rel.get("toTable"),
                "toColumn": rel.get("toColumn"),
                "toCardinality": rel.get("toCardinality"),
                "isActive": rel.get("isActive", True),
                "crossFilteringBehavior": rel.get("crossFilteringBehavior"),
                "securityFilteringBehavior": rel.get("securityFilteringBehavior"),
                "joinOnDateBehavior": rel.get("joinOnDateBehavior"),
            }
            extracted.append(rel_info)
        self._relationships = extracted

    def _extract_roles(self) -> None:
        roles = self._raw_model.get("roles", [])
        extracted_roles: List[Dict[str, Any]] = []
        for role in roles:
            role_info = {
                "name": role.get("name"),
                "modelPermission": role.get("modelPermission"),
                "annotations": self._list_to_annotation_map(role.get("annotations", [])),
                "tablePermissions": [],
            }
            table_permissions = []
            for permission in role.get("tablePermissions", []):
                table_permissions.append({
                    "table": permission.get("name"),
                    "filterExpression": permission.get("filterExpression"),
                })
            role_info["tablePermissions"] = table_permissions
            extracted_roles.append(role_info)
        self._roles = extracted_roles

    def _extract_columns(self, columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        extracted_columns: List[Dict[str, Any]] = []
        for column in columns:
            extracted_columns.append({
                "name": column.get("name"),
                "dataType": column.get("dataType"),
                "formatString": column.get("formatString"),
                "dataCategory": column.get("dataCategory"),
                "summarizeBy": column.get("summarizeBy"),
                "description": column.get("description"),
                "isHidden": column.get("isHidden", False),
                "displayFolder": column.get("displayFolder"),
                "annotations": self._list_to_annotation_map(column.get("annotations", [])),
            })
        return extracted_columns

    def _extract_measures(self, measures: List[Dict[str, Any]], table_name: Optional[str]) -> List[Dict[str, Any]]:
        extracted_measures: List[Dict[str, Any]] = []
        for measure in measures:
            expression = "\n".join(measure.get("expression", []))
            extracted_measures.append({
                "table": table_name,
                "name": measure.get("name"),
                "expression": expression.strip(),
                "formatString": measure.get("formatString"),
                "displayFolder": measure.get("displayFolder"),
                "description": measure.get("description"),
                "isHidden": measure.get("isHidden", False),
                "annotations": self._list_to_annotation_map(measure.get("annotations", [])),
            })
        return extracted_measures

    def _extract_partitions(self, partitions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        extracted_partitions: List[Dict[str, Any]] = []
        for partition in partitions:
            partition_info = {
                "name": partition.get("name"),
                "mode": partition.get("mode"),
                "sourceType": None,
                "queryGroup": partition.get("queryGroup"),
            }
            source = partition.get("source", {})
            if source:
                partition_info["sourceType"] = source.get("type")
                if source.get("type") == "m":
                    partition_info["expression"] = "\n".join(source.get("expression", [])).strip()
                else:
                    partition_info["expression"] = source.get("expression")
            extracted_partitions.append(partition_info)
        return extracted_partitions

    def _list_to_annotation_map(self, annotations: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        if not annotations:
            return {}
        result: Dict[str, Any] = {}
        for annotation in annotations:
            name = annotation.get("name")
            if not name:
                continue
            result[name] = annotation.get("value")
        return result
