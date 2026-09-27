"""Create eight styled copies of the original Bar Chart visual in place."""
import copy
import uuid
from pathlib import Path

from build_executive_summary import read, write, literal as L
from polish_report import color, props, text

ROOT = Path(__file__).resolve().parent / 'output/finance-app/JEV.Report/definition/pages'

DESIGNS = [
    ('01 / Nordic clarity', 'Crisp white, cool blue columns and restrained gridlines.', 'columnChart', '#FFFFFF', '#2468A2', '#263B52', '#DCE5EE', False, False),
    ('02 / Floating cloud', 'Soft surface, airy teal columns and a gentle lift.', 'columnChart', '#FFFFFF', '#087F8C', '#31445B', '#E3EBF2', True, False),
    ('03 / Executive navy', 'Confident blue palette with clear value labels.', 'columnChart', '#F5F8FC', '#315E91', '#203B5A', '#DAE4EF', False, True),
    ('04 / Editorial', 'Warm paper tones and muted terracotta for a quieter report.', 'columnChart', '#FFFEFB', '#B66A45', '#55463D', '#E9E0D7', False, False),
    ('05 / Mint signal', 'Light mint canvas with an understated emerald accent.', 'columnChart', '#F5FBF8', '#25866B', '#234C41', '#DDEBE5', False, False),
    ('06 / Graphite', 'Dark graphite panel with high contrast cyan data.', 'columnChart', '#17232E', '#49C5C1', '#F0F6FA', '#344554', False, False),
    ('07 / Azure horizontal', 'Horizontal bars make category labels easy to scan.', 'barChart', '#F7FAFE', '#3978B8', '#263F5B', '#DFE8F1', False, False),
    ('08 / Midnight', 'Deep navy surface with a warm gold highlight.', 'columnChart', '#101B2B', '#E9B96E', '#F5F2E9', '#334256', True, False),
]


def main():
    matches = [p for p in ROOT.glob('*/page.json') if read(p).get('displayName', '').lower() == 'bar chart']
    if len(matches) != 1:
        raise SystemExit('Expected exactly one Bar Chart page')
    page_path = matches[0]
    folder = page_path.parent
    source_paths = list((folder / 'visuals').glob('*/visual.json'))
    if len(source_paths) != 1:
        raise SystemExit('Expected a single source visual on Bar Chart; refusing to overwrite an existing gallery')
    source_path = source_paths[0]
    source_bytes = source_path.read_bytes()
    page_bytes = page_path.read_bytes()
    source = read(source_path)
    if source.get('visual', {}).get('visualType') != 'columnChart':
        raise SystemExit('Source visual is not a column chart')

    visuals = [
        text('BAR CHART STUDIO  /  Eight polished directions', 40, 22, 1520, 48, 27),
        text('Same payroll amount, calendar hierarchy and source date filter in every view.', 40, 76, 1520, 32, 12, '#64748B'),
    ]
    positions = [(40 + (i % 2) * 780, 176 + (i // 2) * 448) for i in range(8)]
    chart_copies = []
    for i, ((title, caption, chart_type, bg, bar, ink, grid, shadow, labels), (x, y)) in enumerate(zip(DESIGNS, positions)):
        v = copy.deepcopy(source)
        if i:
            v['name'] = uuid.uuid4().hex[:20]
        v['position'] = {'x': x, 'y': y, 'width': 740, 'height': 354, 'z': i + 1, 'tabOrder': i + 1}
        vis = v['visual']
        vis['visualType'] = chart_type
        obj = vis.setdefault('objects', {})
        obj['dataPoint'] = props({'defaultColor': color(bar)})
        axis_color = '#AFC1D1' if bg in ('#17232E', '#101B2B') else '#64748B'
        obj['categoryAxis'] = props({'show': L('true'), 'showAxisTitle': L('false'), 'fontSize': L('10D'),
                                     'fontFamily': L("'Segoe UI'"), 'labelColor': color(axis_color),
                                     'gridlineShow': L('false')})
        obj['valueAxis'] = props({'show': L('true'), 'showAxisTitle': L('false'), 'fontSize': L('10D'),
                                  'fontFamily': L("'Segoe UI'"), 'labelColor': color(axis_color),
                                  'gridlineShow': L('true'), 'gridlineColor': color(grid), 'start': L('0D')})
        obj['legend'] = props({'show': L('false')})
        obj['labels'] = props({'show': L('true' if labels else 'false'), 'color': color(ink), 'fontSize': L('9D'),
                               'fontFamily': L("'Segoe UI'")})
        vc = vis.setdefault('visualContainerObjects', {})
        vc['title'] = props({'show': L('true'), 'text': L("'Total Rentenversicherung'"),
                             'fontFamily': L("'Segoe UI Semibold'" if i in (2, 5, 7) else "'Segoe UI'"),
                             'fontSize': L('13D'), 'fontColor': color(ink), 'alignment': L("'left'")})
        vc['background'] = props({'show': L('true'), 'color': color(bg), 'transparency': L('0D')})
        vc['border'] = props({'show': L('true'), 'color': color(grid), 'radius': L('18D' if i == 1 else '8D'), 'width': L('1D')})
        vc['dropShadow'] = props({'show': L('true' if shadow else 'false'), 'color': color('#60768C'),
                                  'transparency': L('82D'), 'position': L("'Outer'"), 'shadowBlur': L('22D'),
                                  'shadowDistance': L('5D'), 'angle': L('90D')})
        visuals.extend([text(title, x, y - 38, 740, 26, 15, ink), v,
                        text(caption, x, y + 360, 740, 36, 10, '#687A8C')])
        chart_copies.append(v)

    page = read(page_path)
    page.update(width=1600, height=1980, displayOption='FitToWidth')
    page['objects'] = {'background': props({'color': color('#EDF1F5'), 'transparency': L('0D')})}
    if source_path.read_bytes() != source_bytes or page_path.read_bytes() != page_bytes:
        raise SystemExit('Page changed during generation; save and retry')
    for v in visuals:
        write(folder / 'visuals' / v['name'] / 'visual.json', v)
    write(page_path, page)

    assert len(chart_copies) == 8
    assert all(v['visual']['query'] == source['visual']['query'] for v in chart_copies)
    assert all(v.get('filters') == source.get('filters') and v.get('filterConfig') == source.get('filterConfig') for v in chart_copies)
    print('Created eight bar chart variants; source query and date filter preserved on every chart.')


if __name__ == '__main__':
    main()
