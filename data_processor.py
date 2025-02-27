import json

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