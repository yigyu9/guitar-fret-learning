"""Supervise the unchanged learner and archive each completed native evaluation."""
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
import shutil,subprocess,sys,tempfile
R=Path('/home/ajou/yigyu/3');G=Path(__file__).resolve().parent
OUT=G/'long_on_v1';ARCHIVE=R/'docs/2026-10-12/video/graphics_long_v1'
CP=G/'smoke_on_v1/checkpoints/update_000242.pt'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,value):
    fd,temporary=tempfile.mkstemp(prefix='.'+p.name+'.',dir=p.parent)
    try:
        with os.fdopen(fd,'w') as f:
            json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
        os.link(temporary,p)
    finally:os.unlink(temporary)

def archive_complete():
    records=OUT/'evaluation_records'
    if not records.exists():return
    for path in sorted(records.glob('record_*.json')):
        record=json.loads(path.read_text())
        base=Path(record['output']);native=base/'native/episode_0001/report.json'
        if not native.exists():continue
        report=json.loads(native.read_text())
        if not all(name in report.get('videos',{}) for name in ('whole_body','hands')):continue
        target=ARCHIVE/record['label'];target.mkdir(parents=True,exist_ok=True)
        if (target/'manifest.json').exists():
            existing=json.loads((target/'manifest.json').read_text())
            if existing['native_report_sha256']!=sha(native):raise AssertionError('archived report changed')
            for value in existing['videos'].values():
                if sha(value['archive'])!=value['sha256'] or sha(value['source'])!=value['sha256']:
                    raise AssertionError('existing archived video changed')
            continue
        videos={}
        for name in ('whole_body','hands'):
            source=Path(report['videos'][name]['path']);expected=report['videos'][name]['sha256']
            if sha(source)!=expected:raise AssertionError('source native video differs from report')
            destination=target/(name+'.mp4')
            if destination.exists():
                if sha(destination)!=expected:raise AssertionError('archive differs; original left untouched')
            else:
                with destination.open('xb') as stream,source.open('rb') as original:shutil.copyfileobj(original,stream)
            if sha(destination)!=expected or sha(source)!=expected:raise AssertionError('copy verification failed')
            videos[name]={'source':str(source),'archive':str(destination),'sha256':expected}
        status='정상 완주' if report['full_horizon_completed'] else '부분 종료: '+report['stop_reason']
        text='# 체크포인트 영상\n\n'+f"{record['label']}: 실제 Isaac Gym, 스트랩 표시, 환경 시작부터 {report['physics_seconds']:.6f}초까지({status}). 연주 성공 {report['joint_success_events']}/{report['settled_events']}이며, 완주는 성공 판정이 아닙니다.\n\n"
        for name,value in videos.items():text+=f"![{name}]({value['archive']})\n\n"
        readme=target/'README.md'
        if readme.exists():
            if readme.read_text()!=text:raise AssertionError('partial or changed archive README; preserved for diagnosis')
        else:
            with readme.open('x') as f:f.write(text)
        save(target/'manifest.json',{'created_utc':datetime.now(timezone.utc).isoformat(),'native_report':str(native),
            'native_report_sha256':sha(native),'evaluation_record':str(path),'videos':videos,'full_horizon_completed':report['full_horizon_completed'],'stop_reason':report['stop_reason'],
            'scope':'saved native videos with explicit completion status; immutable per-evaluation archive'})

verified=json.loads((G/'verification_v1.json').read_text());assert verified['passed']
assert all(sha(p)==h for p,h in verified['input_sha256'].items())
command=[sys.executable,'-u','-m','stability_adapter_2.run_deadline_training_v9','--out',str(OUT),
    '--checkpoint',str(CP),'--strap','on','--device','cuda','--interval-minutes','30','--stop-at','2026-10-12T11:40:00+09:00']
record={'started_utc':datetime.now(timezone.utc).isoformat(),'command':command,'launcher_sha256':sha(__file__),
    'supervisor_pid':os.getpid(),'source_checkpoint_sha256':sha(CP),'archive':str(ARCHIVE),'archive_errors':[]}
with OUT.with_suffix('.log').open('x') as log:
    proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
    record['pid']=proc.pid;save(OUT.with_suffix('.launch.json'),record)
    while True:
        try:archive_complete()
        except Exception as error:
            record['archive_errors'].append({'utc':datetime.now(timezone.utc).isoformat(),'type':type(error).__name__,'message':str(error)})
        try:record['returncode']=proc.wait(timeout=20);break
        except subprocess.TimeoutExpired:pass
    try:archive_complete()
    except Exception as error:record['archive_errors'].append({'type':type(error).__name__,'message':str(error)})
record['finished_utc']=datetime.now(timezone.utc).isoformat()
save(OUT.with_suffix('.exit.json'),record)
