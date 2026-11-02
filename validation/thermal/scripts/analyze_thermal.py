"""Read-only thermal audit. No device commands, plotting, or source modification.

Uses the literal named tj channel (not recomputed maximum of other sensors).
Retains all input rows, checks original row order, compares CSV to raw LOG,
and writes descriptive statistics. A time sample is not an independent trial.
"""
from pathlib import Path
import argparse, csv, hashlib, json, math, re, statistics
from collections import Counter
from datetime import datetime

CHANNELS = ['tj_C','CPU_C','GPU_C','SOC0_C','SOC1_C','SOC2_C']
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields or list(rows[0])); w.writeheader(); w.writerows(rows)
def slope(xs,ys):
    if len(xs)<2:return None
    xm,ym=statistics.mean(xs),statistics.mean(ys)
    den=sum((x-xm)**2 for x in xs)
    return sum((x-xm)*(y-ym) for x,y in zip(xs,ys))/den if den else None
def quantile(x,q):
    a=sorted(x); p=(len(a)-1)*q; lo=math.floor(p); hi=math.ceil(p)
    return a[lo]+(a[hi]-a[lo])*(p-lo)
def inspect_run(csvpath,logpath,label,out):
    before={str(p):sha(p) for p in [csvpath,logpath]}
    with csvpath.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f); headers=reader.fieldnames; raw=list(reader)
    assert headers==['timestamp']+CHANNELS,headers
    clean=[]; invalid=[]
    for n,r in enumerate(raw,2):
        try:
            t=datetime.fromisoformat(r['timestamp']); assert t.tzinfo is not None
            v={k:float(r[k]) for k in CHANNELS}; assert all(math.isfinite(x) for x in v.values())
            clean.append({'source_csv_line':n,'timestamp':r['timestamp'],'_time':t,**v})
        except (ValueError,AssertionError,KeyError,TypeError) as e:invalid.append({'line':n,'row':r,'reason':str(e)})
    assert clean,'No valid data'
    t0=clean[0]['_time']
    for r in clean:r['elapsed_s']=(r['_time']-t0).total_seconds()
    diffs=[(b['_time']-a['_time']).total_seconds() for a,b in zip(clean,clean[1:])]
    duplicates=len(clean)-len({r['timestamp'] for r in clean})
    assert not duplicates and all(d>0 for d in diffs),'Non-monotonic or duplicate time; manual audit needed'
    duration=clean[-1]['elapsed_s']
    rawlines=logpath.read_text(encoding='utf-8-sig').splitlines()
    logs=[]; log_invalid=[]; log_metadata=[]
    monitor_format=any('| tj=' in line for line in rawlines)
    for ln,line in enumerate(rawlines,1):
        if not line.strip():continue
        if monitor_format and not re.match(r'^\d{4}-\d{2}-\d{2}T',line):
            log_metadata.append({'line':ln,'text':line}); continue
        try:
            timestamp=line.split()[0]; datetime.fromisoformat(timestamp)
            sep='=' if monitor_format else '@'
            temps=dict((k,float(v)) for k,v in re.findall(r'\b([A-Za-z][A-Za-z0-9]*)'+sep+r'(-?\d+(?:\.\d+)?)C',line))
            values={k:temps.get(k[:-2]) for k in CHANNELS}
            assert values['tj_C'] is not None
            cpu=re.search(r'CPU \[([^\]]+)\]',line)
            pairs=re.findall(r'(\d+)%@(\d+)',cpu.group(1)) if cpu else []
            ram=re.search(r'RAM (\d+)/(\d+)MB',line)
            gpu=re.search(r'GR3D_FREQ (\d+)%@\[([^\]]*)\]',line)
            logs.append({'source_log_line':ln,'timestamp':timestamp,**values,
              'cpu_mean_utilization_pct':statistics.mean(int(p[0]) for p in pairs) if pairs else None,
              'cpu_frequency_min_mhz':min(int(p[1]) for p in pairs) if pairs else None,
              'cpu_frequency_max_mhz':max(int(p[1]) for p in pairs) if pairs else None,
              'cpu_frequency_list_mhz':';'.join(p[1] for p in pairs),
              'cpu_utilization_list_pct':';'.join(p[0] for p in pairs),
              'gpu_utilization_pct':int(gpu.group(1)) if gpu else None,
              'gpu_frequency_literal':gpu.group(2) if gpu else None,
              'ram_used_mb':int(ram.group(1)) if ram else None,
              'CV0_literal_C':temps.get('CV0'),'CV1_literal_C':temps.get('CV1'),'CV2_literal_C':temps.get('CV2')})
        except (KeyError,ValueError,AssertionError) as e:log_invalid.append({'line':ln,'reason':str(e),'text':line})
    log_by_time={}
    for r in logs:log_by_time.setdefault(r['timestamp'],[]).append(r)
    mismatches=[]; missing=[]; pairs_checked=0
    for r in clean:
        matches=log_by_time.get(r['timestamp'],[])
        if len(matches)!=1:missing.append({'timestamp':r['timestamp'],'log_matches':len(matches)});continue
        for key in CHANNELS:
            if matches[0][key] is None:continue
            pairs_checked+=1
            if abs(r[key]-matches[0][key])>1e-9:mismatches.append({'timestamp':r['timestamp'],'channel':key,'csv':r[key],'log':matches[0][key]})
    csvtimes={r['timestamp'] for r in clean}
    extra=[r['timestamp'] for r in logs if r['timestamp'] not in csvtimes]
    stats=[]
    for key in CHANNELS:
        vs=[r[key] for r in clean]; first=[r for r in clean if r['elapsed_s']<=300]
        last=[r for r in clean if r['elapsed_s']>=duration-300]
        stats.append({'run_id':label,'independent_runs':1,'channel':key,'n_samples':len(vs),'duration_s':duration,
          'first_timestamp':clean[0]['timestamp'],'last_timestamp':clean[-1]['timestamp'],
          'first_C':vs[0],'last_C':vs[-1],'delta_last_minus_first_C':vs[-1]-vs[0],
          'mean_C':statistics.mean(vs),'median_C':statistics.median(vs),'min_C':min(vs),'max_C':max(vs),
          'sd_within_run_C':statistics.stdev(vs),'p05_C':quantile(vs,.05),'p95_C':quantile(vs,.95),
          'time_weighted_trapezoid_mean_C':sum((a[key]+b[key])/2*d for a,b,d in zip(clean,clean[1:],diffs))/duration,
          'descriptive_linear_slope_C_per_min':slope([r['elapsed_s']/60 for r in clean],vs),
          'first_5min_n':len(first),'first_5min_mean_C':statistics.mean(r[key] for r in first),
          'last_5min_n':len(last),'last_5min_mean_C':statistics.mean(r[key] for r in last),
          'last_5min_slope_C_per_min':slope([r['elapsed_s']/60 for r in last],[r[key] for r in last]),
          'peak_first_timestamp':clean[vs.index(max(vs))]['timestamp']})
    simple=[{k:v for k,v in r.items() if k!='_time'} for r in clean]
    write_csv(out/f'{label}_temperature_source_data.csv',simple)
    write_csv(out/f'{label}_tegrastats_fields.csv',logs)
    write_csv(out/f'{label}_temperature_statistics.csv',stats)
    bins=[]
    for start in range(0,int(duration)+1,300):
        rs=[r for r in clean if start<=r['elapsed_s']<start+300]
        if rs:bins.append({'run_id':label,'bin_start_s':start,'bin_nominal_end_s':start+300,'n':len(rs),'tj_mean_C':statistics.mean(r['tj_C'] for r in rs),'tj_min_C':min(r['tj_C'] for r in rs),'tj_max_C':max(r['tj_C'] for r in rs)})
    write_csv(out/f'{label}_fixed_5min_bins.csv',bins)
    def available_range(key):
        v=[r[key] for r in logs if r[key] is not None]
        return [min(v),max(v)] if v else None
    diagnostics={
      'run_id':label,'original_csv_rows':len(raw),'valid_csv_rows':len(clean),'excluded_csv_rows':invalid,
      'raw_log_lines':len(rawlines),'parsed_log_lines':len(logs),'unparsed_log_lines':log_invalid,
      'log_format':'three-channel monitor stdout, NOT raw tegrastats' if monitor_format else 'timestamped raw tegrastats',
      'log_metadata_lines':log_metadata,
      'matched_field_comparisons':pairs_checked,'csv_log_mismatches':mismatches,'missing_or_ambiguous_log_matches':missing,'extra_log_timestamps':extra,
      'timestamp_duplicates':duplicates,'timestamp_timezone':'explicit offset preserved; +01:00 in these source files',
      'duration_s':duration,'nominal_observed_interval_s':statistics.median(diffs),
      'interval_counts_s':dict(Counter(diffs)),'interval_mean_s':statistics.mean(diffs),'interval_min_s':min(diffs),'interval_max_s':max(diffs),
      'intervals_over_1point5_times_median':sum(d>1.5*statistics.median(diffs) for d in diffs),
      'cpu_mean_utilization_pct_range':available_range('cpu_mean_utilization_pct'),
      'cpu_frequency_mhz_range':None if monitor_format else [min(r['cpu_frequency_min_mhz'] for r in logs),max(r['cpu_frequency_max_mhz'] for r in logs)],
      'gpu_frequency_literals':dict(Counter(r['gpu_frequency_literal'] for r in logs)),
      'ram_used_mb_range':available_range('ram_used_mb'),
      'CV0_CV1_CV2_literal_counts':{k:dict(Counter(r[k+'_literal_C'] for r in logs)) for k in ['CV0','CV1','CV2']},
      'thermal_throttling':'NOT VERIFIED — no thermal event/cooling-state/boot evidence; CPU DVFS is not a thermal flag',
      'source_files':[{'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':before[str(p)]} for p in [csvpath,logpath]],
      'statistics':stats,'analysis_notes':['all finite six-channel CSV rows retained; no smoothing or initial-temperature matching',('3 channels tj/CPU/GPU compared to monitor stdout; SOC0/1/2 not independently cross-checked' if monitor_format else '6 valid temperature channels compared exactly to named LOG fields'),('air raw tegrastats LOG absent; no frequency/utilization/throttling evidence' if monitor_format else 'CV channels -256 C retained literally but not interpreted; GPU frequency literal 0 does not prove normal frequency or no throttling'),'sample SD and slopes describe this run, not between-run uncertainty; no significance tests','elapsed time begins at first logged sample, not inferred workload start','environment/depth/workload are not inferred from processor logs']}
    for p in [csvpath,logpath]:assert sha(p)==before[str(p)]
    (out/f'{label}_audit.json').write_text(json.dumps(diagnostics,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return diagnostics

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--csv',type=Path,required=True);p.add_argument('--log',type=Path,required=True);p.add_argument('--run-id',required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    d=inspect_run(a.csv,a.log,a.run_id,a.out)
    print(json.dumps({k:v for k,v in d.items() if k not in ['statistics','source_files']},ensure_ascii=False,indent=2))
    print(json.dumps(d['statistics'][0],ensure_ascii=False,indent=2))
