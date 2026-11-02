"""기존 검사에 쓰지 않고 완료 원장과 입력을 읽어 검증 결과만 기록한다."""
import collections
import hashlib
import json
from pathlib import Path
import time

ROOT=Path('/home/ajou/yigyu/3')
OUT=Path(__file__).resolve().parent.parent
RUN=ROOT/'docs/2026-11-02/압현실험/단일압현/전수검증_1-14_v1/로그/sweep_v1'
REC=ROOT/'docs/2026-11-02/압현실험/손가락별진행상태/작업자료/소스간섭_재검사/state.json'

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,value):
    p=OUT/name; tmp=p.with_suffix(p.suffix+'.tmp')
    tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)

def main():
    deadline=time.monotonic()+4*3600
    while True:
        state=read(RUN/'state.json'); recovery=read(REC)
        write('진행상황.json',dict(updated_epoch=time.time(),status='waiting',finished=state.get('finished'),
            total=state['total'],remaining=state.get('remaining'),counts=dict(collections.Counter(
            r.get('outcome','inspection_error') for r in state['results'].values())),
            recovery=recovery,estimated_remaining_s=state.get('estimated_remaining_s')))
        if state.get('status') in ('interrupted','blocked_input_or_integrity_error') or recovery.get('stage')=='failed':
            raise RuntimeError('기존 검사 또는 복구 중단; 원문 상태 파일 확인')
        if state.get('completed') and recovery.get('completed'):break
        if time.monotonic()>deadline:raise TimeoutError('완료 대기4시간 초과')
        time.sleep(30)
    manifest=read(RUN/'manifest.json')
    if sha(RUN/'manifest.json')!=state['manifest_sha256']:raise ValueError('명세 SHA 불일치')
    if len(state['results'])!=336 or set(state['results'])!=set(manifest['cases']):raise ValueError('336조합 분모 불일치')
    for p,expected in manifest['pins'].items():
        if sha(p)!=expected:raise ValueError('명세 입력 SHA 불일치: '+p)
    errors=[];cache={};counts=collections.Counter();rows=[]
    for case,entry in state['results'].items():
        try:
            if entry['status']!='done':raise ValueError('정상 실행 완료 아님')
            path=Path(entry['report']);report=read(path)
            if report.get('schema')!='guitar_learning.range336.native_single_press.v1' or report.get('case')!=case:
                raise ValueError('보고서 identity 불일치')
            if report.get('environments')!=1 or report.get('start_denominator')!=1 or report.get('optimizer_updates')!=0:
                raise ValueError('실행 분모 불일치')
            if report.get('failure') or not all(report.get(k) for k in ('completed','execution_completed','source_sha256_match_after','scene_closed','pool_closed')):
                raise ValueError('실행 검증 실패')
            pins=read(path.parent/'inputs_before.json')
            if not pins:raise ValueError('빈 입력 pin')
            for p,expected in pins.items():
                if p not in cache:cache[p]=sha(p)
                if cache[p]!=expected:raise ValueError('현재 입력 SHA 불일치: '+p)
            outcome=report['outcome']
            if outcome!=entry['outcome']:raise ValueError('원장과 보고서 결과 불일치')
            if outcome=='press_success':
                episode=read(path.parent/'episode.json')
                if not report.get('task_success') or not report.get('preparation_ready') or episode.get('song',{}).get('stage_success') is not True:
                    raise ValueError('성공 에피소드 원장 불일치')
            counts[outcome]+=1;rows.append(dict(case=case,outcome=outcome,report=str(path),sha256=sha(path)))
        except Exception as exc:errors.append(dict(case=case,error=repr(exc)))
    result=dict(completed=not errors,updated_epoch=time.time(),total=336,verified=len(rows),counts=dict(counts),errors=errors,rows=rows,
        source_state=str(RUN/'state.json'),recovery=str(REC),source_state_sha256=sha(RUN/'state.json'))
    write('검증결과.json',result)
    text=['# 단일 압현 검사 최종 결과','',f"336조합 중 검증 통과 {len(rows)}개, 검사 오류 {len(errors)}개.",'']
    text.extend(f'- {key}: {value}개' for key,value in counts.items())
    text.extend(['','정해진 동작의 물리 진단이며 학습 성공률은 아니다. 준비 실패는 물리적 불가능 판정이 아니다.',
        '','다음 전환 후보의 단일 압현 결과:'])
    for case in ('middle_s3_f6','middle_s3_f8','middle_s1_f6'):
        text.append(f"- {case}: {state['results'][case].get('outcome')}")
    text.append('\n전환 자체의 제한 시간 내 실현성과 새 손가락별 구조의 GPU 실행은 별도 검증이 필요하다.\n')
    (OUT/'최종결과.md').write_text('\n'.join(text))
    write('진행상황.json',dict(status='complete' if not errors else 'verification_failed',**{k:v for k,v in result.items() if k!='rows'}))
    if not errors:
        p=OUT/'README.md';p.write_text(p.read_text().replace('- [ ]','- [x]'))

if __name__=='__main__':
    try:main()
    except Exception as exc:
        write('진행상황.json',dict(status='failed',completed=False,error=repr(exc),updated_epoch=time.time()));raise
