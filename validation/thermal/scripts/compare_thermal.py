"""Descriptive comparisons only. No interpolation, pairing, tests, or imputation."""
from pathlib import Path
import argparse, csv, json, statistics
from analyze_thermal import write_csv

def read(stats,label):
    with (stats/f'{label}_temperature_source_data.csv').open(encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    for r in rows:
        for k in ['elapsed_s','tj_C']: r[k]=float(r[k])
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    STATS=a.root/'statistics'
    air=read(STATS,'AIR_20261014_190802'); water=read(STATS,'WATER_20261014_181314')
    common=min(air[-1]['elapsed_s'],water[-1]['elapsed_s'])
    # Reconstruct an explicitly post-hoc alternative; not the recovered old analysis.
    anchor=next(r for r in air if r['tj_C']==water[0]['tj_C'])
    definitions=[('full_record','air',air,0,None),('full_record','water',water,0,None),
      ('common_elapsed_window','air',air,0,common),('common_elapsed_window','water',water,0,common),
      ('posthoc_first_exact_initial_match','air',air,anchor['elapsed_s'],common),
      ('posthoc_first_exact_initial_match','water',water,0,common)]
    summary=[]; data=[]
    for window,condition,rows,offset,limit in definitions:
        chosen=[r for r in rows if r['elapsed_s']>=offset and (limit is None or r['elapsed_s']-offset<=limit)]
        v=[r['tj_C'] for r in chosen]
        summary.append(dict(window=window,condition=condition,independent_runs=1,n_samples=len(v),
          nominal_window_s=limit,excluded_initial_samples=sum(r['elapsed_s']<offset for r in rows),
          origin_shift_s=offset,first_timestamp=chosen[0]['timestamp'],last_timestamp=chosen[-1]['timestamp'],
          actual_span_s=chosen[-1]['elapsed_s']-chosen[0]['elapsed_s'],first_C=v[0],last_C=v[-1],
          delta_C=v[-1]-v[0],mean_C=statistics.mean(v),max_C=max(v),min_C=min(v)))
        for r in chosen:
            data.append(dict(window=window,condition=condition,source_csv_line=r['source_csv_line'],
              timestamp=r['timestamp'],original_elapsed_s=r['elapsed_s'],display_elapsed_s=r['elapsed_s']-offset,tj_C=r['tj_C']))
    write_csv(STATS/'comparison_summary.csv',summary)
    write_csv(STATS/'comparison_source_data.csv',data)
    report={'comparison_limit_s':common,'posthoc_air_anchor':anchor,'paired':False,
      'interpolated':False,'smoothing':False,'equivalent_workload_verified':False,
      'notes':['Elapsed origin is first logged sample, not verified workload start.',
       'Primary comparison retains different initial temperatures.',
       'Secondary anchor is first exact equality to initial water tj; excludes early air samples.',
       'The old matched-30min CSV was not recovered. This is a new transparent reconstruction.',
       'Time samples are not replicate trials. No inferential p-values or confidence intervals.'],
      'summaries':summary}
    (STATS/'comparison_methods.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
