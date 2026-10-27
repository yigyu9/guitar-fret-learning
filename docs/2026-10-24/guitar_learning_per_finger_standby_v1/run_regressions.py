"""Run existing relevant CPU modules in isolated processes; no GPU training."""
from pathlib import Path
import argparse,json,os,re,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
old=json.loads((ROOT/'docs/2026-10-23/guitar_learning_action_change_v1/cpu_tests.json').read_text())
modules=[r['module'] for r in old['modules']]
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
output=args.out.resolve();output.mkdir(parents=True,exist_ok=False)
environment=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT))
results=[]
for module in modules:
 path=output/(module.rsplit('.',1)[-1]+'.log')
 with path.open('w') as log:
  run=subprocess.run([sys.executable,'-B','-m','unittest',module,'-v'],cwd=ROOT,env=environment,stdout=log,stderr=subprocess.STDOUT)
 match=re.search(r'Ran (\d+) tests?',path.read_text())
 results.append(dict(module=module,tests=int(match[1]) if match else 0,returncode=run.returncode,log=path.name))
 if run.returncode:print('FAILED '+module,flush=True)
(output/'cpu_regressions.json').write_text(json.dumps(dict(modules=results,total_tests=sum(r['tests'] for r in results),all_passed=all(r['returncode']==0 for r in results)),indent=2)+'\n')
print(json.dumps(dict(modules=len(results),tests=sum(r['tests'] for r in results),all_passed=all(r['returncode']==0 for r in results))),flush=True)
raise SystemExit(any(r['returncode']!=0 for r in results))
