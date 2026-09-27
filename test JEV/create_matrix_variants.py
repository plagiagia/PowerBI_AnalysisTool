"""Four deep-hierarchy matrix designs on the existing Matrix Test page."""
import copy
import uuid
from pathlib import Path
from build_executive_summary import read, write, literal as L, projection
from polish_report import props, color, text

ROOT=Path(__file__).resolve().parent/'output/finance-app/JEV.Report/definition/pages'


def main():
    pages=[p for p in ROOT.glob('*/page.json') if read(p).get('displayName','').lower()=='matrix test']
    if len(pages)!=1:raise SystemExit('Expected one Matrix Test page')
    pagepath=pages[0];folder=pagepath.parent;paths=list(folder.glob('visuals/*/visual.json'))
    if len(paths)!=1:raise SystemExit('Expected one source matrix')
    sourcepath=paths[0];before=sourcepath.read_bytes();pagebefore=pagepath.read_bytes();source=read(sourcepath)
    if source['visual']['visualType']!='pivotTable':raise SystemExit('Source is not a matrix')
    rows=[projection('Expenses_New',n,'Column') for n in ['Category','Type','Description','Date']]
    cols=[projection('DT_Calendar',n,'Column') for n in ['Year','Quarter','Month Name']]
    for p in rows+cols:p['active']=True
    designs=[
        ('01 / Cloud explorer','Compact','Nested rows with generous indentation and soft teal subtotals.','#EDF6F5','#155E59','#F6FAFA',9,22),
        ('02 / Structured outline','Outline','Separate hierarchy columns make parent and child levels easier to track.','#EAF0FA','#234E7C','#F5F8FD',7,18),
        ('03 / Audit ledger','Tabular','Repeated parent labels, tighter rows and subtle column rules for tracing details.','#ECEFF3','#26384C','#F5F6F8',5,18),
        ('04 / High-contrast review','Compact','Dark column headings, spacious light rows and strong subtotal bands.','#20374F','#FFFFFF','#F2F6FA',10,26),
    ]
    visuals=[text('MATRIX STUDIO / Explore the details',40,24,1520,50,28),
             text('Rows: Category > Type > Description > Date. Columns: Year > Quarter > Month. Values: original Total Expenses measure.',40,82,1520,40,12),
             text('Use + / - to open a branch. The visual header exposes drill controls; choose Rows or Columns. Date-level rows may aggregate multiple transactions.',40,122,1520,42,11,'#64748B')]
    matrices=[]
    for idx,(title,layout,caption,header,headerfg,stripe,padding,indent) in enumerate(designs):
        y=244+idx*626
        v=copy.deepcopy(source)
        if idx:v['name']=uuid.uuid4().hex[:20]
        v['position']={'x':40,'y':y,'width':1520,'height':504,'z':idx+1,'tabOrder':idx+1}
        vis=v['visual'];q=vis['query']['queryState'];q['Rows']={'projections':copy.deepcopy(rows)};q['Columns']={'projections':copy.deepcopy(cols)}
        vis['query']['sortDefinition']={'sort':[{'field':copy.deepcopy(rows[0]['field']),'direction':'Ascending'}]}
        vis['expansionStates']=[]
        for role,fields in [('Rows',rows),('Columns',cols)]:
            vis['expansionStates'].append({'roles':[role],'levels':[{'queryRefs':[p['queryRef']],
                'identityKeys':[copy.deepcopy(p['field'])],'isCollapsed':True,'isPinned':True} for p in fields],'root':{}})
        subtotal='#E6F0F4' if idx==3 else header
        objects={
            'general':props({'layout':L(repr(layout))}),
            'rowHeaders':props({'showExpandCollapseButtons':L('true'),'expandCollapseButtonsSize':L('13D'),
                'steppedLayoutIndentation':L(f'{indent}D'),'repeatRowHeaders':L('true' if idx==2 else 'false'),
                'fontFamily':L("'Segoe UI'"),'fontSize':L('11D'),'fontColor':color('#263B50'),
                'backColor':color('#FFFFFF'),'wordWrap':L('true')}),
            'columnHeaders':props({'fontFamily':L("'Segoe UI Semibold'"),'fontSize':L('11D'),
                'fontColor':color(headerfg),'backColor':color(header),'wordWrap':L('true')}),
            'values':props({'fontFamily':L("'Segoe UI'"),'fontSize':L('11D'),'fontColorPrimary':color('#263B50'),
                'fontColorSecondary':color('#263B50'),'backColorPrimary':color('#FFFFFF'),
                'backColorSecondary':color(stripe),'wordWrap':L('false')}),
            'grid':props({'rowPadding':L(f'{padding}D'),'gridHorizontal':L('true'),'gridHorizontalColor':color('#E3EAF0'),
                'gridVertical':L('true' if idx==2 else 'false'),'gridVerticalColor':color('#E3EAF0')}),
            'subTotals':props({'rowSubtotals':L('true'),'columnSubtotals':L('true'),'rowSubtotalsPosition':L("'Top'"),
                'perRowLevel':L('false'),'fontColor':color('#254A60'),'backColor':color(subtotal),
                'bold':L('true'),'applyToHeaders':L('true'),'fontSize':L('11D')}),
            'columnWidth':[{'selector':{'metadata':p['queryRef']},'properties':{'value':L(f'{w}D')}}
                for p,w in zip(rows,[170,190,470,150])],
        }
        for total in ('rowTotal','columnTotal'):
            objects[total]=props({'fontColor':color('#FFFFFF'),'backColor':color('#28445D'),
                'bold':L('true'),'applyToHeaders':L('true'),'fontSize':L('11D')})
        vis['objects']=objects
        vis['visualContainerObjects']={
            'title':props({'show':L('true'),'text':L("'Expenses by category and date'"),'fontSize':L('12D'),'fontFamily':L("'Segoe UI'"),'fontColor':color('#263B50')}),
            'background':props({'show':L('true'),'color':color('#FFFFFF'),'transparency':L('0D')}),
            'border':props({'show':L('true'),'color':color('#DAE3EB'),'radius':L('16D' if idx==0 else '6D'),'width':L('1D')}),
            'visualHeader':props({'show':L('true')}),
            'dropShadow':props({'show':L('true' if idx==0 else 'false'),'color':color('#72859B'),'transparency':L('82D'),
                'position':L("'Outer'"),'shadowBlur':L('20D'),'shadowDistance':L('4D'),'angle':L('90D')}),
        }
        matrices.append(v);visuals.extend([text(title,40,y-70,1520,34,18),text(caption,40,y-34,1520,28,11,'#64748B'),v])
    page=read(pagepath);page.update(width=1600,height=2670,displayOption='FitToWidth')
    page['objects']={'background':props({'color':color('#EDF1F5'),'transparency':L('0D')})}
    if sourcepath.read_bytes()!=before or pagepath.read_bytes()!=pagebefore:raise SystemExit('Page changed during generation')
    for v in visuals:write(folder/'visuals'/v['name']/'visual.json',v)
    write(pagepath,page)
    for v in matrices:
        assert v['visual']['query']['queryState']['Values']==source['visual']['query']['queryState']['Values']
        assert v.get('filterConfig')==source.get('filterConfig')
        assert len(v['visual']['query']['queryState']['Rows']['projections'])==4
        assert len(v['visual']['query']['queryState']['Columns']['projections'])==3
    print('Created four matrix variants with four row levels, three column levels, and unchanged measure/filter definitions.')


if __name__=='__main__':main()
