"""Create four comparable line chart formats on Line Plot Test in place."""
import copy
import uuid
from pathlib import Path
from build_executive_summary import read, write, literal as L
from polish_report import color, props, text

ROOT=Path(__file__).resolve().parent/'output/finance-app/JEV.Report/definition/pages'


def main():
    pages=[p for p in ROOT.glob('*/page.json') if read(p).get('displayName','').lower()=='line plot test']
    if len(pages)!=1: raise SystemExit('Expected one Line Plot Test page')
    page_path=pages[0]; folder=page_path.parent
    paths=list(folder.glob('visuals/*/visual.json'))
    if len(paths)!=1: raise SystemExit('Expected one source visual; refusing to replace an existing gallery')
    source_path=paths[0]; original=source_path.read_bytes(); original_page=page_path.read_bytes()
    source=read(source_path)
    # Retain the source category selectors, query, filters and chronological sorting.
    selectors={}
    for item in source['visual']['objects'].get('lineStyles',[]):
        if 'selector' in item:
            val=item['selector']['data'][0]['scopeId']['Comparison']['Right']['Literal']['Value'].strip("'")
            selectors[val]=copy.deepcopy(item['selector'])
    if not {'Credit','Debit'} <= selectors.keys(): raise SystemExit('Missing source series selectors')
    variants=[
        ('01 / Essential','Precise straight lines, fine strokes and minimal decoration.','#FFFFFF','#334155','#CBD5E1',0,2,False,'linear','#168A87','#CC7845'),
        ('02 / Floating Cloud','Your preferred soft surface, with airy shadows and smooth lines.','#FFFFFF','#31445B','#E4EBF2',24,3,False,'smooth','#087F8C','#D18A54'),
        ('03 / Data focus','Visible data points and a dashed debit series for easy comparison.','#F8FBFE','#253D58','#CDDEEC',12,3,True,'linear','#2468A2','#AD5A29'),
        ('04 / Midnight studio','Dark canvas, bright series and subtle gridlines.','#112237','#E6F1FF','#29425C',20,3,True,'linear','#66E3D4','#FFB47C'),
    ]
    planned=[]
    for idx,(title,caption,bg,fg,border,radius,width,markers,curve,credit,debit) in enumerate(variants):
        v=copy.deepcopy(source)
        if idx: v['name']=uuid.uuid4().hex[:20]
        x=40+(idx%2)*780;y=172+(idx//2)*432
        v['position']={'x':x,'y':y,'width':740,'height':344,'z':idx+1,'tabOrder':idx+1}
        vis=v['visual'];vis['visualType']='lineChart'
        obj=vis['objects'];obj['lineStyles']=props({'lineChartType':L(repr(curve)),'strokeWidth':L(f'{width}D'),
            'showMarker':L('true' if markers else 'false'),'markerSize':L('5D'),'areaShow':L('false'),'lineStyle':L("'solid'")})
        if idx==2:
            obj['lineStyles'].append({'selector':selectors['Debit'],'properties':{'lineStyle':L("'dashed'")}})
        obj['dataPoint']=[{'selector':selectors[k],'properties':{'fill':color(c)}} for k,c in [('Credit',credit),('Debit',debit)]]
        axis_color='#A4B6CB' if idx==3 else '#64748B'
        for axis in ('categoryAxis','valueAxis'):
            obj.setdefault(axis,props({}))[0]['properties'].update(labelColor=color(axis_color),fontSize=L('10D'),fontFamily=L("'Segoe UI'"),showAxisTitle=L('false'))
        obj['valueAxis'][0]['properties'].update(start=L('0D'),gridlineShow=L('true' if idx>=2 else 'false'),gridlineColor=color('#263B52' if idx==3 else '#E3EBF2'))
        obj['legend']=props({'show':L('true'),'position':L("'Top'"),'showTitle':L('false'),'fontSize':L('11D'),'labelColor':color(axis_color)})
        obj['labels']=props({'show':L('false')})
        vc=vis['visualContainerObjects']
        vc['title']=props({'show':L('true'),'text':L("'Income vs expenses'"),'fontFamily':L("'Segoe UI'"),'fontSize':L('13D'),'fontColor':color(fg),'alignment':L("'left'")})
        vc['background']=props({'show':L('true'),'color':color(bg),'transparency':L('0D')})
        vc['border']=props({'show':L('true'),'color':color(border),'radius':L(f'{radius}D'),'width':L('1D')})
        vc['dropShadow']=props({'show':L('true' if idx in (1,3) else 'false'),'color':color('#61778E'),
            'transparency':L('80D'),'position':L("'Outer'"),'shadowBlur':L('24D'),'shadowDistance':L('5D'),'angle':L('90D')})
        planned.append(v)
        planned.extend([text(title,x,y-46,740,34,16),text(caption,x,y+356,740,40,11,'#64748B')])
    planned.extend([text('LINE STUDIO / Four perspectives',40,22,1520,52,27),
                    text('Same Credit / Debit data, date hierarchy and source date filter. Styling only; all value axes start at zero.',40,84,1520,42,12,'#64748B')])
    page=read(page_path);page.update(width=1600,height=1040,displayOption='FitToPage')
    page['objects']={'background':props({'color':color('#EDF1F5'),'transparency':L('0D')})}
    if source_path.read_bytes()!=original or page_path.read_bytes()!=original_page: raise SystemExit('Page changed; save and retry')
    for v in planned:write(folder/'visuals'/v['name']/'visual.json',v)
    write(page_path,page)
    charts=[v for v in planned if v['visual']['visualType']=='lineChart']
    assert len(charts)==4
    assert all(v['visual']['query']==source['visual']['query'] and v.get('filterConfig')==source.get('filterConfig') for v in charts)
    print('Created four line-chart variants; identical queries and source filters verified.')


if __name__=='__main__':main()
