"""Apply a consistent finance-app layout to an isolated PBIP copy."""
import copy
import json
import shutil
import uuid
from pathlib import Path
from build_executive_summary import literal as L, container, write, read

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'output/executive-summary'
DEST = ROOT / 'output/finance-app'
NAVY, TEAL, INK, MUTED = '#14283F', '#087F8C', '#1B3047', '#64748B'


def color(value):
    return {'solid': {'color': L(repr(value))}}


def props(value):
    return [{'properties': value}]


def place(v, box):
    x,y,w,h=box
    v['position'].update(x=x,y=y,width=w,height=h)


def text(value, x,y,w,h,size=12,fg=INK,bg=None):
    v=container('textbox','',x,y,w,h)
    v['visual']['visualContainerObjects']={'title':props({'show':L('false')}),
        'background':props({'show':L('true' if bg else 'false'),'color':color(bg or '#FFFFFF'),'transparency':L('0D')})}
    v['visual']['objects']={'general':props({'paragraphs':[{'textRuns':[{'value':value,'textStyle':{
        'fontFamily':'Segoe UI','fontSize':f'{size}pt','color':fg}}]}]})}
    return v


def style(v):
    visual=v['visual']; kind=visual['visualType']
    vc=visual.setdefault('visualContainerObjects',{})
    vc['background']=props({'show':L('true'),'color':color('#FFFFFF'),'transparency':L('0D')})
    vc['border']=props({'show':L('true'),'color':color('#E1E8EF'),'radius':L('10D'),'width':L('1D')})
    vc['visualHeader']=props({'show':L('false')})
    title=vc.setdefault('title',props({}))[0]['properties']
    title.update(fontFamily=L("'Segoe UI'"),fontSize=L('12D'),fontColor=color(INK),alignment=L("'left'"),bold=L('true'))
    objects=visual.setdefault('objects',{})
    if kind=='card':
        objects['labels']=props({'fontSize':L('32D'),'color':color(INK),'labelDisplayUnits':L('1D'),'labelPrecision':L('0D')})
        objects['categoryLabels']=props({'show':L('false')})
        measure=visual['query']['queryState']['Values']['projections'][0]['nativeQueryRef']
        if '%' in measure: objects['labels'][0]['properties']['labelPrecision']=L('1D')
    if 'Chart' in kind:
        for axis in ('categoryAxis','valueAxis'):
            objects.setdefault(axis,props({}))[0]['properties'].update(fontSize=L('10D'),fontFamily=L("'Segoe UI'"),labelColor=color(MUTED),showAxisTitle=L('false'))
        objects['dataPoint']=props({'defaultColor':color(TEAL)})
        objects['legend']=props({'show':L('true'),'position':L("'Top'"),'fontSize':L('10D'),'labelColor':color(MUTED)})
        objects['labels']=props({'show':L('false')})
    if kind in ('tableEx','pivotTable'):
        objects['columnHeaders']=props({'fontColor':color(INK),'backColor':color('#EDF3F7'),'fontFamily':L("'Segoe UI'"),'fontSize':L('11D')})
        objects['values']=props({'fontColorPrimary':color(INK),'backColorPrimary':color('#FFFFFF'),'backColorSecondary':color('#F5F8FA'),'fontSize':L('11D')})
        objects['grid']=props({'gridVertical':L('false'),'gridHorizontal':L('true'),'gridHorizontalColor':color('#E8EEF3'),'rowPadding':L('7D')})
    if kind=='slicer':
        objects['items']=props({'fontColor':color(INK),'background':color('#FFFFFF'),'textSize':L('11D')})
        objects['header']=props({'show':L('true'),'fontColor':color(MUTED),'textSize':L('10D')})


def main():
    if DEST.exists(): raise SystemExit('Output exists; refusing to overwrite')
    shutil.copytree(SOURCE,DEST,ignore=shutil.ignore_patterns('.pbi','.platform'))
    pages=DEST/'JEV.Report/definition/pages'
    meta=read(pages/'pages.json')
    names={
        'executivesummary2026':('Overview','Your financial position, at a glance'),
        'c65861ef956aa27ca503':('Cash flow','Explore income and spending patterns'),
        'ReportSection591a00be3acd3ae3ff43':('Transactions','Explore transaction details and descriptions'),
        'ee59d6a27e5809480ad0':('Payroll','Review salary, deductions and net pay'),
        'ReportSection3b97570e1b61a0a5a0ff':('Pay components','Understand the components of your payslip')}
    meta['pageOrder']=list(names); meta['activePageName']='executivesummary2026'
    write(pages/'pages.json',meta)
    layouts={
        'c65861ef956aa27ca503':{'areaChart':[(248,238,816,590)],'waterfallChart':[(1088,550,480,278)],'columnChart':[(1088,238,480,288)],'slicer':[(248,144,1320,70)]},
        'ReportSection591a00be3acd3ae3ff43':{'slicer':[(248,144,968,70),(1240,144,328,684)],'pivotTable':[(248,238,968,348)],'lineStackedColumnComboChart':[(248,610,968,218)]},
        'ee59d6a27e5809480ad0':{'slicer':[(920,144,304,84),(1240,144,328,84)],'tableEx':[(248,144,648,684)],'kpi':[(920,252,648,260)]},
        'ReportSection3b97570e1b61a0a5a0ff':{'slicer':[(248,144,320,70),(248,238,320,590)],'tableEx':[(592,144,976,104)],'columnChart':[(592,272,976,556)]}}
    for pid,(name,subtitle) in names.items():
        folder=pages/pid; page=read(folder/'page.json'); page.update(displayName=name,width=1600,height=900)
        page['objects']={'background':props({'color':color('#F2F5F8'),'transparency':L('0D')})}
        write(folder/'page.json',page)
        originals=[(p,read(p)) for p in sorted((folder/'visuals').glob('*/visual.json'))]
        counts={}; cards=0
        for path,v in originals:
            kind=v['visual']['visualType']
            if kind in ('shape','textbox'):
                v['isHidden']=True
                write(path,v)
                continue
            style(v)
            if pid=='executivesummary2026':
                if kind=='card':
                    measure=v['visual']['query']['queryState']['Values']['projections'][0]['nativeQueryRef']
                    order={'Total Income Clean':0,'Total Expenses Clean':1,'Total Gross Salary':2,'Net Salary to Gross Salary Ratio (%)':3}
                    place(v,(248+order[measure]*336,176,312,140))
                    if measure=='Total Income Clean': v['visual']['objects']['labels'][0]['properties']['color']=color(TEAL)
                elif kind=='slicer': place(v,(1232,72,336,72))
                elif kind=='lineChart':
                    place(v,(248,344,816,440))
                    v['visual']['objects']['dataPoint']=[{'selector':{'metadata':f'Expenses_New.{m}'},'properties':{'fill':color(c)}} for m,c in [('Total Income Clean',TEAL),('Total Expenses Clean','#E89550')]]
                    v['visual']['objects']['lineStyles']=props({'strokeWidth':L('3D')})
                elif kind=='barChart': place(v,(1088,344,480,440))
            else:
                idx=counts.get(kind,0); counts[kind]=idx+1
                boxes=layouts[pid].get(kind)
                if boxes and idx<len(boxes): place(v,boxes[idx])
            write(path,v)
        shell=[text('',0,0,220,900,bg=NAVY),text('JEV / FINANCE',24,30,180,42,17,'#FFFFFF',NAVY),
               text('PERSONAL WORKSPACE',24,84,180,28,9,'#91A6BC',NAVY),
               text(name,248,28,930,50,27),text(subtitle,248,84,900,40,12,MUTED),
               text('FINANCIAL INTELLIGENCE',24,806,180,32,9,'#91A6BC',NAVY),
               text('Amounts in EUR',24,844,180,28,10,'#FFFFFF',NAVY)]
        for idx,(target,(label,_)) in enumerate(names.items()):
            active=target==pid
            button=container('actionButton','',16,158+idx*64,188,48)
            button['visual']['visualContainerObjects']={
                'title':props({'show':L('false')}),
                'background':props({'show':L('true'),'color':color('#25445F' if active else NAVY),'transparency':L('0D')}),
                'visualLink':props({'show':L('true'),'type':L("'PageNavigation'"),'navigationSection':L(repr(target))})}
            button['visual']['objects']={'text':props({'show':L('true'),'text':L(repr(label)),'fontColor':color('#FFFFFF' if active else '#B9C9D9'),'fontSize':L('12D'),'fontFamily':L("'Segoe UI'")}),
                'outline':props({'show':L('false')}),'icon':props({'show':L('false')})}
            shell.append(button)
        if pid=='executivesummary2026':
            shell.append(text('Credit and debit totals follow the year selection. Payroll indicators are separate from transaction income.',248,810,1320,42,10,MUTED))
        for idx,v in enumerate(shell):
            v['position']['z']=0 if idx==0 else 90000+idx
            write(folder/'visuals'/v['name']/'visual.json',v)
    report=read(DEST/'JEV.Report/definition/report.json')
    report['objects']['outspacePane']=props({'expanded':L('false')})
    write(DEST/'JEV.Report/definition/report.json',report)
    print(DEST/'JEV.pbip')


if __name__=='__main__': main()
