import csv

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