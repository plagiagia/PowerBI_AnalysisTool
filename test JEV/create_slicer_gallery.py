"""Create twenty interactive date and field slicer styles on the Slicers page."""
import copy
import uuid
from pathlib import Path

from build_executive_summary import read, write, literal as L, projection
from polish_report import color, props, text

ROOT = Path(__file__).resolve().parent / 'output/finance-app/JEV.Report/definition/pages'

# name, table, field, mode, single-select, background, ink, accent, item-bg, direction
DESIGNS = [
    ('01 / Date range · Cloud', 'DT_Calendar', 'Date', 'Between', False, '#FFFFFF', '#31445B', '#087F8C', '#F4F8FA', 'vertical'),
    ('02 / Date range · Outline', 'DT_Calendar', 'Date', 'Between', False, '#FFFFFF', '#263B52', '#3978B8', '#FFFFFF', 'vertical'),
    ('03 / Date range · Midnight', 'DT_Calendar', 'Date', 'Between', False, '#17232E', '#F0F6FA', '#49C5C1', '#233544', 'vertical'),
    ('04 / Date before', 'DT_Calendar', 'Date', 'Before', True, '#F7FAFE', '#263F5B', '#3978B8', '#FFFFFF', 'vertical'),
    ('05 / Date after', 'DT_Calendar', 'Date', 'After', True, '#FFFEFB', '#55463D', '#B66A45', '#FFFFFF', 'vertical'),
    ('06 / Relative date', 'DT_Calendar', 'Date', 'Relative', True, '#F5FBF8', '#234C41', '#25866B', '#FFFFFF', 'vertical'),
    ('07 / Calendar dropdown', 'DT_Calendar', 'Date', 'Dropdown', True, '#FFFFFF', '#263B52', '#315E91', '#F5F8FC', 'vertical'),
    ('08 / Date list', 'DT_Calendar', 'Date', 'Basic', False, '#F7FAFE', '#263F5B', '#3978B8', '#FFFFFF', 'vertical'),
    ('09 / Year · Dropdown', 'DT_Calendar', 'Year', 'Dropdown', True, '#FFFFFF', '#263B52', '#087F8C', '#FFFFFF', 'vertical'),
    ('10 / Year · Buttons', 'DT_Calendar', 'Year', 'Basic', True, '#F1F5FC', '#193B65', '#3468A0', '#FFFFFF', 'horizontal'),
    ('11 / Quarter · Multi select', 'DT_Calendar', 'vizQuarter', 'Basic', False, '#F5FBF8', '#234C41', '#25866B', '#FFFFFF', 'horizontal'),
    ('12 / Month · Dropdown', 'DT_Calendar', 'Month Name', 'Dropdown', True, '#FFFEFB', '#55463D', '#B66A45', '#FFFFFF', 'vertical'),
    ('13 / Month · List', 'DT_Calendar', 'Month Name', 'Basic', False, '#FFFFFF', '#31445B', '#087F8C', '#F4F8FA', 'vertical'),
    ('14 / Expense category', 'Expenses_New', 'Category', 'Basic', False, '#FFFFFF', '#263B52', '#3978B8', '#F5F8FC', 'vertical'),
    ('15 / Expense type · Single', 'Expenses_New', 'Type', 'Basic', True, '#F7FAFE', '#263F5B', '#3978B8', '#FFFFFF', 'vertical'),
    ('16 / Description · Search', 'Expenses_New', 'Description', 'Dropdown', True, '#FFFFFF', '#31445B', '#087F8C', '#F4F8FA', 'vertical'),
    ('17 / Description · Multi', 'Expenses_New', 'Description', 'Basic', False, '#F5F8FC', '#203B5A', '#315E91', '#FFFFFF', 'vertical'),
    ('18 / Payroll category', 'Payslips', 'Lohnart', 'Dropdown', True, '#FFFEFB', '#55463D', '#B66A45', '#FFFFFF', 'vertical'),
    ('19 / Payroll category · List', 'Payslips', 'Lohnart', 'Basic', False, '#FFFFFF', '#263B52', '#087F8C', '#F4F8FA', 'vertical'),
    ('20 / Expense category · Midnight', 'Expenses_New', 'Category', 'Basic', False, '#101B2B', '#F5F2E9', '#E9B96E', '#233044', 'vertical'),
]


def main():
    pages = [p for p in ROOT.glob('*/page.json') if read(p).get('displayName', '').lower() == 'slicers']
    if len(pages) != 1:
        raise SystemExit('Expected exactly one Slicers page')
    page_path = pages[0]
    folder = page_path.parent
    sources = list((folder / 'visuals').glob('*/visual.json'))
    if len(sources) != 1:
        raise SystemExit('Expected one source slicer on the Slicers page; refusing to replace an existing gallery')
    source_path = sources[0]
    source_bytes = source_path.read_bytes()
    page_bytes = page_path.read_bytes()
    source = read(source_path)
    if source.get('visual', {}).get('visualType') != 'slicer':
        raise SystemExit('Slicers page source is not a native slicer')
    date_candidates = []
    for path in ROOT.glob('*/visuals/*/visual.json'):
        v = read(path)
        projections = v.get('visual', {}).get('query', {}).get('queryState', {}).get('Values', {}).get('projections', [])
        if v.get('visual', {}).get('visualType') == 'slicer' and any(
                p.get('field', {}).get('Column', {}).get('Expression', {}).get('SourceRef', {}).get('Entity') == 'DT_Calendar'
                and p.get('field', {}).get('Column', {}).get('Property') == 'Date' for p in projections):
            date_candidates.append(v)
    if not date_candidates:
        raise SystemExit('Could not find an existing date slicer template')
    date_template = next((v for v in date_candidates if v.get('visual', {}).get('objects', {}).get('data', [{}])[0].get('properties', {}).get('mode', {}).get('expr', {}).get('Literal', {}).get('Value') == "'Between'"), date_candidates[0])

    labels = [
        text('SLICER STUDIO  /  20 interactive selection styles', 40, 20, 1520, 46, 27),
        text('Choose a date, time period, expense field or payroll field. Single and multiple selection examples are labeled.', 40, 72, 1520, 32, 12, '#64748B'),
    ]
    positions = [(40 + (i % 4) * 390, 166 + (i // 4) * 394) for i in range(len(DESIGNS))]
    slicers = []
    for i, ((title, table, field, mode, single, bg, ink, accent, item_bg, orientation), (x, y)) in enumerate(zip(DESIGNS, positions)):
        template = date_template if field == 'Date' else source
        v = copy.deepcopy(template)
        if i:
            v['name'] = uuid.uuid4().hex[:20]
        v['position'] = {'x': x, 'y': y, 'width': 350, 'height': 276, 'z': i + 1, 'tabOrder': i + 1}
        proj = projection(table, field, 'Column')
        proj.update(queryRef=f'{table}.{field}', nativeQueryRef=field, active=True)
        vis = v['visual']
        vis['query']['queryState'] = {'Values': {'projections': [proj]}}
        if field in ('Date', 'Year', 'Month Name', 'vizQuarter'):
            vis['query']['sortDefinition'] = {'isDefaultSort': True}
        else:
            vis['query'].pop('sortDefinition', None)
        # Prevent an inherited date range filter from clipping the user's date selector.
        if field == 'Date':
            vis.setdefault('objects', {}).setdefault('general', [{}])[0].setdefault('properties', {}).pop('filter', None)
        objects = vis.setdefault('objects', {})
        objects['data'] = props({'mode': L(repr(mode))})
        objects['general'] = props({'selfFilterEnabled': L('true'),
                                     'orientation': L('1D' if orientation == 'horizontal' else '0D'),
                                     'outlineColor': color(accent)})
        objects['header'] = props({'show': L('true'), 'fontColor': color(ink), 'textSize': L('10D')})
        objects['items'] = props({'fontColor': color(ink), 'background': color(item_bg), 'textSize': L('11D'),
                                  'selectedColor': color(accent)})
        objects['selection'] = props({'selectAllCheckboxEnabled': L('true' if not single else 'false'),
                                      'strictSingleSelect': L('true' if single else 'false')})
        objects['slider'] = props({'show': L('true' if field == 'Date' and mode in ('Between', 'Before', 'After') else 'false')})
        vc = vis.setdefault('visualContainerObjects', {})
        vc['title'] = props({'show': L('true'), 'text': L(repr(f'{table}.{field}')),
                             'fontFamily': L("'Segoe UI Semibold'"), 'fontSize': L('12D'),
                             'fontColor': color(ink), 'alignment': L("'left'")})
        vc['background'] = props({'show': L('true'), 'color': color(bg), 'transparency': L('0D')})
        vc['border'] = props({'show': L('true'), 'color': color(accent if i % 4 else '#DFE7EE'),
                              'radius': L('18D' if i in (0, 1, 9, 10, 19) else '8D'), 'width': L('1D')})
        vc['dropShadow'] = props({'show': L('true' if i in (0, 2, 9, 19) else 'false'),
                                  'color': color(accent), 'transparency': L('83D'), 'position': L("'Outer'"),
                                  'shadowBlur': L('18D'), 'shadowDistance': L('4D'), 'angle': L('90D')})
        labels.append(text(title, x, y - 30, 350, 24, 11, ink))
        labels.append(v)
        labels.append(text(('Single select' if single else 'Multi select') + ' · ' + mode,
                           x, y + 282, 350, 22, 9, '#687A8C'))
        slicers.append(v)

    page = read(page_path)
    page.update(width=1600, height=2160, displayOption='FitToWidth')
    page['objects'] = {'background': props({'color': color('#EDF1F5'), 'transparency': L('0D')})}
    if source_path.read_bytes() != source_bytes or page_path.read_bytes() != page_bytes:
        raise SystemExit('Page changed during generation; save and retry')
    for v in labels:
        write(folder / 'visuals' / v['name'] / 'visual.json', v)
    write(page_path, page)
    assert len(slicers) == 20
    assert all(v['visual']['visualType'] == 'slicer' for v in slicers)
    assert all(len(v['visual']['query']['queryState']['Values']['projections']) == 1 for v in slicers)
    print('Created 20 interactive native slicers across date, calendar, expense and payroll fields.')


if __name__ == '__main__':
    main()
