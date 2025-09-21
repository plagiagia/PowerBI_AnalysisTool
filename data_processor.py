import json
from typing import Any, Dict, List, Optional, Set


class DataProcessor:
    _KNOWN_FEATURE_KEYS = {
        'title', 'background', 'border', 'visualTooltip', 'dropShadow', 'dataColors',
        'labels', 'categoryLabels', 'valueAxis', 'xAxis', 'yAxis', 'legend', 'grid',
        'stylePreset', 'effects', 'general', 'fill', 'line', 'shape', 'image', 'actions',
        'conditionalFormatting'
    }

    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
        self._reset_state()

    def _reset_state(self) -> None:
        self.visuals_data: List[List[str]] = []
        self.theme_info: Dict[str, Any] = {}
        self.bookmark_summaries: List[Dict[str, Any]] = []
        self.visual_layouts: List[Dict[str, Any]] = []
        self.visual_formatting: List[Dict[str, Any]] = []
        self.visual_queries: List[Dict[str, Any]] = []
        self.navigation_items: List[Dict[str, Any]] = []

    def process_json(self) -> None:
        self._reset_state()
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except json.JSONDecodeError:
            print("Error reading or parsing the JSON file.")
            return

        self._extract_config_data(data.get('config'))

        page_filters = json.loads(data.get('filters', '[]'))
        if page_filters:
            filter_name = page_filters[0].get('name', '')
            page_filter_fields = self.extract_filter_fields(page_filters)
            if page_filter_fields:
                self.visuals_data.append(
                    ['All Pages', 'Global Level Filters', filter_name, '', page_filter_fields, '', ''])

        for section in data.get('sections', []):
            self.process_section(section)

    def process_section(self, section: dict) -> None:
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
                expr_name = self._describe_expression(f['expression'])
                if expr_name:
                    filter_fields.append(expr_name)
            if 'filter' in f:
                where_clauses = f['filter'].get('Where', [])
                for clause in where_clauses:
                    condition = clause.get('Condition', {})
                    described = self._describe_expression(condition)
                    if described:
                        filter_fields.append(described)
        return "; ".join(filter_fields)

    def extract_visual_data(self, visual: dict, page_name: str) -> List[str]:
        config = json.loads(visual['config'])

        visual_config = None
        for key in config:
            candidate = config[key]
            if isinstance(candidate, dict) and 'visualType' in candidate:
                visual_config = candidate
                break
        if not visual_config:
            return [page_name, "Unknown visual type", "", "", "", '', '']

        visual_type = visual_config.get('visualType', '')
        visual_name = config.get('name', '')

        self._collect_visual_metadata(page_name, visual_name, visual_type, config, visual_config)

        if 'prototypeQuery' not in visual_config:
            return [page_name, visual_type, visual_name, "", "", '', '']

        entity_aliases = {item['Name']: item['Entity']
                          for item in visual_config['prototypeQuery'].get('From', [])}

        select_fields = self.extract_fields(
            visual_config['prototypeQuery'].get('Select', []), entity_aliases)

        filter_data = visual.get('filters', '[]')
        filter_data = json.loads(filter_data)
        filter_fields = self.extract_filter_fields(filter_data)

        object_data = visual_config.get('objects', {})
        object_fields = self.extract_vc_objects_fields(object_data)

        vc_objects_data = visual_config.get('vcObjects', {})
        vc_objects_fields = self.extract_vc_objects_fields(vc_objects_data)

        prototype_query = visual_config.get('prototypeQuery', {})
        if prototype_query:
            self._record_query_details(page_name, visual_name, visual_type, prototype_query)

        return [page_name, visual_type, visual_name, select_fields, filter_fields, vc_objects_fields, object_fields]

    def extract_objects_fields(self, objects_data: Any) -> str:
        fields: List[str] = []
        if isinstance(objects_data, dict):
            for key, value in objects_data.items():
                if isinstance(value, dict):
                    for inner_key, inner_value in value.items():
                        if inner_key == 'expr' and isinstance(inner_value, dict):
                            extracted = self.extract_expression_fields(inner_value)
                            fields.extend(extracted)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict) and 'expr' in item:
                            extracted = self.extract_expression_fields(item['expr'])
                            fields.extend(extracted)
        return "; ".join(filter(None, fields))

    def extract_expression_fields(self, expr_obj: Any) -> List[str]:
        extracted_fields: List[str] = []
        if isinstance(expr_obj, dict):
            for key, value in expr_obj.items():
                if key in ['Expression', 'Aggregation'] and isinstance(value, dict):
                    if 'Column' in value:
                        column = value['Column']
                        entity = column.get('SourceRef', {}).get('Entity', '')
                        property_name = column.get('Property', '')
                        if entity and property_name:
                            extracted_fields.append(f"{entity}[{property_name}]")
        return extracted_fields

    def extract_vc_objects_fields(self, vc_object: Any, current_entity: Optional[str] = None) -> str:
        fields: List[str] = []
        if isinstance(vc_object, dict):
            for key, value in vc_object.items():
                if isinstance(value, dict):
                    if 'Expression' in value and 'SourceRef' in value['Expression'] and 'Property' in value:
                        entity = value['Expression']['SourceRef'].get('Entity', current_entity)
                        property_name = value['Property']
                        if entity:
                            fields.append(f"{entity}[{property_name}]")
                    else:
                        nested = self.extract_vc_objects_fields(value, current_entity)
                        if nested:
                            fields.extend(nested.split("; "))
                elif isinstance(value, list):
                    for item in value:
                        nested = self.extract_vc_objects_fields(item, current_entity)
                        if nested:
                            fields.extend(nested.split("; "))
        return "; ".join(filter(None, fields))

    def extract_fields(self, fields: List[Dict[str, Any]], entity_aliases: Dict[str, str]) -> str:
        extracted_fields: List[str] = []
        for field in fields:
            if 'Column' in field:
                field_details = field['Column']
            elif 'Aggregation' in field:
                field_details = field['Aggregation']['Expression']['Column']
            elif 'Measure' in field:
                field_details = field['Measure']
            else:
                continue

            source_ref = field_details.get('Expression', {}).get('SourceRef', {})
            entity_alias = source_ref.get('Source')
            entity_name = entity_aliases.get(entity_alias, source_ref.get('Entity', ''))
            property_name = field_details.get('Property', '')

            if entity_name and property_name:
                field_name = f"{entity_name}[{property_name}]"
                extracted_fields.append(field_name)

        return "; ".join(extracted_fields)

    def get_used_measures(self, known_measures: Optional[Set[str]] = None) -> Set[str]:
        used_measures: Set[str] = set()
        lookup = None

        if known_measures:
            lookup = {name.lower(): name for name in known_measures}

        for visual_data in self.visuals_data:
            for index in [3, 4, 5, 6]:
                if index >= len(visual_data):
                    continue

                field_block = visual_data[index]
                if not field_block:
                    continue

                for field in field_block.split('; '):
                    field = field.strip()
                    if not field or '[' not in field or not field.endswith(']'):
                        continue

                    candidate = field[field.rfind('[') + 1:-1].strip()
                    if not candidate:
                        continue

                    if lookup is not None:
                        match = lookup.get(candidate.lower())
                        if match:
                            used_measures.add(match)
                    else:
                        used_measures.add(candidate)

        return used_measures

    def get_theme_info(self) -> Dict[str, Any]:
        return self.theme_info

    def get_bookmarks(self) -> List[Dict[str, Any]]:
        return self.bookmark_summaries

    def get_visual_layouts(self) -> List[Dict[str, Any]]:
        return self.visual_layouts

    def get_visual_queries(self) -> List[Dict[str, Any]]:
        return self.visual_queries

    def get_visual_formatting(self) -> List[Dict[str, Any]]:
        return self.visual_formatting

    def get_navigation_items(self) -> List[Dict[str, Any]]:
        return self.navigation_items

    def _extract_config_data(self, config_payload: Optional[str]) -> None:
        if not config_payload:
            return
        try:
            config_data = json.loads(config_payload)
        except json.JSONDecodeError:
            return

        theme_collection = config_data.get('themeCollection', {})
        self.theme_info = {
            'customTheme': theme_collection.get('customTheme'),
            'baseTheme': theme_collection.get('baseTheme'),
            'activeSectionIndex': config_data.get('activeSectionIndex')
        }

        bookmarks_summary: List[Dict[str, Any]] = []
        for bookmark in config_data.get('bookmarks', []):
            exploration = bookmark.get('explorationState', {})
            sections = exploration.get('sections', {})
            filter_fields = sorted(self._summarize_bookmark_filters(sections))
            visual_count = sum(len(section.get('visualContainers', {})) for section in sections.values())
            bookmarks_summary.append({
                'display_name': bookmark.get('displayName'),
                'name': bookmark.get('name'),
                'target_section': exploration.get('activeSection'),
                'filter_fields': filter_fields,
                'filter_count': len(filter_fields),
                'target_visuals': bookmark.get('options', {}).get('targetVisualNames', []),
                'visual_count': visual_count
            })

        self.bookmark_summaries = bookmarks_summary

    def _summarize_bookmark_filters(self, sections: Dict[str, Any]) -> Set[str]:
        results: Set[str] = set()
        for section in sections.values():
            filter_group = section.get('filters', {})
            for filter_entry in filter_group.get('byExpr', []):
                expression = filter_entry.get('expression')
                described = self._describe_expression(expression)
                if described:
                    results.add(described)

                filter_payload = filter_entry.get('filter', {})
                for clause in filter_payload.get('Where', []):
                    condition = clause.get('Condition', {})
                    described_condition = self._describe_expression(condition)
                    if described_condition:
                        results.add(described_condition)

            for visual in section.get('visualContainers', {}).values():
                visual_filters = visual.get('filters', {}).get('byExpr', [])
                for filter_entry in visual_filters:
                    described = self._describe_expression(filter_entry.get('expression'))
                    if described:
                        results.add(described)
        return results

    def _describe_expression(self, expression: Any) -> Optional[str]:
        if isinstance(expression, dict):
            if 'Measure' in expression:
                return self._describe_measure(expression['Measure'])
            if 'Column' in expression:
                return self._describe_column(expression['Column'])
            if 'Aggregation' in expression:
                return self._describe_expression(expression['Aggregation'])
            if 'Expression' in expression:
                return self._describe_expression(expression['Expression'])
            if 'Condition' in expression:
                return self._describe_expression(expression['Condition'])
            if 'Not' in expression:
                return self._describe_expression(expression['Not'])
            if 'In' in expression:
                for expr in expression['In'].get('Expressions', []):
                    described = self._describe_expression(expr)
                    if described:
                        return described
        return None

    def _describe_measure(self, measure_payload: Dict[str, Any]) -> Optional[str]:
        source_ref = measure_payload.get('Expression', {}).get('SourceRef', {})
        entity = source_ref.get('Entity') or source_ref.get('Source')
        prop = measure_payload.get('Property')
        if entity and prop:
            return f"{entity}[{prop}]"
        return None

    def _describe_column(self, column_payload: Dict[str, Any]) -> Optional[str]:
        source_ref = column_payload.get('Expression', {}).get('SourceRef', {})
        entity = source_ref.get('Entity') or source_ref.get('Source')
        prop = column_payload.get('Property')
        if entity and prop:
            return f"{entity}[{prop}]"
        return None

    def _collect_visual_metadata(self, page_name: str, visual_name: str, visual_type: str,
                                  config: Dict[str, Any], visual_config: Dict[str, Any]) -> None:
        self._record_layout(page_name, visual_name, visual_type, config)
        self._record_navigation(page_name, visual_name, visual_type, visual_config)
        self._record_formatting(page_name, visual_name, visual_type, visual_config)

    def _record_layout(self, page_name: str, visual_name: str, visual_type: str,
                        config: Dict[str, Any]) -> None:
        layouts = config.get('layouts')
        if not isinstance(layouts, list):
            return
        for layout in layouts:
            position = layout.get('position', {})
            if position:
                self.visual_layouts.append({
                    'page': page_name,
                    'visual_name': visual_name,
                    'visual_type': visual_type,
                    'x': position.get('x'),
                    'y': position.get('y'),
                    'width': position.get('width'),
                    'height': position.get('height'),
                    'z': position.get('z'),
                    'tabOrder': position.get('tabOrder')
                })
                break

    def _record_navigation(self, page_name: str, visual_name: str, visual_type: str,
                           visual_config: Dict[str, Any]) -> None:
        reasons: List[str] = []
        nav_types = {'button', 'bookmarkNavigator', 'pageNavigator', 'basicShape', 'shape', 'image', 'textbox'}
        if visual_type in nav_types:
            reasons.append('visualType')
        if visual_config.get('drillFilterOtherVisuals'):
            reasons.append('drillFilterOtherVisuals')
        if 'prototypeQuery' not in visual_config:
            reasons.append('nonQueryVisual')
        if reasons:
            self.navigation_items.append({
                'page': page_name,
                'visual_name': visual_name,
                'visual_type': visual_type,
                'reasons': sorted(set(reasons))
            })

    def _record_formatting(self, page_name: str, visual_name: str, visual_type: str,
                           visual_config: Dict[str, Any]) -> None:
        objects_data = visual_config.get('objects', {})
        vc_objects = visual_config.get('vcObjects', {})
        formatting_summary = {
            'page': page_name,
            'visual_name': visual_name,
            'visual_type': visual_type,
            'has_custom_tooltip': self._contains_key(vc_objects, 'visualTooltip'),
            'has_custom_title': self._contains_key(objects_data, 'title') or self._contains_key(vc_objects, 'title'),
            'has_background': self._contains_key(objects_data, 'background') or self._contains_key(vc_objects, 'background'),
            'has_border': self._contains_key(objects_data, 'border') or self._contains_key(vc_objects, 'border'),
            'has_drop_shadow': self._contains_key(vc_objects, 'dropShadow'),
            'object_features': sorted(self._find_known_keys(objects_data)),
            'vc_object_features': sorted(self._find_known_keys(vc_objects))
        }
        self.visual_formatting.append(formatting_summary)

    def _record_query_details(self, page_name: str, visual_name: str, visual_type: str,
                               prototype_query: Dict[str, Any]) -> None:
        order_by_entries = []
        for entry in prototype_query.get('OrderBy', []):
            direction = entry.get('Direction')
            direction_label = 'DESC' if direction == 2 else 'ASC'
            described = self._describe_expression(entry.get('Expression'))
            if described:
                order_by_entries.append(f"{described} ({direction_label})")

        group_by_entries = []
        for entry in prototype_query.get('GroupBy', []):
            described = self._describe_expression(entry.get('Expression'))
            if described:
                group_by_entries.append(described)

        where_entries = []
        for clause in prototype_query.get('Where', []):
            described = self._describe_expression(clause)
            if described:
                where_entries.append(described)

        top_payload = prototype_query.get('Top')
        top_summary = json.dumps(top_payload) if top_payload else ''

        if not (order_by_entries or group_by_entries or where_entries or top_summary):
            return

        self.visual_queries.append({
            'page': page_name,
            'visual_name': visual_name,
            'visual_type': visual_type,
            'order_by': order_by_entries,
            'group_by': group_by_entries,
            'where': where_entries,
            'top': top_summary
        })

    def _contains_key(self, container: Any, target: str) -> bool:
        if isinstance(container, dict):
            if target in container:
                return True
            return any(self._contains_key(value, target) for value in container.values())
        if isinstance(container, list):
            return any(self._contains_key(item, target) for item in container)
        return False

    def _find_known_keys(self, container: Any) -> Set[str]:
        found: Set[str] = set()
        if isinstance(container, dict):
            for key, value in container.items():
                if key in self._KNOWN_FEATURE_KEYS:
                    found.add(key)
                found.update(self._find_known_keys(value))
        elif isinstance(container, list):
            for item in container:
                found.update(self._find_known_keys(item))
        return found
