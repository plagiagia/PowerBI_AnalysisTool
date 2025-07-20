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
        self.measure_data = {}  # Cache for measure data

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

            # Store all parent measures
            if parent_measures:
                for parent in parent_measures:
                    if parent:
                        self.measures_with_children.add(parent)

            # Store all child measures
            child_measures = measure[self.CHILD_INDEX].split(
                '; ') if measure[self.CHILD_INDEX] else []
            if child_measures:
                for child in child_measures:
                    if child:
                        self.measures_with_children.add(measure_name)

            # Cache the measure data for later use
            self.measure_data[measure_name] = {
                'parent_measures': parent_measures,
                'child_measures': child_measures,
                'dax': measure[self.DAX_EXPRESSION_INDEX],
                'columns': measure[self.COLUMN_INDEX].split('; ') if measure[self.COLUMN_INDEX] else []
            }

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
        """
        Get all measures from the lineage data.
        """
        all_measures = set()
        
        with open(self.tsv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter='\t')
            next(reader)  # Skip the header row
            
            for measure in reader:
                measure_name = measure[self.MEASURE_INDEX]
                all_measures.add(measure_name)
        
        return all_measures

    def get_final_measures(self):
        """
        Get only final measures (measures with no children).
        """
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

    def get_measure_dependencies(self, measure_name):
        """
        Get parent and child measures for a specific measure.
        
        Parameters:
        measure_name (str): Name of the measure to get dependencies for
        
        Returns:
        dict: Dictionary with 'parent_measures', 'child_measures', and 'type'
        """
        # Process data first if not already done
        if not self.measure_data:
            self.process_lineage_data()
            
        # Get the data from our cache if available
        if measure_name in self.measure_data:
            data = self.measure_data[measure_name]
            
            # Determine measure type
            measure_type = "final"
            if data['child_measures'] and not data['parent_measures']:
                measure_type = "parent"
            elif data['child_measures'] and data['parent_measures']:
                measure_type = "intermediate"
                
            return {
                "parent_measures": data['parent_measures'],
                "child_measures": data['child_measures'],
                "columns": data['columns'],
                "type": measure_type
            }
        
        # If not in the cache, return empty data
        return {
            "parent_measures": [],
            "child_measures": [],
            "columns": [],
            "type": "unknown"
        }

    def get_dependency_data(self, measure_names):
        """
        Get dependency data for multiple measures.
        
        Parameters:
        measure_names (list): List of measure names to get dependencies for
        
        Returns:
        dict: Dictionary mapping measure names to their dependencies
        """
        dependency_data = {}
        
        for measure_name in measure_names:
            dependency_data[measure_name] = self.get_measure_dependencies(measure_name)
        
        return dependency_data
        
    def get_full_dependency_chain(self, measure_names):
        """
        Get a complete dependency chain including all related measures.
        This helps with visualizing the entire network of dependencies.
        
        Parameters:
        measure_names (list): Starting list of measure names
        
        Returns:
        dict: Full dependency graph with all related measures
        """
        # Process data first if not already done
        if not self.measure_data:
            self.process_lineage_data()
            
        # Initialize with the starting measures
        all_measures = set(measure_names)
        dependency_data = {}
        
        # First pass: collect all related measures (breadth-first)
        measures_to_process = list(measure_names)
        processed = set()
        
        while measures_to_process:
            current_measure = measures_to_process.pop(0)
            
            if current_measure in processed:
                continue
                
            processed.add(current_measure)
            
            if current_measure in self.measure_data:
                data = self.measure_data[current_measure]
                
                # Add parents to the processing queue
                for parent in data['parent_measures']:
                    if parent and parent not in processed:
                        all_measures.add(parent)
                        measures_to_process.append(parent)
                
                # Add children to the processing queue
                for child in data['child_measures']:
                    if child and child not in processed:
                        all_measures.add(child)
                        measures_to_process.append(child)
        
        # Second pass: get dependency data for all collected measures
        for measure in all_measures:
            dependency_data[measure] = self.get_measure_dependencies(measure)
            
        return dependency_data

    def get_comprehensive_unused_measures(self, used_measures_set):
        """
        Get ALL measures that would be safe to remove, including measures that
        would become unused after removing their child measures.
        
        This is the improved logic that detects the complete chain of unused measures.
        
        Parameters:
        used_measures_set (set): Set of measures that are used in visuals
        
        Returns:
        dict: Dictionary with comprehensive analysis including:
            - all_unused: All measures safe to remove
            - deletion_chain: The order in which measures become unused
            - impact_analysis: Details about each measure's impact
        """
        # Process data first if not already done
        if not self.measure_data:
            self.process_lineage_data()
        
        all_measures = self.get_all_measures()
        
        # Start with measures not used in any visuals
        unused_measures = all_measures - used_measures_set
        
        # Build a reverse dependency map (child -> parents)
        child_to_parents = {}
        for measure_name, data in self.measure_data.items():
            for child in data['child_measures']:
                if child:
                    if child not in child_to_parents:
                        child_to_parents[child] = set()
                    child_to_parents[child].add(measure_name)
        
        # Iteratively find all measures that would become unused
        deletion_chain = []
        all_unused = set(unused_measures)
        measures_to_check = list(unused_measures)
        
        while measures_to_check:
            current_unused = set(measures_to_check)
            measures_to_check = []
            
            for unused_measure in current_unused:
                # Check all parents of this unused measure
                if unused_measure in child_to_parents:
                    for parent in child_to_parents[unused_measure]:
                        if parent not in all_unused and parent not in used_measures_set:
                            # Check if ALL children of this parent are unused
                            parent_data = self.measure_data.get(parent, {})
                            children = parent_data.get('child_measures', [])
                            
                            # Filter out empty strings
                            children = [c for c in children if c]
                            
                            if children and all(child in all_unused for child in children):
                                # This parent would become unused after removing its children
                                all_unused.add(parent)
                                measures_to_check.append(parent)
            
            if current_unused:
                deletion_chain.append(list(current_unused))
        
        # Build impact analysis
        impact_analysis = {}
        for measure in all_unused:
            data = self.measure_data.get(measure, {})
            
            # Determine why this measure is unused
            if measure not in used_measures_set:
                if not data.get('child_measures'):
                    reason = "Leaf measure not used in any visual"
                else:
                    reason = "Not used in visuals and all children are unused"
            else:
                reason = "Would become unused after removing child measures"
            
            impact_analysis[measure] = {
                'type': self._get_measure_type(data),
                'parent_measures': data.get('parent_measures', []),
                'child_measures': data.get('child_measures', []),
                'reason': reason,
                'safe_to_remove': True
            }
        
        return {
            'all_unused': sorted(list(all_unused)),
            'deletion_chain': deletion_chain,
            'impact_analysis': impact_analysis,
            'total_unused': len(all_unused),
            'immediate_unused': len(unused_measures),
            'cascade_unused': len(all_unused) - len(unused_measures)
        }
    
    def _get_measure_type(self, measure_data):
        """Helper to determine measure type"""
        has_parents = bool(measure_data.get('parent_measures'))
        has_children = bool(measure_data.get('child_measures'))
        
        if not has_parents and has_children:
            return "parent"
        elif has_parents and not has_children:
            return "final"
        elif has_parents and has_children:
            return "intermediate"
        else:
            return "isolated"

    def analyze_deletion_impact(self, measure_names):
        """
        Analyze what happens if we delete these measures.
        
        Parameters:
        measure_names (list): List of measure names to consider for deletion
        
        Returns:
        dict: Deletion analysis with chains and impact
        """
        # Process data first if not already done
        if not self.measure_data:
            self.process_lineage_data()
            
        # Start with the selected measures as level 1
        chain = {
            "level1": list(measure_names),
            "level2": [],
            "level3": []
        }
        
        # Collect all measures that reference our level 1 measures
        level2_candidates = set()
        
        for measure in self.measure_data:
            data = self.measure_data[measure]
            
            # Skip if this is in our level 1
            if measure in measure_names:
                continue
                
            # Check if this measure depends on any level 1 measure
            for parent in data['parent_measures']:
                if parent in measure_names:
                    level2_candidates.add(measure)
                    break
        
        # Filter level 2 candidates - only include ones where ALL parents are in level 1
        for candidate in level2_candidates:
            data = self.measure_data[candidate]
            all_parents_in_level1 = True
            
            for parent in data['parent_measures']:
                if parent not in measure_names:
                    all_parents_in_level1 = False
                    break
                    
            if all_parents_in_level1:
                chain["level2"].append(candidate)
        
        # Now similarly for level 3 - measures that depend only on level 1 and level 2
        level3_candidates = set()
        
        for measure in self.measure_data:
            data = self.measure_data[measure]
            
            # Skip if already in level 1 or 2
            if measure in measure_names or measure in chain["level2"]:
                continue
                
            # Check if this measure depends on any level 2 measure
            for parent in data['parent_measures']:
                if parent in chain["level2"]:
                    level3_candidates.add(measure)
                    break
        
        # Filter level 3 candidates - only include ones where ALL parents are in level 1 or 2
        all_previous_levels = set(measure_names) | set(chain["level2"])
        
        for candidate in level3_candidates:
            data = self.measure_data[candidate]
            all_parents_in_previous_levels = True
            
            for parent in data['parent_measures']:
                if parent not in all_previous_levels:
                    all_parents_in_previous_levels = False
                    break
                    
            if all_parents_in_previous_levels:
                chain["level3"].append(candidate)
        
        # Calculate impact score - more complex formulas could be used
        impact_score = len(chain["level1"]) + len(chain["level2"])*2 + len(chain["level3"])*3
        
        return {
            "chain": chain,
            "impact_score": impact_score,
            "total_measures": len(chain["level1"]) + len(chain["level2"]) + len(chain["level3"])
        }