"""Main routes blueprint - workbench dashboard and workflow pages."""

import datetime
import os
from typing import Any, Dict, List

from flask import Blueprint, current_app, render_template

from data_processor import DataProcessor
from lineage_view import LineageView
from model_processor import ModelProcessor
from utils.processors import (
    get_data_processor,
    get_lineage_view_processor,
    get_model_processor,
    get_report_metrics,
)

main_bp = Blueprint('main', __name__)


def _severity_rank(severity: str) -> int:
    """Return a sortable rank for issue severities."""
    ranks = {
        'critical': 4,
        'high': 3,
        'medium': 2,
        'low': 1
    }
    return ranks.get((severity or '').lower(), 0)


def _build_issue_catalog(metrics: Dict[str, Any], model_processor: ModelProcessor) -> List[Dict[str, Any]]:
    """Create a prioritized issue list for dashboard triage."""
    issues: List[Dict[str, Any]] = []

    measure_count = max(int(metrics.get('measure_count') or 0), 1)
    visual_count = int(metrics.get('visual_count') or 0)
    page_count = max(int(metrics.get('page_count') or 0), 1)
    visuals_per_page = visual_count / page_count

    model_summary = metrics.get('model_summary') or {}
    report_summary = metrics.get('report_summary') or {}
    unused_count = int(metrics.get('unused_count') or 0)
    cascade_unused = int((metrics.get('unused_breakdown') or {}).get('cascade') or 0)

    measures = model_processor.get_measures() or []
    tables = model_processor.get_tables() or []

    measures_without_description = [
        measure for measure in measures
        if not (measure.get('description') or '').strip()
    ]
    measures_without_format = [
        measure for measure in measures
        if not (measure.get('formatString') or '').strip()
    ]
    columns_without_category = [
        column
        for table in tables
        for column in table.get('columns', [])
        if not (column.get('dataCategory') or '').strip()
    ]

    if unused_count > 0:
        ratio = unused_count / measure_count
        severity = 'critical' if ratio >= 0.30 else 'high' if ratio >= 0.16 else 'medium'
        penalty = min(28, round(unused_count * 0.85))
        issues.append({
            'id': 'unused-measures',
            'title': 'Unused measures are inflating model complexity',
            'severity': severity,
            'category': 'Optimization',
            'count': unused_count,
            'impact': f'{ratio * 100:.1f}% of measures are not used by visuals.',
            'effort': 'low',
            'penalty': penalty,
            'why': (
                f'{unused_count} measures are removable now'
                + (f' with {cascade_unused} additional cascade opportunities.' if cascade_unused else '.')
            ),
            'recommendation': 'Start with leaf measures and remove in controlled batches using dependency checks.',
            'link': '/unused-measures'
        })

    if measures_without_description:
        missing_count = len(measures_without_description)
        severity = 'high' if missing_count >= 30 else 'medium'
        issues.append({
            'id': 'measure-docs',
            'title': 'Measure documentation coverage is low',
            'severity': severity,
            'category': 'Governance',
            'count': missing_count,
            'impact': f'{missing_count} measures are missing descriptions.',
            'effort': 'medium',
            'penalty': min(18, round(missing_count * 0.45)),
            'why': 'Lack of descriptions slows onboarding and increases semantic drift.',
            'recommendation': 'Document business logic for high-use measures first, then enforce via review checklist.',
            'link': '/model-insights'
        })

    if measures_without_format:
        missing_count = len(measures_without_format)
        severity = 'high' if missing_count >= 35 else 'medium'
        issues.append({
            'id': 'measure-formatting',
            'title': 'Format strings are missing for key measures',
            'severity': severity,
            'category': 'Consistency',
            'count': missing_count,
            'impact': f'{missing_count} measures can render inconsistently across visuals.',
            'effort': 'low',
            'penalty': min(14, round(missing_count * 0.30)),
            'why': 'Unformatted values reduce trust and make reports harder to scan.',
            'recommendation': 'Apply numeric/currency/percentage formats in bulk from model metadata.',
            'link': '/model-insights'
        })

    if columns_without_category:
        missing_count = len(columns_without_category)
        severity = 'medium' if missing_count >= 20 else 'low'
        issues.append({
            'id': 'data-category',
            'title': 'Columns are missing data categories',
            'severity': severity,
            'category': 'Model Quality',
            'count': missing_count,
            'impact': f'{missing_count} columns miss categorization metadata.',
            'effort': 'medium',
            'penalty': min(10, round(missing_count * 0.18)),
            'why': 'Missing categories can impact geospatial and semantic behaviors.',
            'recommendation': 'Prioritize geographic, URL, and image-like columns for categorization.',
            'link': '/model-insights'
        })

    if visuals_per_page >= 18:
        severity = 'high' if visuals_per_page >= 26 else 'medium'
        issues.append({
            'id': 'visual-density',
            'title': 'Report pages are visually overloaded',
            'severity': severity,
            'category': 'UX Risk',
            'count': round(visuals_per_page, 1),
            'impact': f'Average page density is {visuals_per_page:.1f} visuals per page.',
            'effort': 'high',
            'penalty': min(15, round((visuals_per_page - 12) * 0.9)),
            'why': 'High density raises cognitive load and can hide KPI priorities.',
            'recommendation': 'Refactor crowded pages into focused views with explicit narrative flow.',
            'link': '/report-insights'
        })

    bookmark_count = int(report_summary.get('bookmark_count') or 0)
    navigation_count = int(report_summary.get('navigation_count') or 0)
    if bookmark_count >= 15 or navigation_count >= 20:
        severity = 'medium' if bookmark_count >= 24 or navigation_count >= 30 else 'low'
        issues.append({
            'id': 'navigation-complexity',
            'title': 'Navigation and bookmark complexity is high',
            'severity': severity,
            'category': 'Maintainability',
            'count': bookmark_count + navigation_count,
            'impact': f'{bookmark_count} bookmarks and {navigation_count} navigation visuals detected.',
            'effort': 'medium',
            'penalty': min(9, round((bookmark_count + navigation_count) * 0.13)),
            'why': 'Complex navigation states are harder to test and easier to break.',
            'recommendation': 'Consolidate redundant bookmark states and standardize navigation patterns.',
            'link': '/report-insights'
        })

    hidden_total = int(model_summary.get('hidden_table_count') or 0)
    hidden_total += int(model_summary.get('hidden_column_count') or 0)
    hidden_total += int(model_summary.get('hidden_measure_count') or 0)
    if hidden_total >= 180:
        issues.append({
            'id': 'hidden-assets',
            'title': 'Hidden model assets should be reviewed',
            'severity': 'low',
            'category': 'Governance',
            'count': hidden_total,
            'impact': f'{hidden_total} hidden objects were found.',
            'effort': 'low',
            'penalty': min(6, round(hidden_total * 0.02)),
            'why': 'Hidden assets accumulate technical debt when no ownership policy exists.',
            'recommendation': 'Label intentional hidden assets and remove deprecated artifacts.',
            'link': '/model-insights'
        })

    issues.sort(
        key=lambda issue: (_severity_rank(issue['severity']), issue['penalty'], float(issue['count'])),
        reverse=True
    )

    for index, issue in enumerate(issues, start=1):
        issue['rank'] = index

    return issues


def _build_health_summary(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate portfolio-friendly health summary stats."""
    severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    penalty_total = 0

    for issue in issues:
        severity = (issue.get('severity') or '').lower()
        if severity in severity_counts:
            severity_counts[severity] += 1
        penalty_total += int(issue.get('penalty') or 0)

    bounded_penalty = min(88, penalty_total)
    score = max(12, 100 - bounded_penalty)

    if score >= 85:
        label = 'Strong'
        tone = 'good'
    elif score >= 70:
        label = 'Watchlist'
        tone = 'watch'
    elif score >= 55:
        label = 'At Risk'
        tone = 'risk'
    else:
        label = 'Critical'
        tone = 'critical'

    return {
        'score': score,
        'label': label,
        'tone': tone,
        'penalty_total': bounded_penalty,
        'issue_count': len(issues),
        'critical_count': severity_counts['critical'],
        'high_count': severity_counts['high'],
        'medium_count': severity_counts['medium'],
        'low_count': severity_counts['low']
    }


def _build_workbench_context() -> Dict[str, Any]:
    """Assemble shared context for workbench pages."""
    metrics = get_report_metrics()
    model_processor = get_model_processor()
    issues = _build_issue_catalog(metrics, model_processor)
    health = _build_health_summary(issues)

    quick_wins = [
        issue for issue in issues
        if issue.get('effort') in {'low', 'medium'}
    ][:4]

    focus_areas = issues[:3]

    return {
        'metrics': metrics,
        'issues': issues,
        'health': health,
        'quick_wins': quick_wins,
        'focus_areas': focus_areas
    }


@main_bp.route('/')
def index() -> str:
    """Render the workbench health dashboard."""
    context = _build_workbench_context()
    context['time_loaded'] = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")
    return render_template('index.html', **context)


@main_bp.route('/upload-validate')
def upload_validate() -> str:
    """Render file readiness and validation checks."""
    context = _build_workbench_context()

    checks: List[Dict[str, Any]] = []
    file_specs = [
        ('Report Definition', current_app.config['REPORT_JSON_PATH'], 'report.json', 'Required'),
        ('Measure Dependencies', current_app.config['MEASURE_DEPENDENCIES_TSV_PATH'], 'MeasureDependencies.tsv', 'Required'),
        ('Semantic Model', current_app.config['MODEL_JSON_PATH'], 'model.json', 'Required')
    ]

    for label, path, expected_name, requirement in file_specs:
        exists = os.path.exists(path)
        stats = os.stat(path) if exists else None
        checks.append({
            'label': label,
            'path': path,
            'expected_name': expected_name,
            'requirement': requirement,
            'exists': exists,
            'size_kb': round((stats.st_size / 1024), 1) if stats else 0,
            'modified': datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M') if stats else '-'
        })

    validation_checks: List[Dict[str, Any]] = []
    successful_checks = 0

    report_path = current_app.config['REPORT_JSON_PATH']
    if os.path.exists(report_path):
        try:
            report_processor = DataProcessor(report_path)
            report_processor.process_json()
            successful_checks += 1
            validation_checks.append({
                'name': 'Report JSON parsing',
                'status': 'pass',
                'detail': f'{len(report_processor.visuals_data)} visual records parsed.'
            })
        except Exception as exc:  # pragma: no cover - defensive UI path
            validation_checks.append({
                'name': 'Report JSON parsing',
                'status': 'fail',
                'detail': f'Failed to parse report.json ({exc}).'
            })
    else:
        validation_checks.append({
            'name': 'Report JSON parsing',
            'status': 'fail',
            'detail': 'Missing report.json file.'
        })

    lineage_path = current_app.config['MEASURE_DEPENDENCIES_TSV_PATH']
    if os.path.exists(lineage_path):
        try:
            lineage_processor = LineageView(lineage_path)
            lineage_processor.process_lineage_data()
            successful_checks += 1
            validation_checks.append({
                'name': 'Lineage TSV parsing',
                'status': 'pass',
                'detail': f'{len(lineage_processor.get_all_measures())} measures discovered.'
            })
        except Exception as exc:  # pragma: no cover - defensive UI path
            validation_checks.append({
                'name': 'Lineage TSV parsing',
                'status': 'fail',
                'detail': f'Failed to parse MeasureDependencies.tsv ({exc}).'
            })
    else:
        validation_checks.append({
            'name': 'Lineage TSV parsing',
            'status': 'fail',
            'detail': 'Missing MeasureDependencies.tsv file.'
        })

    model_path = current_app.config['MODEL_JSON_PATH']
    if os.path.exists(model_path):
        try:
            model_processor = ModelProcessor(model_path)
            model_processor.load()
            successful_checks += 1
            validation_checks.append({
                'name': 'Model JSON parsing',
                'status': 'pass',
                'detail': f'{len(model_processor.get_tables())} tables loaded successfully.'
            })
        except Exception as exc:  # pragma: no cover - defensive UI path
            validation_checks.append({
                'name': 'Model JSON parsing',
                'status': 'fail',
                'detail': f'Failed to parse model.json ({exc}).'
            })
    else:
        validation_checks.append({
            'name': 'Model JSON parsing',
            'status': 'fail',
            'detail': 'Missing model.json file.'
        })

    required_ready = sum(1 for file_check in checks if file_check['exists'])
    readiness_score = round(((required_ready + successful_checks) / 6) * 100)

    context.update({
        'file_checks': checks,
        'validation_checks': validation_checks,
        'readiness_score': readiness_score
    })
    return render_template('upload_validate.html', **context)


@main_bp.route('/explore')
def explore() -> str:
    """Render the exploration hub with fast entry points."""
    context = _build_workbench_context()
    metrics = context['metrics']

    explore_sections = [
        {
            'title': 'Report Surface',
            'description': 'Understand what users see and interact with.',
            'tools': [
                {
                    'name': 'Visual Fields Explorer',
                    'description': 'Audit field usage across all visuals and pages.',
                    'href': '/table-view',
                    'kpi': f"{metrics.get('visual_count', 0)} visuals"
                },
                {
                    'name': 'Report Insights',
                    'description': 'Inspect bookmarks, layout patterns, and formatting debt.',
                    'href': '/report-insights',
                    'kpi': f"{(metrics.get('report_summary') or {}).get('bookmark_count', 0)} bookmarks"
                },
            ]
        },
        {
            'title': 'Semantic Model',
            'description': 'Validate structure, metadata quality, and dependencies.',
            'tools': [
                {
                    'name': 'Model Insights',
                    'description': 'Review tables, columns, relationships, and RLS roles.',
                    'href': '/model-insights',
                    'kpi': f"{(metrics.get('model_summary') or {}).get('table_count', 0)} tables"
                },
                {
                    'name': 'Data Lineage',
                    'description': 'Trace measure dependencies and upstream calculations.',
                    'href': '/lineage-view',
                    'kpi': f"{metrics.get('measure_count', 0)} measures"
                },
            ]
        },
        {
            'title': 'Code & Sources',
            'description': 'Inspect logic implementation and source query patterns.',
            'tools': [
                {
                    'name': 'DAX Analyzer',
                    'description': 'Browse formulas and identify duplication risk.',
                    'href': '/dax-expressions',
                    'kpi': f"{metrics.get('measure_count', 0)} DAX measures"
                },
                {
                    'name': 'Source Explorer',
                    'description': 'Review M queries, source types, and dependencies.',
                    'href': '/source-explorer',
                    'kpi': 'M query inventory'
                },
            ]
        }
    ]

    context['explore_sections'] = explore_sections
    return render_template('explore.html', **context)


@main_bp.route('/impact-simulator')
def impact_simulator() -> str:
    """Render simulated impact from measure cleanup actions."""
    context = _build_workbench_context()
    metrics = context['metrics']
    data_processor = get_data_processor()
    lineage_processor = get_lineage_view_processor()

    known_measures = set(lineage_processor.measure_data) or lineage_processor.get_all_measures()
    used_measures = data_processor.get_used_measures(known_measures)
    used_measures = lineage_processor.expand_used_measures(used_measures)
    unused_analysis = lineage_processor.get_comprehensive_unused_measures(used_measures)

    deletion_levels: List[Dict[str, Any]] = []
    for level_index, measures_in_level in enumerate(unused_analysis.get('deletion_chain', []), start=1):
        if not measures_in_level:
            continue
        deletion_levels.append({
            'level': level_index,
            'count': len(measures_in_level),
            'sample': sorted(measures_in_level)[:6]
        })

    scenarios: List[Dict[str, Any]] = []
    for measure_name in sorted(unused_analysis.get('all_unused', []))[:4]:
        impact = lineage_processor.analyze_deletion_impact([measure_name])
        chain = impact.get('chain', {})
        scenarios.append({
            'measure': measure_name,
            'impact_score': impact.get('impact_score', 0),
            'level1': len(chain.get('level1', [])),
            'level2': len(chain.get('level2', [])),
            'level3': len(chain.get('level3', [])),
            'total': impact.get('total_measures', 0)
        })

    context.update({
        'unused_analysis': unused_analysis,
        'deletion_levels': deletion_levels,
        'scenarios': scenarios,
        'impact_summary': {
            'unused_total': unused_analysis.get('total_unused', 0),
            'immediate_unused': unused_analysis.get('immediate_unused', 0),
            'cascade_unused': unused_analysis.get('cascade_unused', 0),
            'used_measures': len(used_measures),
            'all_measures': metrics.get('measure_count', 0)
        }
    })
    return render_template('impact_simulator.html', **context)


@main_bp.route('/exports')
def exports_center() -> str:
    """Render export options and reporting handoff formats."""
    context = _build_workbench_context()

    export_items = [
        {
            'name': 'Model JSON API',
            'description': 'Export raw semantic model metadata for downstream automation.',
            'format': 'JSON',
            'path': '/api/model-json',
            'action_label': 'Open Endpoint'
        },
        {
            'name': 'Field Usage Inventory',
            'description': 'Use Visual Fields Explorer export to share field lineage with analysts.',
            'format': 'CSV',
            'path': '/table-view',
            'action_label': 'Go to Visual Fields'
        },
        {
            'name': 'DAX Catalog',
            'description': 'Export measure formulas and similarity analysis for code review.',
            'format': 'CSV',
            'path': '/dax-expressions',
            'action_label': 'Go to DAX Analyzer'
        },
        {
            'name': 'Source Query Catalog',
            'description': 'Export M query inventory and source dependency mappings.',
            'format': 'CSV',
            'path': '/source-explorer',
            'action_label': 'Go to Source Explorer'
        },
    ]

    context['export_items'] = export_items
    return render_template('exports.html', **context)
