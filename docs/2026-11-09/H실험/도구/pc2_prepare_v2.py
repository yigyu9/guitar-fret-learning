from pathlib import Path
import json,os,sys,subprocess,shutil,datetime,hashlib,importlib.util,platform
D=Path(__file__).resolve().parents[1];R=D.parents[2];SNAP=D/'작업자료/source_snapshot';SH=Path('/home/yigyu/cgl-lab/docs/2026-11-09/H실험');PY=sys.executable
now=lambda:datetime.datetime.now().astimezone().isoformat()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2))
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',MAX_JOBS='2');env.pop('PYTHONUTF8',None);env.pop('PYTHONOPTIMIZE',None)
for n in ('guitar_learning','scripts','data','isaacgym'):
 shutil.copytree(SNAP/n,R/n,symlinks=True,dirs_exist_ok=True)
# Root mirrors are independent copies. Only the sealed nested snapshot is executed.
spec=importlib.util.spec_from_file_location('horizon_study',D/'도구/study.py');study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
check=study.check(R,D);assert check['snapshot_valid'] and check['design_valid'];write(D/'검증/다른PC_봉인검사.json',check)
cmd=study.commands(R,D);write(D/'작업자료/명령목록.json',cmd)
cpu=dict(env,CUDA_VISIBLE_DEVICES='',PYTHONPATH=str(SNAP))
with (D/'검증/다른PC_C1_CPU검사.json').open('w') as f:subprocess.run([PY,'-X','utf8','-m','guitar_learning.tool.experiments.press_sequence','check','C1'],cwd=SNAP,env=cpu,stdout=f,stderr=subprocess.PIPE,text=True,check=True)
versions=json.loads(subprocess.check_output([PY,'-X','utf8','-c','import json,torch,sys;print(json.dumps(dict(python=sys.version,torch=torch.__version__,cuda_build=torch.version.cuda)))'],env=cpu,text=True))
probe=lambda argv:subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True).stdout.strip()
info=dict(checked_at=now(),versions=versions,python_executable=PY,platform=platform.platform(),gpu=probe(['nvidia-smi','--query-gpu=name,uuid,driver_version,memory.total','--format=csv,noheader']),compute_processes=probe(['nvidia-smi','--query-compute-apps=pid,process_name,used_gpu_memory','--format=csv,noheader']),compiler=probe(['g++','--version']),ffmpeg=probe(['ffmpeg','-version']).splitlines()[0],display=os.environ.get('DISPLAY'),xvfb_run=shutil.which('xvfb-run'),display_probe=probe(['xdpyinfo','-display',os.environ.get('DISPLAY',':1')]).splitlines()[:3],local_study=str(D),shared_study=str(SH),execution_snapshot=str(SNAP),native_cache=str(SNAP/'.runtime/cache'),source_origin='prepared sealed copy; active shared code is not execution source',shell_env_overrides={k:env[k] for k in ('PYTHONDONTWRITEBYTECODE','OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','MAX_JOBS')})
assert not info['compute_processes'],'another GPU compute process present'
write(D/'검증/다른PC_환경.json',info)
for p in (D/'검증/다른PC_봉인검사.json',D/'검증/다른PC_C1_CPU검사.json',D/'검증/다른PC_환경.json',D/'작업자료/명령목록.json',D/'도구/pc2_prepare_v2.py'):
 dest=SH/p.relative_to(D);dest.parent.mkdir(parents=True,exist_ok=True)
 with p.open('rb') as a,dest.open('xb') as b:shutil.copyfileobj(a,b)
write(D/'검증/로컬경로.json',dict(local_project=str(R),local_study=str(D),execution_snapshot=str(SNAP),shared_study=str(SH),root_mirror='independent local copy for study root discovery; execution uses nested sealed snapshot'))
x=json.loads((D/'진행상황.json').read_text());x.update(phase='cpu_verified_ready_for_H128_memory',updated_at=now(),next_step='H1281024환경1업데이트메모리검사',environment='검증/다른PC_환경.json',snapshot_valid=True,design_valid=True);write(D/'진행상황.json',x);write(SH/'진행상황.json',x)
print('CPU check and source seal passed; commands prepared',flush=True)
