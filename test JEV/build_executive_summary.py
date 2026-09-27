"""Create an isolated executive-summary report from the existing PBIP."""
import copy
import json
import shutil
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output' / 'executive-summary'
PAGE = 'executivesummary2026'
SCHEMA = 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding='utf-8')


def literal(value):
    return {'expr': {'Literal': {'Value': value}}}


def projection(table, name, kind='Measure'):
    return {'field': {kind: {'Expression': {'SourceRef': {'Entity': table}}, 'Property': name}},
            'queryRef': f'{table}.{name}', 'nativeQueryRef': name}


def container(kind, title, x, y, w, h, roles=None):
    obj = {'$schema': SCHEMA + 'visualContainer/2.12.0/schema.json',
           'name': uuid.uuid4().hex[:20],
           'position': {'x': x, 'y': y, 'width': w, 'height': h, 'z': y * 10 + x, 'tabOrder': y * 10 + x},
           'visual': {'visualType': kind, 'drillFilterOtherVisuals': True,
                      'visualContainerObjects': {
                          'title': [{'properties': {'show': literal('true'), 'text': literal("'" + title + "'"),
                                                   'fontSize': literal('12D')}}],
                          'background': [{'properties': {'show': literal('true'), 'color': {'solid': {'color': literal("'#FFFFFF'")}}, 'transparency': literal('0D')}}]}}}
    if roles:
        obj['visual']['query'] = {'queryState': {k: {'projections': v} for k, v in roles.items()}}
    return obj


def main():
    if OUT.exists():
        raise SystemExit(f'Output already exists: {OUT}; refusing to overwrite')
    OUT.mkdir(parents=True)
    shutil.copy2(ROOT / 'JEV.pbip', OUT / 'JEV.pbip')
    for folder in ('JEV.Report', 'JEV.SemanticModel'):
        shutil.copytree(ROOT / folder, OUT / folder, ignore=shutil.ignore_patterns('.pbi', '.platform'))
    pages = OUT / 'JEV.Report/definition/pages'
    page = {'$schema': SCHEMA + 'page/2.1.0/schema.json', 'name': PAGE,
            'displayName': 'Executive Summary', 'displayOption': 'FitToPage', 'width': 1280, 'height': 720,
            'objects': {'background': [{'properties': {'color': {'solid': {'color': literal("'#F3F5F7'")}}, 'transparency': literal('0D')}}]}}
    write(pages / PAGE / 'page.json', page)
    visuals = []
    header = container('textbox', '', 24, 16, 890, 62)
    header['visual']['visualContainerObjects']['title'][0]['properties']['show'] = literal('false')
    header['visual']['objects'] = {'general': [{'properties': {'paragraphs': [
        {'textRuns': [{'value': 'Executive Summary', 'textStyle': {'fontFamily': 'Segoe UI', 'fontSize': '24pt', 'fontWeight': 'bold'}}]},
        {'textRuns': [{'value': 'Income, spending and payroll | Selected period | EUR', 'textStyle': {'fontSize': '10pt'}}]}
    ]}}]}
    visuals.append(header)
    slicer = read(ROOT / 'JEV.Report/definition/pages/ee59d6a27e5809480ad0/visuals/f9927d77d709b037384e/visual.json')
    slicer['name'] = uuid.uuid4().hex[:20]
    slicer['position'] = {'x': 960, 'y': 16, 'width': 296, 'height': 62, 'z': 1, 'tabOrder': 1}
    slicer['visual'].pop('expansionStates', None)
    slicer['visual']['objects'].pop('general', None)
    visuals.append(slicer)
    cards = [('Income', 'Expenses_New', 'Total Income Clean'),
             ('Expenses', 'Expenses_New', 'Total Expenses Clean'),
             ('Gross salary', 'Payslips', 'Total Gross Salary'),
             ('Net / gross salary', 'Payslips', 'Net Salary to Gross Salary Ratio (%)')]
    for index, (title, table, measure) in enumerate(cards):
        card = container('card', title, 24 + index * 312, 96, 296, 120,
                         {'Values': [projection(table, measure)]})
        card['visual']['objects'] = {'labels': [{'properties': {'fontSize': literal('28D')}}],
                                     'categoryLabels': [{'properties': {'show': literal('false')}}]}
        visuals.append(card)
    trend = container('lineChart', 'Income and expenses over time', 24, 236, 736, 408,
                      {'Category': [projection('DT_Calendar', 'Date', 'Column')],
                       'Y': [projection('Expenses_New', 'Total Income Clean'), projection('Expenses_New', 'Total Expenses Clean')]})
    trend['visual']['query']['sortDefinition'] = {'sort': [{'field': projection('DT_Calendar', 'Date', 'Column')['field'], 'direction': 'Ascending'}]}
    visuals.append(trend)
    top = read(ROOT / 'JEV.Report/definition/pages/c65861ef956aa27ca503/visuals/35c2d9b5d61fea378d85/visual.json')
    top['name'] = uuid.uuid4().hex[:20]
    top['position'] = {'x': 784, 'y': 236, 'width': 472, 'height': 408, 'z': 5, 'tabOrder': 5}
    top['visual']['visualType'] = 'barChart'
    top['visual']['visualContainerObjects'] = copy.deepcopy(trend['visual']['visualContainerObjects'])
    top['visual']['visualContainerObjects']['title'][0]['properties']['text'] = literal("'Top 10 expense descriptions'")
    top['filterConfig']['filters'] = [f for f in top['filterConfig']['filters'] if f['type'] == 'TopN']
    visuals.append(top)
    footer = container('textbox', '', 24, 662, 1232, 40)
    footer['visual']['visualContainerObjects']['title'][0]['properties']['show'] = literal('false')
    footer['visual']['objects'] = {'general': [{'properties': {'paragraphs': [{'textRuns': [{'value': 'Income = credit transactions. Expenses = debit transactions (absolute amounts). Payroll figures are separate and are not added to income.', 'textStyle': {'fontSize': '10pt'}}]}]}}]}
    visuals.append(footer)
    for visual in visuals:
        write(pages / PAGE / 'visuals' / visual['name'] / 'visual.json', visual)
    metadata = read(pages / 'pages.json')
    metadata['pageOrder'].insert(0, PAGE)
    metadata['activePageName'] = PAGE
    write(pages / 'pages.json', metadata)
    print(f'Created {OUT / "JEV.pbip"} with {len(visuals)} summary visuals')


if __name__ == '__main__':
    main()
