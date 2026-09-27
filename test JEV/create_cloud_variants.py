"""Add five refinements of Floating Cloud to the current report in place."""
import copy
import uuid
from pathlib import Path
from build_executive_summary import read, write, literal as L
from polish_report import color, props, text

ROOT=Path(__file__).resolve().parent/'output/finance-app/JEV.Report/definition/pages'
VARIANTS=[
    ('01 / Air cushion','Wide, quiet shadow. The closest refinement of your favorite.', '#FFFFFF','#31445B','#72859B',80,26,5,24,'Segoe UI Light',36,None),
    ('02 / Elevated pearl','More lift, a crisp edge, and stronger number typography.', '#FFFFFF','#263B52','#52677F',72,20,9,20,'Segoe UI Semibold',34,None),
    ('03 / Arctic mist','Cool-white surface with a pale blue shadow and fine accent.', '#F8FCFF','#284D6C','#659DC9',72,28,5,28,'Segoe UI Light',36,'#B3D6EF'),
    ('04 / Mint whisper','Soft green tint, restrained teal detail, gentle elevation.', '#FAFFFD','#246257','#62998B',78,24,6,24,'Segoe UI',34,'#A7DCCB'),
    ('05 / Porcelain','Warm ivory, an editorial number, and a soft ambient shadow.', '#FFFEFB','#594D42','#A39584',78,30,4,30,'Georgia',34,None),
]


def main():
    candidates=[]
    for p in ROOT.glob('*/visuals/*/visual.json'):
        v=read(p)
        if '10 / Floating cloud' in str(v.get('visual',{}).get('visualContainerObjects',{}).get('title',[])):
            candidates.append(v)
    if len(candidates)!=1: raise SystemExit('Expected exactly one Floating Cloud template')
    template=candidates[0]
    pid='cloudvariants'+uuid.uuid4().hex[:12]
    folder=ROOT/pid
    metadata_path=ROOT/'pages.json'; metadata_bytes=metadata_path.read_bytes(); metadata=read(metadata_path)
    positions=[(64,204),(576,204),(1088,204),(320,584),(832,584)]
    visuals=[text('FLOATING CLOUD',64,34,1450,52,29),
             text('Five refinements of your favorite card. Same Income measure, same scale — choose by number.',64,96,1450,38,12,'#64748B')]
    for i,((title,caption,bg,ink,shadow,transparency,blur,distance,radius,font,size,accent),(x,y)) in enumerate(zip(VARIANTS,positions)):
        v=copy.deepcopy(template);v['name']=uuid.uuid4().hex[:20]
        v['position']={'x':x,'y':y,'width':448,'height':244,'z':i+1,'tabOrder':i+1}
        vc=v['visual']['visualContainerObjects']
        vc['title']=props({'show':L('false')})
        vc['background']=props({'show':L('true'),'color':color(bg),'transparency':L('0D')})
        vc['border']=props({'show':L('true'),'color':color('#E6EBEF' if i<2 else bg), 'radius':L(f'{radius}D'),'width':L('1D')})
        vc['dropShadow']=props({'show':L('true'),'color':color(shadow),'transparency':L(f'{transparency}D'),
                               'position':L("'Outer'"),'shadowBlur':L(f'{blur}D'),
                               'shadowDistance':L(f'{distance}D'),'angle':L('90D'),'shadowSpread':L('0D')})
        objects=v['visual']['objects']
        objects['value'][0]['properties'].update(fontFamily=L(repr(font)),fontSize=L(f'{size}D'),fontColor=color(ink),bold=L('true' if i==1 else 'false'))
        objects['label'][0]['properties'].update(fontColor=color('#6A7D8E'),fontSize=L('12D'))
        objects['fillCustom'][0]['properties']['fillColor']=color(bg)
        objects['padding'][0]['properties']['paddingUniform']=L('24L')
        objects['accentBar'][0]['properties'].update(show=L('true' if accent else 'false'),color=color(accent or bg),position=L("'Bottom'"),width=L('2D'))
        vc['general']=props({'altText':L(repr(title+'. Income. '+caption))})
        visuals.extend([v,text(title,x,y-46,448,32,14,ink),text(caption,x,y+264,448,62,11,'#64748B')])
    if metadata_path.read_bytes()!=metadata_bytes: raise SystemExit('Report metadata changed during generation')
    page={'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json',
          'name':pid,'displayName':'Floating Cloud · 5 variants','width':1600,'height':1000,'displayOption':'FitToPage',
          'objects':{'background':props({'color':color('#EDF1F5'),'transparency':L('0D')})}}
    write(folder/'page.json',page)
    for v in visuals: write(folder/'visuals'/v['name']/'visual.json',v)
    metadata['pageOrder'].append(pid); metadata['activePageName']=pid
    write(metadata_path,metadata)
    cards=[v for v in visuals if v['visual']['visualType']=='cardVisual']
    assert len(cards)==5 and all(v['visual']['query']==template['visual']['query'] for v in cards)
    print('Added Floating Cloud · 5 variants. Five native cards; source card and original pages unchanged.')


if __name__=='__main__':main()
