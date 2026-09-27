"""Build twenty native cardVisual styles on the user's Card test page in place."""
import copy
import hashlib
import json
import uuid
from pathlib import Path
from build_executive_summary import literal as L, write, read
from polish_report import color, props, text

ROOT=Path(__file__).resolve().parent/'output/finance-app/JEV.Report/definition/pages'
PAGE=ROOT/'bca357581790d2830655'
SOURCE=PAGE/'visuals/4723c3c003e57ce7bba7/visual.json'

# Name, background, value, accent, radius, typeface, point size, alignment.
STYLES=[
 ('Essential','#FFFFFF','#1B3047','#CBD5E1',0,'Segoe UI',30,'left'),
 ('Fine outline','#FFFFFF','#334155','#94A3B8',0,'Segoe UI',30,'left'),
 ('Editorial','#FAF9F6','#292524','#A8A29E',0,'Georgia',32,'left'),
 ('Centered','#FFFFFF','#0F172A','#CBD5E1',8,'Segoe UI',34,'center'),
 ('Teal accent','#FFFFFF','#087F8C','#087F8C',8,'Segoe UI',32,'left'),
 ('Executive blue','#F1F5FC','#193B65','#3468A0',10,'Segoe UI Semibold',32,'left'),
 ('Soft mint','#E9F6F0','#155E4B','#35A781',16,'Segoe UI',32,'left'),
 ('Warm sandstone','#FCF2E4','#79512B','#C28A49',16,'Georgia',32,'left'),
 ('Lavender','#F1EDFC','#58418C','#9874CB',20,'Segoe UI',32,'center'),
 ('Floating cloud','#FFFFFF','#31445B','#D9E3EC',24,'Segoe UI Light',34,'center'),
 ('Midnight executive','#152A43','#FFFFFF','#769ABF',12,'Segoe UI Semibold',32,'left'),
 ('Graphite','#262B34','#F1F5F9','#8C99AC',4,'Segoe UI',32,'left'),
 ('Emerald premium','#103D37','#D6FFF1','#50CDA7',16,'Segoe UI Semibold',32,'left'),
 ('Black and gold','#1F1E1B','#F3DBA2','#C6A567',8,'Georgia',32,'center'),
 ('Terminal','#091812','#83E8B4','#33B878',0,'Consolas',30,'left'),
 ('Electric blue','#0B1831','#8BCFFF','#339CFF',12,'Consolas',32,'left'),
 ('Neon violet','#1D1136','#E0BFFF','#AB6BFF',18,'Segoe UI Semibold',34,'center'),
 ('Cyber cyan','#071D28','#89F2FF','#16D4ED',4,'Consolas',32,'left'),
 ('Plasma magenta','#270D25','#FFC5F0','#FF5EC4',24,'Segoe UI Semibold',34,'center'),
 ('Mission control','#070F1F','#BCFFF4','#45F0D0',0,'Consolas',34,'left'),
]


def scoped(properties):
    return [{'selector':{'id':'default'},'properties':properties}]


def main():
    original=SOURCE.read_bytes(); original_page=(PAGE/'page.json').read_bytes()
    files=list((PAGE/'visuals').glob('*/visual.json'))
    if len(files)!=1: raise SystemExit('Expected the original single-card page; refusing to overwrite a modified gallery.')
    source=json.loads(original)
    planned=[]
    for idx,(name,bg,fg,accent,radius,font,size,align) in enumerate(STYLES):
        v=copy.deepcopy(source)
        if idx: v['name']=uuid.uuid4().hex[:20]
        x=32+(idx%4)*392; y=116+(idx//4)*224
        v['position']={'x':x,'y':y,'width':368,'height':200,'z':idx+1,'tabOrder':idx+1}
        vc=v['visual']['visualContainerObjects']
        vc['title']=props({'show':L('true'),'text':L(repr(f'{idx+1:02d} / {name}')),
                          'fontSize':L('11D'),'fontFamily':L("'Segoe UI'"),
                          'fontColor':color(fg),'bold':L('false'),'alignment':L("'left'")})
        vc['background']=props({'show':L('true'),'color':color(bg),'transparency':L('0D')})
        vc['border']=props({'show':L('false' if idx==0 else 'true'),'color':color(accent),
                           'radius':L(f'{radius}D'),'width':L('2D' if idx>=14 else '1D')})
        vc['dropShadow']=props({'show':L('true' if idx in (9,12,15,16,17,18,19) else 'false'),
                               'color':color(accent if idx>=15 else '#64748B'),
                               'transparency':L('65D'),'position':L("'Outer'"),
                               'shadowBlur':L('12D'),'shadowDistance':L('3D'),'angle':L('90D')})
        v['visual']['objects']={
            'value':scoped({'show':L('true'),'fontFamily':L(repr(font)),'fontSize':L(f'{size}D'),
                            'fontColor':color(fg),'horizontalAlignment':L(repr(align)),
                            'bold':L('true' if idx in (5,10,12,16,18,19) else 'false'),
                            'labelDisplayUnits':L('1D'),'labelPrecision':L('0L')}),
            'label':scoped({'show':L('true'),'text':L("'Income'"),'fontFamily':L("'Segoe UI'"),
                            'fontSize':L('11D'),'fontColor':color(fg),'position':L("'aboveValue'"),
                            'horizontalAlignment':L(repr(align))}),
            'fillCustom':scoped({'show':L('true'),'fillColor':color(bg),'transparency':L('0D')}),
            'outline':scoped({'show':L('false')}),
            'accentBar':scoped({'show':L('true' if idx>=4 and idx!=9 else 'false'),
                                'color':color(accent),'position':L(repr('Bottom' if idx>=15 else 'Left')),
                                'width':L('4D'),'transparency':L('0D')}),
            'padding':scoped({'paddingSelection':L("'Custom'"),'paddingUniform':L('16L')}),
            'glowCustom':scoped({'show':L('true' if idx>=15 else 'false'),'color':color(accent),
                                 'transparency':L('75D'),'glowSpread':L('2D'),
                                 'shadowBlur':L('10D'),'position':L("'Inner'")}),
        }
        planned.append((PAGE/'visuals'/v['name']/'visual.json',v))
    header=text('CARD STUDIO  /  20 ways to show Income',32,20,1520,44,25)
    subtitle=text('01–04 minimal  /  05–10 refined  /  11–14 premium dark  /  15–20 futuristic. Same measure and scale in every card.',32,68,1520,30,11)
    for v in (header,subtitle): planned.append((PAGE/'visuals'/v['name']/'visual.json',v))
    page=json.loads(original_page); page.update(width=1600,height=1250,displayOption='FitToWidth')
    page['objects']={'background':props({'color':color('#E8EDF3'),'transparency':L('0D')})}
    # Detect user saves during generation before changing the target files.
    if SOURCE.read_bytes()!=original or (PAGE/'page.json').read_bytes()!=original_page:
        raise SystemExit('Page changed during generation; rerun after saving.')
    for path,v in planned: write(path,v)
    write(PAGE/'page.json',page)
    cards=[read(p) for p in (PAGE/'visuals').glob('*/visual.json') if read(p)['visual']['visualType']=='cardVisual']
    assert len(cards)==20
    assert all(c['visual']['query']==source['visual']['query'] for c in cards)
    assert all(c.get('filterConfig')==source.get('filterConfig') for c in cards)
    print('Created 20 numbered native card variants in place; identical measure queries and filters verified.')


if __name__=='__main__': main()
