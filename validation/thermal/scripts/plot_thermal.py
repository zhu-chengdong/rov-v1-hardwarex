"""Plot audited measurements, not synthetic results. Python/Matplotlib only.

Use --root for the results directory. Panel QA tool is a local authoring dependency,
passed explicitly with --qa-tools. Raw points are retained without smoothing.
"""
from pathlib import Path
import argparse, csv, json, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.transforms import ScaledTranslation

plt.rcParams.update({'font.family':'Arial','font.size':8,'axes.labelsize':8,
 'axes.titlesize':9,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,
 'axes.linewidth':0.7,'lines.linewidth':0.85,'pdf.fonttype':42,'ps.fonttype':42,
 'svg.fonttype':'none','savefig.dpi':600,'figure.dpi':150,'axes.unicode_minus':False})
COLORS={'air':'#B85C00','water':'#0072B2'}
STYLES={'air':'-','water':(0,(4,1.8))}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--root',type=Path,required=True)
    gate=p.add_mutually_exclusive_group(required=True)
    gate.add_argument('--qa-tools',type=Path)
    gate.add_argument('--skip-alignment-qa',action='store_true',help='Explicitly skip the optional local authoring dependency; report NOT RUN, never PASS.')
    a=p.parse_args()
    if a.qa_tools:
        sys.path.insert(0,str(a.qa_tools))
        from audit_panel_alignment import require_matplotlib_panel_alignment
    with (a.root/'statistics/comparison_source_data.csv').open(encoding='utf-8') as f: data=list(csv.DictReader(f))
    out=a.root/'figures'; qa=a.root/'qa';out.mkdir(parents=True,exist_ok=True);qa.mkdir(exist_ok=True)
    def draw(ax,window,condition,label):
        rows=[r for r in data if r['window']==window and r['condition']==condition]
        ax.plot([float(r['display_elapsed_s'])/60 for r in rows],[float(r['tj_C']) for r in rows],
          color=COLORS[condition],linestyle=STYLES[condition],label=label,zorder=3)
    def style(ax,xmax):
        ax.set(xlim=(0,xmax),ylim=(48.5,55.5),xlabel='Elapsed time (min)',ylabel='Jetson tj temperature (°C)')
        ax.set_yticks([49,51,53,55]);ax.spines[['top','right']].set_visible(False)
        ax.tick_params(direction='out',length=3,width=.6);ax.set_axisbelow(True)
    def label(ax,letter,title):
        ax.text(0,1.075,letter,transform=ax.transAxes+ScaledTranslation(-28/72,0,ax.figure.dpi_scale_trans),fontweight='bold',fontsize=10,ha='left',va='bottom')
        ax.set_title(title,loc='left',pad=12)
    def export(fig,name):
        fig.savefig(out/f'{name}.pdf',facecolor='white')
        fig.savefig(out/f'{name}.svg',facecolor='white')
        fig.savefig(out/f'{name}.png',dpi=600,facecolor='white')
        plt.close(fig)
    fig=plt.figure(figsize=(180/25.4,136/25.4))
    gs=fig.add_gridspec(2,2,left=.105,right=.97,bottom=.15,top=.91,wspace=.30,hspace=.65)
    air=fig.add_subplot(gs[0,0]);water=fig.add_subplot(gs[0,1]);common=fig.add_subplot(gs[1,:])
    draw(air,'full_record','air','Air');style(air,120);air.set_xticks([0,30,60,90,120]);label(air,'a','Air · complete record')
    draw(water,'full_record','water','Water');style(water,30);water.set_xticks([0,10,20,30]);label(water,'b','Water · complete record')
    draw(common,'common_elapsed_window','air','Air · initial 49.656 °C')
    draw(common,'common_elapsed_window','water','Water · initial 50.156 °C')
    style(common,30);common.set_xticks([0,5,10,15,20,25,30]);label(common,'c','Common elapsed window · 0–29.85 min')
    # Legend sits above the highest recorded value; no opaque masking of data.
    common.legend(loc='upper left',ncol=2,frameon=False,borderaxespad=.3,handlelength=2.7)
    fig.text(.105,.035,'One run per environment; workload equivalence and ambient temperatures not verified.',fontsize=8)
    fig.canvas.draw()
    if a.qa_tools:
        require_matplotlib_panel_alignment(fig,json_out=qa/'Fig_T1_panel_alignment.json',overlay_svg=qa/'Fig_T1_panel_alignment.svg',tolerance_pt=1.5)
    else:
        (qa/'Fig_T1_panel_alignment.json').write_text(json.dumps({'status':'NOT RUN','reason':'explicit --skip-alignment-qa'})+'\n',encoding='utf-8')
    export(fig,'Fig_T1_thermal_records_and_common_window')

    fig,ax=plt.subplots(figsize=(140/25.4,88/25.4));fig.subplots_adjust(left=.13,right=.97,bottom=.25,top=.84)
    draw(ax,'posthoc_first_exact_initial_match','air','Air · starts 315 s after first log')
    draw(ax,'posthoc_first_exact_initial_match','water','Water · starts at first log')
    style(ax,30);ax.set_xlabel('Elapsed time from selected anchor (min)');ax.set_xticks([0,5,10,15,20,25,30])
    ax.set_title('Exploratory initial-temperature match',loc='left',pad=13)
    ax.legend(loc='upper left',frameon=False,borderaxespad=.3,handlelength=2.7)
    fig.text(.13,.095,'Both anchors: 50.156 °C; 63 early air samples excluded.',fontsize=8)
    fig.text(.13,.045,'Post-hoc window; one unpaired run per environment.',fontsize=8)
    fig.canvas.draw()
    (qa/'Fig_S1_panel_alignment.json').write_text(json.dumps({'status':'NOT APPLICABLE','reason':'single panel'})+'\n',encoding='utf-8')
    export(fig,'Fig_S1_posthoc_initial_temperature_match')
    print('Exported two figures in PDF/SVG/PNG; retained unsmoothed observations.')

if __name__=='__main__': main()
