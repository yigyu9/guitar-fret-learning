"""18조합을 순환 학습하고 검증된 저장본으로 재개하는 독립 감독기.

학습기 내부 계약 검증은 runtime이 소유한다. 여기서는 시도·예산·오류 격리를
관리하며 완료하지 않은 작업을 덮어쓰거나 성공으로 취급하지 않는다.
"""
import argparse
import csv
from datetime import datetime, timezone, timedelta
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import signal
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parents[1]
ROOT = next(p for p in BASE.parents if (p/'guitar_learning/train.py').is_file())
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'
KST = timezone(timedelta(hours=9))


def now():
    return datetime.now(KST).isoformat(timespec='seconds')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name+'.tmp')
    with temp.open('w') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
    os.replace(str(temp), str(path))


def passed(metrics, count):
    return (metrics['episodes'] == count and metrics['achievement'] >= (15 if count == 16 else 31)
        and metrics['clean_fraction'] >= .9 and metrics['physical'] == 0
        and metrics['wrist'] == 0 and metrics['wrong_s'] <= .05)


def rank(metrics):
    return (metrics['achievement']/metrics['episodes'], metrics['clean_fraction'],
        -metrics['wrong_s'], -metrics['physical']-metrics['wrist'])


def terminate(child):
    # 대표가 먼저 끝나도 그 세션의 자식이 남아 있으면 같이 정리한다.
    try:os.killpg(child.pid,signal.SIGTERM)
    except ProcessLookupError:return
    try:child.wait(timeout=20)
    except subprocess.TimeoutExpired:pass
    try:os.killpg(child.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    try:child.wait(timeout=10)
    except subprocess.TimeoutExpired:pass


class Study:
    def __init__(self, out, hours=8):
        self.out = Path(out).resolve()
        self.path = self.out/'state.json'
        if self.path.exists():
            self.state = json.loads(self.path.read_text())
            if self.state['status'] in ('complete','budget_complete'):
                raise ValueError('완료 연구 자동 재실행 금지')
            self.check_seal()
            self.state['restarts'].append(dict(at=now(), pid=os.getpid()))
        else:
            cases = json.loads((BASE/'설계/cases.json').read_text())['cases']
            random.Random(7).shuffle(cases)
            baseline=['index_s1_f1','middle_s1_f1','ring_s3_f1','pinky_s3_f1']
            cases.sort(key=lambda c:baseline.index(c['case_id']) if c['case_id'] in baseline else 4)
            start = time.time()
            pins = {str(p):sha(p) for p in sorted((BASE/'도구').glob('*.py'))}
            pins[str(BASE/'설계/cases.json')] = sha(BASE/'설계/cases.json')
            sys.path.insert(0,str(ROOT))
            from guitar_learning.training.training_log_io import active_source_paths
            for path in active_source_paths(ROOT/'guitar_learning'):
                pins[str(path)]=sha(path)
            for proof in sorted((BASE/'입력').glob('*/*/provenance.json')):
                pins[str(proof)]=sha(proof)
                catalog=proof.parent/'catalog.json';pins[str(catalog)]=sha(catalog)
                for name,expected in json.loads(proof.read_text())['active_physical_inputs'].items():
                    path=Path(name) if Path(name).is_absolute() else ROOT/name
                    if sha(path)!=expected:raise RuntimeError('GLOBAL_IDENTITY: 시작 전 입력 변경 '+name)
                    pins[str(path)]=expected
            self.state = dict(schema='single18_supervisor.v1',status='running',started_at=now(),
                started_epoch=start, deadline_epoch=start+hours*3600,
                training_end_epoch=start+max(0,hours-1)*3600,
                retry_end_epoch=start+max(0,hours-2)*3600,
                initial_end_epoch=start+min(1,hours/4)*3600,
                deadline=datetime.fromtimestamp(start+hours*3600,KST).isoformat(timespec='seconds'),
                driver_pid=os.getpid(), source_seal=pins, jobs={}, restarts=[],
                cases={c['case_id']:dict(c,status='pending',updates=0,history=[],candidate_updates=[]) for c in cases})
        self.state['driver_pid']=os.getpid()
        self.child=None
        self.save()

    def check_seal(self):
        bad=[p for p,h in self.state['source_seal'].items() if not Path(p).is_file() or sha(p)!=h]
        if bad: raise RuntimeError('GLOBAL_IDENTITY: 실행 소스 변경 '+str(bad))

    def save(self):
        self.state['heartbeat']=now()
        active=self.state.get('current_job')
        self.state['current_partial_updates']=0
        if active and self.state['jobs'].get(active):
            metrics=Path(self.state['jobs'][active][-1]['out'])/'J/learning_metrics.jsonl'
            if metrics.exists():self.state['current_partial_updates']=len(metrics.read_text().splitlines())
        write(self.path,self.state)
        lines=['# 단일 압현 진행상황','',
            '- 상태: '+self.state['status'], '- 시작: '+self.state['started_at'],
            '- 종료 예정: '+self.state['deadline'], '- 갱신: '+self.state['heartbeat'],
            '- 현재 작업: '+str(self.state.get('current_job','없음')),
            '- 현재 블록 완료 회수: '+str(self.state['current_partial_updates']),'',
            '|조합|상태|학습 회수|달성/평가|clean 비율|영상|', '|---|---|---:|---|---:|---|']
        for case in self.state['cases'].values():
            best=case.get('best',{}).get('metrics',{})
            lines.append('|{}|{}|{}|{}|{}|{}|'.format(case['case_id'],case['status'],case['updates'],
                str(best.get('achievement','-'))+'/'+str(best.get('episodes','-')),
                '{:.1%}'.format(best['clean_fraction']) if best else '-',case.get('video','-')))
        if self.state.get('error'):lines+=['','오류: '+self.state['error']]
        (BASE/'진행상황.md').write_text('\n'.join(lines)+'\n')
        write(BASE/'분석/results.json',list(self.state['cases'].values()))

    def command(self, operation, case, args):
        if operation in ('prepare','calibrate'):
            script='prepare_targets.py' if operation=='prepare' else 'calibrate_hold.py'
            return [PYTHON,'-B',str(BASE/'도구'/script),'--case',case['case_id'],*map(str,args)]
        script=BASE/'도구'/('render_initial.py' if operation=='render_initial' else 'runtime.py')
        operations=[] if operation=='render_initial' else [operation]
        cmd=[PYTHON,'-B',str(ROOT/'scripts/tab2body.py'),'--cache-root',str(ROOT/'.runtime/cache'),
            'run',str(script),*operations,'--case',case['case_id'],*map(str,args)]
        if operation.startswith('render'):
            cmd=['xvfb-run','-a','--server-args=-screen 0 1280x720x24',*cmd]
        return cmd

    def job(self, label, operation, case, args, timeout=900):
        self.check_seal()
        # 같은 label은 완료된 결과만 재사용한다. 불완전 시도는 새 번호로 보존한다.
        prior=self.state['jobs'].get(label,[])
        for record in prior:
            if record['status']=='complete':
                if all(Path(p).is_file() and sha(p)==h for p,h in record['evidence'].items()):
                    return Path(record['out'])
                raise RuntimeError('GLOBAL_IDENTITY: 완료 작업 결과 변경 '+label)
        if time.time()+30>=self.state['deadline_epoch']:raise TimeoutError('연구 시간 예산 종료')
        if shutil.disk_usage(ROOT).free<12*1024**3:raise RuntimeError('GLOBAL_STORAGE: 여유 공간12GiB 미만')
        jobroot=BASE/'모델'/self.out.name if operation=='train' else self.out/'jobs'
        folder=jobroot/label/('attempt%02d'%(len(prior)+1))
        folder.parent.mkdir(parents=True,exist_ok=True)
        cmd=self.command(operation,case,[*args,'--out',folder])
        record=dict(status='running',out=str(folder),command=cmd,started_at=now(),operation=operation)
        self.state['jobs'].setdefault(label,[]).append(record)
        self.state['current_job']=label
        logfile=self.out/'stdout'/(label+'_a%d.log'%(len(prior)+1));logfile.parent.mkdir(exist_ok=True)
        env=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',
            MPLCONFIGDIR=str(ROOT/'.runtime/cache/matplotlib'),VK_ICD_FILENAMES='/usr/share/vulkan/icd.d/nvidia_icd.json')
        if operation not in ('prepare','calibrate'):
            for wait in range(6):
                occupied=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
                if not occupied:break
                time.sleep(5)
            if occupied:raise RuntimeError('GLOBAL_GPU_BUSY: 다른 GPU 프로세스 '+occupied)
        start=time.monotonic()
        last_progress=start;signature=None
        try:
            with logfile.open('x') as stream:
                self.child=subprocess.Popen(cmd,cwd=str(ROOT),env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                record['pid']=self.child.pid
                record['proc_start_ticks']=Path('/proc/%d/stat'%self.child.pid).read_text().rsplit(')',1)[1].split()[19]
                self.save()
                while self.child.poll() is None:
                    self.save()
                    progress_files=[logfile]+list(folder.glob('J/*metrics*.jsonl'))
                    current=tuple((str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in progress_files if p.exists())
                    if current!=signature:signature=current;last_progress=time.monotonic()
                    if time.monotonic()-last_progress>300:raise TimeoutError(label+' 5분간 진행 없음')
                    if time.monotonic()-start>timeout or time.time()>self.state['deadline_epoch']:
                        raise TimeoutError(label+' 작업 시간 상한')
                    time.sleep(10)
                code=self.child.returncode
            self.check_seal()
            if code:
                tail=logfile.read_text(errors='replace')[-2000:]
                if any(word in tail for word in ('SHA 불일치','identity 불일치','원본 체크포인트 변경','실행 소스 변경','input pin','changed_inputs')):
                    raise RuntimeError('GLOBAL_IDENTITY: '+tail)
                raise RuntimeError('작업 종료코드%d: '%code+tail)
            reportpath=folder/('catalog.json' if operation=='prepare' else 'report.json')
            if not reportpath.exists():raise RuntimeError('완료 보고서 누락')
            report=json.loads(reportpath.read_text())
            if operation=='prepare':report=dict(completed=True)
            if report.get('completed') is not True or any(report.get(k) for k in ('failure','changed_inputs','cleanup_errors','missing_import_pins')):
                raise RuntimeError('작업 완료/정리 검증 실패 '+str(report.get('failure')))
            if operation=='probe' and report.get('native_verified') is not True:
                raise RuntimeError('native 초기화 조건 미통과')
            if operation=='train':
                phase=json.loads((folder/'J/report.json').read_text())
                requested=int(args[args.index('--updates')+1])
                if phase.get('updates_in_run')!=requested or phase.get('lifecycle_verified') is not True:
                    raise RuntimeError('학습 블록 반복 수 또는 자원 정리 불일치')
            evidence={str(reportpath):sha(reportpath)}
            for p in (folder/'metrics.json',folder/'J/final.pt',folder/'hand.mp4',folder/'fullbody.mp4',folder/'episode_env0000.json'):
                if p.exists():evidence[str(p)]=sha(p)
            record.update(status='complete',finished_at=now(),wall_s=time.monotonic()-start,evidence=evidence)
            return folder
        except BaseException as error:
            record.update(status='failed',error=repr(error),finished_at=now())
            raise
        finally:
            if self.child is not None:terminate(self.child)
            self.child=None;self.state['current_job']=None;self.save()

    def retry_job(self,label,operation,case,args,timeout=900):
        args=list(args)
        target=(case['updates']+int(args[args.index('--updates')+1])) if operation=='train' else None
        for attempt in range(3):
            if operation=='train':
                candidates=[]
                for record in self.state['jobs'].get(label,[]):
                    manifest=Path(record['out'])/'J/checkpoint_manifest.jsonl'
                    if not manifest.exists():continue
                    for line in manifest.read_text().splitlines():
                        try:row=json.loads(line)
                        except json.JSONDecodeError:continue
                        path=manifest.parent/row['path']
                        update=row.get('optimizer_updates')
                        if row.get('kind')=='periodic' and isinstance(update,int) and case['updates']<update<target and path.is_file() and sha(path)==row['sha256']:
                            candidates.append((update,str(path)))
                if candidates:
                    update,path=max(candidates)
                    if '--resume' in args:
                        args[args.index('--resume')+1]=path
                    else:args+=['--resume',path]
                    args[args.index('--updates')+1]=target-update
                    case['recovery']=dict(checkpoint=path,updates=update,at=now());self.save()
            try:return self.job(label,operation,case,args,timeout)
            except (RuntimeError,TimeoutError) as error:
                if 'GLOBAL_' in str(error) or time.time()>=self.state['deadline_epoch']:raise
                case.setdefault('errors',[]).append(dict(at=now(),operation=operation,error=str(error)))
                self.save()
                if operation=='probe':
                    records=self.state['jobs'].get(label,[])
                    path=Path(records[-1]['out'])/'report.json' if records else None
                    if path is not None and path.exists():
                        result=json.loads(path.read_text())
                        if result.get('completed') is True and result.get('native_verified') is False:raise
                if attempt==2:raise

    def verify_candidate(self,case,label,target):
        current=target
        errors=[]
        for correction in range(3):
            if time.time()+120>=self.state.get('initial_end_epoch',self.state['started_epoch']+3600):break
            joblabel=label+'_c%d'%correction
            try:
                return self.retry_job(joblabel,'probe',case,
                    ['--catalog',current/'catalog.json','--provenance',current/'provenance.json'],timeout=300)
            except (RuntimeError,TimeoutError) as error:
                if 'GLOBAL_' in str(error):raise
                errors.append(str(error))
                if correction==2:break
                records=self.state['jobs'].get(joblabel,[])
                if not records:break
                failed=Path(records[-1]['out'])
                # 보정기는 완전한 무접촉·무종료 probe에만 유지 목표를 보정한다.
                # 충돌·불완전 실행이면 여기서 거부하고 다음 원래 후보를 검사한다.
                try:
                    current=self.job(label+'_calibrate%d'%(correction+1),'calibrate',case,
                        ['--catalog',current/'catalog.json','--provenance',current/'provenance.json','--probe',failed],timeout=60)
                except (RuntimeError,TimeoutError) as error:
                    if 'GLOBAL_' in str(error):raise
                    errors.append(str(error));break
        raise RuntimeError('native 초기화 미확보: '+' / '.join(errors))

    def prepare(self,case):
        if case.get('catalog'):return
        candidates=[BASE/'입력/전체기타후보'/case['case_id'],BASE/'입력/보정후보'/case['case_id'],BASE/'입력/후보'/case['case_id'],BASE/'입력/전체손후보'/case['case_id']]
        errors=[]
        for variant,target in enumerate(candidates):
            if time.time()+180>=self.state.get('initial_end_epoch',self.state['started_epoch']+3600):break
            if not (target/'catalog.json').exists():continue
            candidate=json.loads((target/'catalog.json').read_text())
            if not candidate['goals'][0].get('candidate_valid'):continue
            provenance=json.loads((target/'provenance.json').read_text())
            if sha(target/'catalog.json')!=provenance['catalog_sha256']:
                raise RuntimeError('GLOBAL_IDENTITY: 후보 catalog 변경')
            for name,expected in provenance['active_physical_inputs'].items():
                path=Path(name) if Path(name).is_absolute() else ROOT/name
                if sha(path)!=expected:raise RuntimeError('GLOBAL_IDENTITY: 후보 source 변경 '+name)
            try:
                probe=self.verify_candidate(case,case['case_id']+'_probe_v%d'%variant,target)
                case.update(catalog=str(probe/'verified/catalog.json'),provenance=str(probe/'verified/provenance.json'),
                    status='ready',initial_variant=variant,initial_candidate=str(target))
                for evidence in (probe/'verified/catalog.json',probe/'verified/provenance.json',probe/'report.json'):
                    self.state['source_seal'][str(evidence)]=sha(evidence)
                actualproof=json.loads((probe/'verified/provenance.json').read_text())
                for name,expected in actualproof['active_physical_inputs'].items():
                    path=Path(name) if Path(name).is_absolute() else ROOT/name
                    self.state['source_seal'][str(path)]=expected
                self.save();return
            except (RuntimeError,TimeoutError) as error:
                if 'GLOBAL_' in str(error):raise
                errors.append(str(error))
        raise RuntimeError('초기 후보 미확보: '+' / '.join(errors))

    def common_args(self,case):
        return ['--catalog',case['catalog'],'--provenance',case['provenance']]

    def assess(self,case,checkpoint,count,label):
        folder=self.retry_job(label,'evaluate',case,[*self.common_args(case),
            '--checkpoint',checkpoint,'--episodes',count,'--num-envs',count],timeout=300)
        metrics=json.loads((folder/'metrics.json').read_text())
        if metrics['episodes']!=count:raise ValueError('평가 분모 불일치')
        return metrics,folder

    def train_block(self,case,target):
        if case['status']=='passed' or target in case.get('completed_boundaries',[]):return
        label=case.get('run_id',case['case_id'])
        if case['updates']<target:
            args=self.common_args(case)+['--updates',target-case['updates'],'--num-envs',64,'--seed',case.get('seed',7)]
            if case.get('checkpoint'):args+=['--resume',case['checkpoint']]
            folder=self.retry_job(label+'_u%d'%target,'train',case,args,timeout=900)
            checkpoint=str(folder/'J/final.pt')
            case.update(checkpoint=checkpoint,updates=target,status='trained');self.save()
        else:
            checkpoint=case['checkpoint']
        metrics,evalfolder=self.assess(case,checkpoint,16,label+'_u%d_eval16'%target)
        record=dict(updates=target,checkpoint=checkpoint,metrics=metrics,evaluation=str(evalfolder))
        case['history']=[r for r in case['history'] if r['updates']!=target]+[record]
        if not case.get('best') or rank(metrics)>rank(case['best']['metrics']):case['best']=record
        if passed(metrics,16):
            earlier=[u for u in case['candidate_updates'] if u<target]
            previous=max(earlier) if earlier else None
            if target not in case['candidate_updates']:case['candidate_updates'].append(target)
            if previous==target-25 or target==100:
                confirm,path=self.assess(case,checkpoint,32,label+'_u%d_confirm32'%target)
                case['confirmation']=dict(metrics=confirm,evaluation=str(path),checkpoint=checkpoint)
                if passed(confirm,32):case.update(status='passed',selected_checkpoint=checkpoint)
        if target==100 and case['status']!='passed':
            best=case.get('best')
            if best and passed(best['metrics'],16) and best['updates']!=100:
                confirm,path=self.assess(case,best['checkpoint'],32,label+'_best_confirm32')
                case['confirmation']=dict(metrics=confirm,evaluation=str(path),checkpoint=best['checkpoint'])
                if passed(confirm,32):case.update(status='passed',selected_checkpoint=best['checkpoint'])
            if case['status']!='passed':case['status']='budget_unresolved'
        case.setdefault('completed_boundaries',[]).append(target)
        self.save()

    def render(self,case):
        if case.get('video'):return
        checkpoint=case.get('selected_checkpoint') or case.get('best',{}).get('checkpoint') or case.get('checkpoint')
        diagnostic=not bool(checkpoint)
        if diagnostic:
            initial=BASE/'입력/보정후보'/case['case_id']
            render_case=dict(case,catalog=str(initial/'catalog.json'),provenance=str(initial/'provenance.json'))
            source=initial/'catalog.json'
            folder=self.retry_job(case['case_id']+'_initial_video','render_initial',render_case,
                [*self.common_args(render_case),'--num-envs',4],timeout=300)
        else:
            source=checkpoint
            folder=self.retry_job(case['case_id']+'_render','render',case,[*self.common_args(case),
                '--checkpoint',checkpoint,'--num-envs',4],timeout=300)
        video=BASE/'video'/(case['case_id']+'.mp4')
        temp=video.with_name(video.stem+'.tmp.mp4')
        publication=BASE/'분석'/(case['case_id']+'_video.json')
        if video.exists():
            if not publication.exists():raise ValueError('기존 영상의 게시 근거 없음: '+str(video))
            saved=json.loads(publication.read_text())
            if sha(video)!=saved['video_sha256'] or sha(source)!=saved['source_sha256']:
                raise RuntimeError('GLOBAL_IDENTITY: 게시 영상 또는 모델 변경')
            subprocess.run(['ffprobe','-v','error',str(video)],check=True,timeout=30)
            case.update(saved['case_publication']);self.save();return
        episode=json.loads((folder/'episode_env0000.json').read_text())
        episode_ok=bool(episode['left_note_ledger']['values']['left'][0])
        caption=case['case_id']+(' | INITIAL DIAGNOSTIC - NOT TRAINED' if diagnostic else ' | wrist support | env0 achieved='+str(episode_ok))
        cmd=['ffmpeg','-y','-loglevel','error','-i',str(folder/'hand.mp4'),'-i',str(folder/'fullbody.mp4'),
             '-filter_complex','[0:v]scale=640:480:force_original_aspect_ratio=decrease,pad=640:480:(ow-iw)/2:(oh-ih)/2[a];[1:v]scale=640:480:force_original_aspect_ratio=decrease,pad=640:480:(ow-iw)/2:(oh-ih)/2[b];[a][b]hstack=inputs=2,drawtext=text="'+caption+'":fontcolor=white:fontsize=20:box=1:boxcolor=black@0.7:x=10:y=10[v]',
             '-map','[v]','-an','-c:v','libx264','-crf','21',str(temp)]
        subprocess.run(cmd,check=True,timeout=120)
        published=dict(video=str(video),video_status='rendered',video_sha256=sha(temp),
            video_episode_success=None if diagnostic else episode['left_note_ledger']['values']['left'],
            video_observed_ledger_left=episode['left_note_ledger']['values']['left'],video_checkpoint=checkpoint,video_raw=str(folder),video_kind='initial_diagnostic' if diagnostic else 'learned_policy')
        write(publication,dict(video_sha256=sha(temp),source_sha256=sha(source),case_publication=published))
        os.replace(str(temp),str(video))
        case.update(published)
        self.save()

    def run(self):
        self.state['status']='running';self.save()
        cases=list(self.state['cases'].values())
        # 초기 준비에 실패한 경우 나머지 조합까지 함께 끝내지 않는다.
        for case in cases:
            if time.time()>=self.state.get('initial_end_epoch',self.state['started_epoch']+3600):
                for remaining in cases:
                    if remaining['status']=='pending':remaining['status']='initial_not_run'
                self.save();break
            if case.get('catalog'):continue
            try:self.prepare(case)
            except (RuntimeError,TimeoutError,ValueError) as error:
                if 'GLOBAL_' in str(error):raise
                case.update(status='initial_unresolved',error=str(error));self.save()
        for target in (25,50,75,100):
            for case in cases:
                if time.time()+300>=self.state['training_end_epoch']:break
                if not case.get('catalog') or case['status'] in ('passed','blocked'):continue
                try:self.train_block(case,target)
                except (RuntimeError,TimeoutError,ValueError) as error:
                    if 'GLOBAL_' in str(error):raise
                    case.update(status='blocked',error=str(error));self.save()
        for case in cases:
            if case.get('catalog') and case['status'] not in ('passed','blocked','budget_unresolved') and case['updates']<100:
                case['status']='budget_partial'
        self.save()
        # 남는 시간에는 손가락별 대표 하나를 새seed로 확인하며 기존 결과를 덮어쓰지 않는다.
        repeats=[]
        for finger in ('index','middle','ring','pinky'):
            eligible=[c for c in cases if c['finger']==finger and c.get('best')]
            if not eligible:continue
            chosen=max(eligible,key=lambda c:rank(c['best']['metrics']))
            if not chosen.get('replicates'):
                repeat={k:chosen[k] for k in ('case_id','finger','catalog','provenance')}
                repeat.update(run_id=chosen['case_id']+'_seed17',seed=17,updates=0,status='ready',history=[],candidate_updates=[])
                chosen['replicates']=[repeat];self.save()
            repeats+=chosen['replicates']
        for target in (25,50,75,100):
            for case in repeats:
                if time.time()+300>=self.state['training_end_epoch']:break
                if case['status'] in ('passed','blocked'):continue
                try:self.train_block(case,target)
                except (RuntimeError,TimeoutError,ValueError) as error:
                    if 'GLOBAL_' in str(error):raise
                    case.update(status='blocked',error=str(error));self.save()
        for case in cases:
            if time.time()+180>=self.state['deadline_epoch']:break
            try:self.render(case)
            except (RuntimeError,TimeoutError,ValueError,subprocess.SubprocessError) as error:
                if 'GLOBAL_' in str(error):raise
                case.update(video_status='render_failed',video_error=str(error));self.save()
        self.state.update(status='complete' if all(c.get('video') for c in cases) else 'budget_complete',finished_at=now())
        self.save()
        report=['# 18조합 결과','',f"시작 {self.state['started_at']} / 종료 {self.state['finished_at']}",'',
            '손목지원·목표손가락4축 독립 학습이다. 미실행/실패를 전체18조합 분모에서 제외하지 않는다.','',
            '|조합|상태|학습 회수|선택 평가 달성|clean|오압현 초|영상 성패|',
            '|---|---|---:|---|---:|---:|---|']
        table=[]
        for case in cases:
            result=case.get('confirmation') or case.get('best') or {}
            metrics=result.get('metrics',{})
            row=dict(case_id=case['case_id'],status=case['status'],updates=case['updates'],
                episodes=metrics.get('episodes'),achievement=metrics.get('achievement'),
                clean_fraction=metrics.get('clean_fraction'),wrong_s=metrics.get('wrong_s'),
                physical=metrics.get('physical'),wrist=metrics.get('wrist'),video=case.get('video'),
                video_episode_success=case.get('video_episode_success'))
            table.append(row)
            report.append('|{}|{}|{}|{}/{}|{}|{}|{}|'.format(row['case_id'],row['status'],row['updates'],
                row['achievement'],row['episodes'],row['clean_fraction'],row['wrong_s'],row['video_episode_success']))
        report+=['','## 분석','']
        passed_count=sum(c['status']=='passed' for c in cases)
        initial_count=sum(not c.get('catalog') for c in cases)
        report += [f'- 빠른 선별 통과: {passed_count}/18.',f'- 초기 상태 미확보/미실행: {initial_count}/18.',
            '- 100회 예산 내 미달은 수렴 불가능이나 물리적 불가능의 증거가 아니다.',
            '- 학습 중 확률적 성공과 고정 정책 평가를 구분한다. 동일 초기 반복은 독립 학습 난수가 아니다.',
            '- 처음 통과한 경계와 선택 모델은 results.json의 history/confirmation에서 확인한다.',
            '- 초기 배치 오류는 초기 후보의 native_endpoint_diagnostics.json, 실행 오류는 상태 원장의 errors와 stdout을 대조한다.']
        (BASE/'분석/REPORT.md').write_text('\n'.join(report)+'\n')
        write(BASE/'분석/영상목록.json',[dict(case_id=c['case_id'],path=c.get('video'),
            status=c.get('video_status','missing'),episode_success=c.get('video_episode_success'),
            checkpoint=c.get('video_checkpoint'),sha256=c.get('video_sha256')) for c in cases])
        with (BASE/'분석/results.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(table[0]))
            writer.writeheader();writer.writerows(table)



def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=BASE/'로그/study_v1')
    parser.add_argument('--hours',type=float,default=8)
    args=parser.parse_args()
    if not 0<args.hours<=8:parser.error('시간 예산은0초과8이하')
    (ROOT/'.runtime').mkdir(exist_ok=True)
    with (ROOT/'.runtime/guitar_gpu_study.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=Study(args.out,args.hours)
        def stop(signum,frame):raise KeyboardInterrupt('감독 종료신호 '+str(signum))
        signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
        try:state.run()
        except BaseException as error:
            if state.child is not None:terminate(state.child)
            state.state.update(status='blocked' if 'GLOBAL_' in str(error) else 'interrupted',error=repr(error),finished_at=now())
            state.save();raise


if __name__=='__main__':main()
