"""Root checks, independent memory-trend reproduction, and final preservation."""
import hashlib
import json
import re
import shutil
from pathlib import Path
import numpy as np

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[4]
RUN=OUT.parent/'guitar_learning_long_B_8env_dense_v2_20261018_130137'


def read(p):return json.loads(p.read_text())


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()


def write(name,data):
    with (OUT/name).open('x') as f:json.dump(data,f,indent=2,ensure_ascii=False,allow_nan=False)


def main():
    assert (OUT/'review.md').is_file()
    for name in ('analysis_verification.json','plot_verification.json','runtime_inputs_after.json'):
        assert read(OUT/name)['completed']
    pins={}
    for name in ('inputs_before.json','plot_inputs_before.json'):
        pins.update(read(OUT/name))
    for row in read(OUT/'runtime_inputs_before.json')['inputs']:pins[row['path']]=row['sha256']
    pins.update(read(RUN/'inputs_before.json'))
    pins[str(Path(__file__).resolve())]=sha(Path(__file__).resolve())
    pins[str(OUT/'runtime_analysis.json')]=sha(OUT/'runtime_analysis.json')
    write('final_inputs_before.json',pins)
    changed=[p for p,h in pins.items() if not Path(p).is_file() or sha(Path(p))!=h]
    assert not changed,changed
    runtime=read(OUT/'runtime_analysis.json');samples=[]
    for line in (RUN/'resources.jsonl').read_text().splitlines():
        r=json.loads(line);w=r.get('workers',[]);parent=r['parent_memory']
        if len(w)==8 and all(v['memory']['rss_current_bytes'] is not None and v['memory']['pss_current_bytes'] is not None for v in w) and all(parent[k] is not None for k in ('rss_current_bytes','pss_current_bytes')):
            rss=sum(v['memory']['rss_current_bytes'] for v in w);pss=sum(v['memory']['pss_current_bytes'] for v in w)
            samples.append(dict(elapsed_s=r['elapsed_s'],worker_rss_bytes=rss,worker_pss_bytes=pss,
                total_rss_bytes=rss+parent['rss_current_bytes'],total_pss_bytes=pss+parent['pss_current_bytes']))
    reproduced={}
    for start in (60,1800,2700):
        rows=[r for r in samples if r['elapsed_s']>=start];x=np.array([r['elapsed_s']/3600 for r in rows])
        reproduced[str(start)]={}
        for field in ('worker_rss_bytes','worker_pss_bytes','total_rss_bytes','total_pss_bytes'):
            y=np.array([r[field]/2**30 for r in rows]);slope,intercept=np.polyfit(x,y,1)
            r2=1-float(np.sum((y-(slope*x+intercept))**2)/np.sum((y-y.mean())**2))
            expected=runtime['memory']['ols_trends'][str(start)][field]
            assert abs(slope-expected['slope_GiB_per_hour'])<1e-8
            assert abs(r2-expected['r_squared'])<1e-8 and len(rows)==expected['samples']
            assert int(np.sum(np.diff(y)<0))==expected['decreases']
            reproduced[str(start)][field]=dict(slope_GiB_per_hour=float(slope),r_squared=r2,samples=len(rows))
    write('runtime_reproduction.json',dict(completed=True,source='raw resources.jsonl; original runtime outputs untouched',trends=reproduced))
    manifest=read(OUT/'main_before/manifest.json')
    assert all(sha(Path(r['snapshot_path']))==r['sha256'] for r in manifest)
    doc=OUT/'README.md';broken=[]
    for target in re.findall(r'\]\((/[^)]+)\)',doc.read_text()):
        if not Path(target.split('#')[0]).exists():broken.append(target)
    assert not broken,broken
    snapshot=OUT/'source_final';snapshot.mkdir();rows=[]
    sources=[OUT/'analyze.py',OUT/'plot.py',Path(__file__).resolve(),doc,OUT/'runtime_notes.md',
        ROOT/'docs/plans/guitar_learning_long_B_8env_analysis_20261018.md',
        ROOT/'stability_adapter_2/PLAN.md',ROOT/'stability_adapter_2/README.md']
    for p in sources:
        t=snapshot/p.relative_to(ROOT);t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,t)
        rows.append(dict(original_path=str(p),snapshot_path=str(t),sha256=sha(p)))
    with (snapshot/'manifest.json').open('x') as f:json.dump(rows,f,indent=2)
    changed=[p for p,h in pins.items() if sha(Path(p))!=h];assert not changed
    inventory={str(p):dict(sha256=sha(p),bytes=p.stat().st_size) for p in OUT.rglob('*') if p.is_file()}
    write('artifact_inventory.json',inventory)
    report=read(RUN/'report.json')
    write('final_verification.json',dict(analysis_completed=True,original_run_completed=report['completed'],
        original_run_stopped=report['stopped'],input_count=len(pins),changed_inputs=changed,
        broken_links=broken,source_final_files=len(rows),artifact_count=len(inventory),
        runtime_trend_reproduction=True,review_sha256=sha(OUT/'review.md'),
        scope='Declared analysis/runtime/plot inputs and original run input map. No native or new policy evaluation; original final physical audit remains unavailable. Inventory excludes itself and this verification.'))


if __name__=='__main__':main()
