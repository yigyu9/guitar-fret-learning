"""Dry-run by default; one A/B candidate, original300+10 sequential stages."""
import argparse
import importlib.util
import os
from pathlib import Path
import time

from variants import VARIANTS, validate_settings
from run_variant import watched_sources


BASE=Path(__file__).resolve().parents[1]
DIAG=BASE.parents[1]
REUSED=DIAG/'03_short_learning/support/run_short_comparison.py'
WRAPPER=Path(__file__).resolve().with_name('run_variant.py')


def original():
    spec=importlib.util.spec_from_file_location('preserved_short_comparison',REUSED)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def jobs(output,variant):
    baseline=original()
    result=baseline.jobs(output,'incremental',7)
    for job in result:
        at=job['args'].index('-m')
        job['args']=job['args'][:at]+[str(WRAPPER),'--variant',variant]+job['args'][at+2:]
    return result


def validate(job,variant):
    baseline=original()
    checked=baseline.validate(job,'incremental',7)
    validate_settings(baseline.read(Path(job['out'])/'settings.json'),variant)
    return checked


def analyze(output,variant):
    baseline=original();baseline.analyze(output)
    rows=[]
    for step in (50,100,150,200,250,300):
        s=baseline.read(output/('evaluation_%06d'%step)/'evaluation.json')['summary']
        passed=(s['achieved_fraction']>=.8 and s['mean_clean_fraction']>=.7
                and s['mean_audible_wrong_fraction']<=.1 and s['physical_failure_fraction']<=.05)
        rows.append(dict(update=step,passed=passed,summary=s))
    pairs=[[a['update'],b['update']] for a,b in zip(rows,rows[1:]) if a['passed'] and b['passed']]
    baseline.write(output/'analysis/acceptance.json',dict(variant=variant,
        criteria=dict(achieved_fraction_min=.8,mean_clean_fraction_min=.7,
            mean_audible_wrong_fraction_max=.1,physical_failure_fraction_max=.05,consecutive_policy_evaluations=2),
        evaluations=rows,passing_pairs=pairs,passed=bool(pairs),
        scope='seed7 single fixed-guitar teacher-supported note; acceptance is not adoption or free-guitar/full-song success',
        wrist_and_any_failures='reported in each summary; no removal from128 denominator'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant',choices=VARIANTS,required=True)
    parser.add_argument('--out',type=Path)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--continue-evaluations',action='store_true')
    parser.add_argument('--analyze-only',action='store_true')
    args=parser.parse_args();baseline=original()
    output=(args.out or BASE/(args.variant+'_seed7')).resolve();plan=jobs(output,args.variant)
    if args.analyze_only:
        for job in plan:validate(job,args.variant)
        analyze(output,args.variant);return
    if not args.execute:
        import json
        print(json.dumps(dict(variant=args.variant,output=str(output),jobs=plan),indent=2));return
    os.sched_setaffinity(0,set(range(14)))
    output.mkdir(parents=True,exist_ok=args.continue_evaluations)
    (output/'logs').mkdir(exist_ok=args.continue_evaluations)
    watched=watched_sources()
    active=[p for p in (baseline.ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts]
    # Reused run_child explicitly watches its own original __file__; our sources
    # are included both in fallback pins and every child's input manifest.
    identity=dict(variant=args.variant,jobs=plan,script_path=str(REUSED),script_sha256=baseline.sha(REUSED),
        active_source_pins={str(p.resolve()):baseline.sha(p) for p in [*active,*watched]},
        teacher_sha256=baseline.sha(baseline.TEACHER),reference_sha256=baseline.sha(baseline.REFERENCE),
        scope='fresh incremental large128 H32/300 seed7 std.1711710544767014; A and B never combined')
    path=output/'comparison_plan.json'
    if path.exists():
        if baseline.read(path)!=identity:raise ValueError('Existing source/job/variant identity differs')
    else:baseline.write(path,identity)
    env=os.environ.copy();env.update(KMP_AFFINITY='disabled',OMP_PROC_BIND='false',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    env['PATH']=str(baseline.PYTHON.parent)+os.pathsep+env.get('PATH','')
    env['PYTHONPATH']=str(baseline.ROOT/'isaacgym/python')+os.pathsep+str(baseline.ROOT)
    env['LD_LIBRARY_PATH']=str(baseline.PYTHON.parent.parent/'lib')+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    completed=[];started=time.time()
    for job in plan:
        if Path(job['out']).exists():
            if not args.continue_evaluations:raise FileExistsError(job['out'])
            checked=validate(job,args.variant)
        else:
            print('START '+job['name'],flush=True)
            baseline.run_child(job,output,env,identity)
            checked=validate(job,args.variant)
        completed.append(dict(name=job['name'],verification=checked))
        print('COMPLETE '+job['name'],flush=True)
    if any(baseline.sha(path)!=value for path,value in identity['active_source_pins'].items()):
        raise ValueError('Orchestrator/wrapper/reused/active source changed')
    baseline.write(output/'comparison_completed.json',dict(completed=True,stages=completed,wall_s=time.time()-started,variant=args.variant))
    analyze(output,args.variant)


if __name__=='__main__':main()
