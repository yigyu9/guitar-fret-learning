"""Two serial native thumb conditions; dry plan unless --execute is supplied."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


BASE=Path(__file__).resolve().parents[1]
ROOT=BASE.parents[5]
PYTHON='/home/ajou/miniconda3/envs/rl38/bin/python'


def jobs(out):
    return [dict(condition=c,out=str(out/c),args=['taskset','-c','0-13',PYTHON,
        str(Path(__file__).resolve().with_name('run_probe.py')),'--surface',c,'--out',str(out/c),'--video'])
        for c in ('current_all_vertices','face_only_playing_neck1')]


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--execute',action='store_true');args=parser.parse_args();out=args.out.resolve();plan=jobs(out)
    if not args.execute:
        print(json.dumps(dict(jobs=plan,GPU_executed=False),indent=2));return
    out.mkdir(parents=True,exist_ok=False)
    from surfaces import validate_freeze
    pins=validate_freeze()
    (out/'plan.json').write_text(json.dumps(dict(jobs=plan,source_pins=pins),indent=2)+'\n')
    env=os.environ.copy();env.update(KMP_AFFINITY='disabled',OMP_PROC_BIND='false',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    env['PATH']=str(Path(PYTHON).parent)+os.pathsep+env.get('PATH','')
    env['PYTHONPATH']=str(ROOT/'isaacgym/python')+os.pathsep+str(ROOT)
    env['LD_LIBRARY_PATH']=str(Path(PYTHON).parent.parent/'lib')+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    reports=[]
    for job in plan:
        with (out/(job['condition']+'.log')).open('x') as stream:
            child=subprocess.Popen(job['args'],cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
            try:
                while True:
                    try:code=child.wait(timeout=30);break
                    except subprocess.TimeoutExpired:
                        if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h for p,h in pins.items()):
                            raise RuntimeError('Comparison input source changed')
            except BaseException:
                child.terminate()
                try:child.wait(timeout=30)
                except subprocess.TimeoutExpired:child.kill();child.wait()
                raise
        report=json.loads((Path(job['out'])/'report.json').read_text());reports.append(report)
        if code or not report['completed'] or not report['scene_closed']:raise RuntimeError('Native child incomplete')
    a,b=reports
    for key in ('asset_sha256','requested_fix_base_link','requested_disable_gravity','shape_readback_sha256'):
        if a['scene']['diagnostic_guitar_asset'][key]!=b['scene']['diagnostic_guitar_asset'][key]:
            raise RuntimeError('A/B physical asset/options differ')
    if a['native_PD_sha256']!=b['native_PD_sha256']:raise RuntimeError('A/B native PD differs')
    if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h for p,h in pins.items()):raise RuntimeError('Comparison source seal failed')
    (out/'comparison.json').write_text(json.dumps(dict(completed=True,conditions=reports,
        scope='diagnostic source-surface A/B, identical fixed physical asset; no learning performance claim'),indent=2)+'\n')


if __name__=='__main__':main()
