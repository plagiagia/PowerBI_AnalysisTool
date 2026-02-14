import csv
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class LineageView:
    """Process and analyze measure lineage data from TSV files."""

    # Column indices for the TSV file
    MEASURE_INDEX = 0
    DAX_EXPRESSION_INDEX = 1
    PARENT_INDEX = 2
    CHILD_INDEX = 3
    COLUMN_INDEX = 5

    def __init__(self, tsv_file_path: str) -> None:
        self.tsv_file_path = tsv_file_path
        self.nodes: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, str]] = []
        self.measures_with_children: Set[str] = set()
        self.unique_edges: Set[Tuple[str, str]] = set()
        self.unique_columns: Set[str] = set()
        self.unique_measure_nodes: Set[str] = set()
        self.measure_data: Dict[str, Dict[str, Any]] = {}
        self._all_measures_cache: Optional[Set[str]] = None
        self._final_measures_cache: Optional[Set[str]] = None
        self._data_loaded: bool = False

    def _iter_tsv_rows(self):
        """Yield TSV rows with robust error handling."""
        try:
            with open(self.tsv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter='\t')
                next(reader, None)  # Skip the header row if it exists
                for row in reader:
                    yield row
        except FileNotFoundError:
            logger.error(f"Lineage file not found: {self.tsv_file_path}")
            raise ValueError(f"Lineage file not found: {self.tsv_file_path}")
        except IOError as e:
            logger.error(f"Error reading lineage file {self.tsv_file_path}: {e}")
            raise ValueError(f"Error reading lineage file: {e}")
        except csv.Error as e:
            logger.error(f"Error parsing TSV file {self.tsv_file_path}: {e}")
            raise ValueError(f"Error parsing lineage file: {e}")

    def process_lineage_data(self) -> None:
        """Process lineage data from the TSV file."""
        if self._data_loaded:
            return

        for measure in self._iter_tsv_rows():
            if len(measure) <= self.COLUMN_INDEX:
                logger.warning(f"Skipping malformed row: {measure}")
                continue

            measure_name = (measure[self.MEASURE_INDEX] or '').strip()
            if not measure_name:
                continue

            dax_expression = measure[self.DAX_EXPRESSION_INDEX] if len(measure) > self.DAX_EXPRESSION_INDEX else ''

            if measure_name not in self.unique_measure_nodes:
                self.nodes.append({
                    'id': measure_name,
                    'label': measure_name,
                    'dax': dax_expression
                })
                self.unique_measure_nodes.add(measure_name)

            parent_measures = self._parse_list_field(measure[self.PARENT_INDEX])
            child_measures = self._parse_list_field(measure[self.CHILD_INDEX])
            columns = self._parse_list_field(measure[self.COLUMN_INDEX])

            # Track measures that have children
            for parent in parent_measures:
                self.measures_with_children.add(parent)

            if child_measures:
                self.measures_with_children.add(measure_name)

            # Cache measure data for later use
            existing = self.measure_data.get(measure_name)
            if existing:
                merged_parents = sorted(set(existing.get('parent_measures', [])) | set(parent_measures))
                merged_children = sorted(set(existing.get('child_measures', [])) | set(child_measures))
                merged_columns = sorted(set(existing.get('columns', [])) | set(columns))
                merged_dax = existing.get('dax') or dax_expression
                self.measure_data[measure_name] = {
                    'parent_measures': merged_parents,
                    'child_measures': merged_children,
                    'dax': merged_dax,
                    'columns': merged_columns
                }
            else:
                self.measure_data[measure_name] = {
                    'parent_measures': parent_measures,
                    'child_measures': child_measures,
                    'dax': dax_expression,
                    'columns': columns
                }

            # Process columns
            for column in columns:
                if column not in self.unique_columns:
                    self.nodes.append({
                        'id': column,
                        'label': column,
                        'type': 'column'
                    })
                    self.unique_columns.add(column)

                edge = (column, measure_name)
                if edge not in self.unique_edges:
                    self.unique_edges.add(edge)
                    self.edges.append({'from': column, 'to': measure_name})

            # Process parent-child relationships
            for parent in parent_measures:
                edge = (parent, measure_name)
                if edge not in self.unique_edges:
                    self.unique_edges.add(edge)
                    self.edges.append({'from': parent, 'to': measure_name})

        self._data_loaded = True
        logger.debug(f"Loaded {len(self.nodes)} nodes and {len(self.edges)} edges from lineage data")

    def _parse_list_field(self, field: str) -> List[str]:
        """Parse a semicolon-separated field into a list of non-empty strings."""
        if not field:
            return []
        return [item.strip() for item in re.split(r'\s*;\s*', field) if item.strip()]

    def extract_dax_expressions(self) -> List[Tuple[str, str]]:
        """Extract DAX expressions from all measures."""
        self.process_lineage_data()

        dax_expressions: List[Tuple[str, str]] = []
        for label, data in self.measure_data.items():
            dax_expression = data.get('dax', '')

            if label and dax_expression:
                # Replace escape sequences with their corresponding characters
                dax_expression = dax_expression.replace('\\n', '\n')
                dax_expression = dax_expression.replace('\\t', '\t')
                dax_expression = dax_expression.replace('\\r', '\r')
                dax_expressions.append((label, dax_expression))

        return dax_expressions

    def get_all_measures(self) -> Set[str]:
        """Get all measures from the lineage data (cached)."""
        if self._all_measures_cache is not None:
            return self._all_measures_cache

        self.process_lineage_data()
        self._all_measures_cache = set(self.measure_data.keys())
        return self._all_measures_cache

    def expand_used_measures(self, used_measures: Optional[Set[str]]) -> Set[str]:
        """Expand a set of measures used in visuals to include all upstream dependencies."""
        self.process_lineage_data()

        expanded: Set[str] = set()
        stack = list(used_measures or [])

        while stack:
            measure = stack.pop()
            if not measure or measure in expanded:
                continue

            expanded.add(measure)
            data = self.measure_data.get(measure)
            if not data:
                continue

            for parent in data.get('parent_measures', []):
                parent = (parent or '').strip()
                if parent and parent not in expanded:
                    stack.append(parent)

        return expanded

    def get_final_measures(self) -> Set[str]:
        """Get only final measures (measures with no children) - cached."""
        if self._final_measures_cache is not None:
            return self._final_measures_cache

        self.process_lineage_data()

        final_measures: Set[str] = set()
        parent_measures: Set[str] = set()

        for measure_name, data in self.measure_data.items():
            child_measures = data.get('child_measures', [])

            if not child_measures:
                final_measures.add(measure_name)
            else:
                parent_measures.add(measure_name)

        self._final_measures_cache = final_measures - parent_measures
        return self._final_measures_cache

    def get_measure_dependencies(self, measure_name: str) -> Dict[str, Any]:
        """Get parent and child measures for a specific measure."""
        self.process_lineage_data()

        if measure_name in self.measure_data:
            data = self.measure_data[measure_name]

            # Determine measure type
            has_parents = bool(data['parent_measures'])
            has_children = bool(data['child_measures'])

            if has_children and not has_parents:
                measure_type = "parent"
            elif has_parents and has_children:
                measure_type = "intermediate"
            elif has_parents and not has_children:
                measure_type = "final"
            else:
                measure_type = "isolated"

            return {
                "parent_measures": data['parent_measures'],
                "child_measures": data['child_measures'],
                "columns": data['columns'],
                "type": measure_type
            }

        return {
            "parent_measures": [],
            "child_measures": [],
            "columns": [],
            "type": "unknown"
        }

    def get_dependency_data(self, measure_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get dependency data for multiple measures."""
        return {
            measure_name: self.get_measure_dependencies(measure_name)
            for measure_name in measure_names
        }

    def get_full_dependency_chain(self, measure_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get a complete dependency chain including all related measures.
        This helps with visualizing the entire network of dependencies.
        """
        self.process_lineage_data()

        all_measures: Set[str] = set(measure_names)
        dependency_data: Dict[str, Dict[str, Any]] = {}

        # Breadth-first traversal to collect all related measures
        measures_to_process = list(measure_names)
        processed: Set[str] = set()

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

        # Get dependency data for all collected measures
        for measure in all_measures:
            dependency_data[measure] = self.get_measure_dependencies(measure)

        return dependency_data

    def get_comprehensive_unused_measures(self, used_measures_set: Set[str]) -> Dict[str, Any]:
        """
        Get ALL measures that would be safe to remove, including measures that
        would become unused after removing their child measures.
        """
        self.process_lineage_data()

        used_measures_set = self.expand_used_measures(used_measures_set)
        all_measures = self.get_all_measures()

        # Start with measures not used in any visuals
        unused_measures = all_measures - used_measures_set

        # Build a reverse dependency map (child -> parents)
        child_to_parents: Dict[str, Set[str]] = {}
        for measure_name, data in self.measure_data.items():
            for child in data['child_measures']:
                if child:
                    if child not in child_to_parents:
                        child_to_parents[child] = set()
                    child_to_parents[child].add(measure_name)

        # Iteratively find all measures that would become unused
        deletion_chain: List[List[str]] = []
        all_unused: Set[str] = set(unused_measures)
        measures_to_check = list(unused_measures)

        while measures_to_check:
            current_unused = set(measures_to_check)
            measures_to_check = []

            for unused_measure in current_unused:
                if unused_measure in child_to_parents:
                    for parent in child_to_parents[unused_measure]:
                        if parent not in all_unused and parent not in used_measures_set:
                            parent_data = self.measure_data.get(parent, {})
                            children = [c for c in parent_data.get('child_measures', []) if c]

                            if children and all(child in all_unused for child in children):
                                all_unused.add(parent)
                                measures_to_check.append(parent)

            if current_unused:
                deletion_chain.append(list(current_unused))

        # Build impact analysis
        impact_analysis: Dict[str, Dict[str, Any]] = {}
        for measure in all_unused:
            data = self.measure_data.get(measure, {})

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

    def _get_measure_type(self, measure_data: Dict[str, Any]) -> str:
        """Helper to determine measure type."""
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

    def analyze_deletion_impact(self, measure_names: List[str]) -> Dict[str, Any]:
        """Analyze what happens if we delete these measures."""
        self.process_lineage_data()

        chain: Dict[str, List[str]] = {
            "level1": list(measure_names),
            "level2": [],
            "level3": []
        }

        measure_names_set = set(measure_names)

        # Collect all measures that reference our level 1 measures
        level2_candidates: Set[str] = set()

        for measure, data in self.measure_data.items():
            if measure in measure_names_set:
                continue

            for parent in data['parent_measures']:
                if parent in measure_names_set:
                    level2_candidates.add(measure)
                    break

        # Filter level 2 candidates - only include ones where ALL parents are in level 1
        for candidate in level2_candidates:
            data = self.measure_data[candidate]
            if all(parent in measure_names_set for parent in data['parent_measures']):
                chain["level2"].append(candidate)

        # Similarly for level 3
        level2_set = set(chain["level2"])
        level3_candidates: Set[str] = set()

        for measure, data in self.measure_data.items():
            if measure in measure_names_set or measure in level2_set:
                continue

            for parent in data['parent_measures']:
                if parent in level2_set:
                    level3_candidates.add(measure)
                    break

        # Filter level 3 candidates
        all_previous_levels = measure_names_set | level2_set

        for candidate in level3_candidates:
            data = self.measure_data[candidate]
            if all(parent in all_previous_levels for parent in data['parent_measures']):
                chain["level3"].append(candidate)

        impact_score = len(chain["level1"]) + len(chain["level2"]) * 2 + len(chain["level3"]) * 3

        return {
            "chain": chain,
            "impact_score": impact_score,
            "total_measures": len(chain["level1"]) + len(chain["level2"]) + len(chain["level3"])
        }
