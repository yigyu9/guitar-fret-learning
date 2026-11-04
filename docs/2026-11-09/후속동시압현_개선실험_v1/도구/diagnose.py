"""변경 없이 남아 있는 C1/N01 원시 기록을 비교해 확인 사실과 한계를 저장한다."""
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np

STUDY=Path(__file__).resolve().parents[1]
ROOT=next(p for p in STUDY.parents if (p/'guitar_learning/train.py').is_file())
OLD=ROOT/'docs/2026-11-09/복합압현_야간확장_v1'
RAW=OLD/'실행/N01_native_16b911aefea0'
FIRST=ROOT/'docs/2026-11-09/복합압현_단계별실험_v1/검증/C1_재생_원인분석.json'
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temp.replace(path)

def main():
    episode=read(RAW/'episode.json');ledger=episode['left_note_ledger'];first=read(FIRST)
    with gzip.open(RAW/'finger_control_trace.jsonl.gz','rt') as stream:rows=[json.loads(line) for line in stream]
    audible=[r for r in rows if 3.<=r['score_time_s']<4.5]
    middle=np.array([r['actual_rad'][9:13] for r in audible]);ring=np.array([r['actual_rad'][13:17] for r in audible])
    actual=np.array([r['actual_rad'] for r in audible]);requested=np.array([r['requested_target_rad'] for r in audible]);applied=np.array([r['applied_target_rad'] for r in audible])
    mid=min(rows,key=lambda r:abs(r['score_time_s']-3.5));v=ledger['values'];sources=ledger['wrong_press_sources'];wrong=sources['values']
    names=sources['body_names'];causes=sources['contract']['causes'];contributors=[]
    for ti,target in enumerate(ledger['target_ids']):
        for bi,body in enumerate(names):
            for ci,cause in enumerate(causes):
                seconds=wrong['wrong_source_time'][ti][bi][ci]
                if seconds:contributors.append(dict(target=target,body=body,cause=cause,time_s=seconds,fret_min=wrong['wrong_source_fret_min'][ti][bi],fret_max=wrong['wrong_source_fret_max'][ti][bi]))
    diagnostics={name:v[name] for name in ('clean','wrong','contact_time','geometry_time','facing_time','loaded_target_time','body_load_time','distal_target_time','other_higher_time','own_wrong_fret_time','own_wrong_string_time')}
    native= dict(ledger=diagnostics,contributors=contributors,sample_count=len(audible),
        actual_middle_mean_rad=middle.mean(0).tolist(),actual_ring_mean_rad=ring.mean(0).tolist(),
        request_apply_max_abs_rad=abs(requested-applied).max(0).tolist(),request_actual_mean_abs_rad=abs(requested-actual).mean(0).tolist(),
        at_3p5=dict(time_s=mid['score_time_s'],targets=mid['targets'],natural_preparation=mid['natural_preparation']))
    assert v['body_load_time']==[1.5,1.5] and v['other_higher_time']==[1.5,0.]
    assert len(contributors)==1 and contributors[0]['body']=='human/LH:ring3' and contributors[0]['cause']=='other_higher'
    pins={str(p):sha(p) for p in (Path(__file__).resolve(),FIRST,RAW/'report.json',RAW/'episode.json',RAW/'finger_control_trace.jsonl.gz',RAW/'diagnostic_trace.jsonl.gz',RAW/'inputs_before.json')}
    result=dict(completed=True,schema='successor_simultaneous_pre_diagnosis.v1',confirmed_primary_blocker='약지 ring3 전체 표면이 S3F7 higher 조건을 만족하여 중지 S3F6을 막음',
        first_C1=first['ledger'],later_N01=native,
        facts=['후속 N01에서는 중지 geometry·facing·담당말단 하중이 각 1.5초이며 단순 하중 부족 설명은 맞지 않는다.','중지 clean은 0, 약지 clean은 1.5초이고 중지 other_higher는 1.5초이다.','방해 원장은 ring3/F7 한 원인만 기록하며 특정 원인 표본번호는 기록하지 않았다.'],
        limitations=['몸체 netforce는 접촉 상대·개별 압력·실제 소리를 식별하지 못한다. 하중 있는 몸체 전체 표면을 쓰는 보수적인 오압현 판정이며 이번 실험에서도 변경하지 않는다.','이전 native 원문에는 전신 q105·몸체·기타 궤적이 없다. 손가락 21축과 국소 기하만으로 팔 PD·기타 미세이동·FK 차이의 기여를 정확히 분해할 수 없다.','이상 FK 목표 약 -0.5mm와 native 선택 패드 높이 약 +2.8/+2.34mm의 차이는 서로 같은 표본을 추적한 보정값이 아니다. 약 3mm 여유 설계의 동기이며 원인 확정이 아니다.','정적 source convex 교차/분리와 native cooked 충돌·하중 인증은 서로 다르다.'],
        next_validation=['새 장면에서 G0→G1→G2를 각각 재생하고 중지·약지 clean, wrong source, 하중을 함께 측정한다.','0/2.5/3/3.5/4.4초의 실제 q105/qd/body/contact/request/applied snapshot을 새 읽기 전용 기록으로 확보한다.','fresh native 두 음 성공·유지·해제와 안정성 통과 전에는 후보로 학습하지 않는다.'],source_sha256=pins)
    write(STUDY/'분석/사전진단.json',result)
    lines=['# 동시 압현 후속 실험 사전진단','','검증된 주원인은 약지 끝마디 ring3의 인접 S3F7 접촉 판정이다. 중지의 S3F6을 더 높은 프렛에서 막고 있다. 보상·제어·오압현 판정·하중 기준을 바꾸지 않고 grip 자세만 비교한다.','','| 실제 native 기록 | 첫 C1 | 이후 N01 |','|---|---:|---:|','| 중지 clean | 0초 | 0초 |','| 약지 clean | 1.29583초 | 1.5초 |','| 중지 담당 말단 하중 | 0초 | 1.5초 |','| 중지 geometry / facing | 1.4875초 | 1.5초 |','| 중지 other_higher | 1.30417초 | 1.5초 |','','이후 N01에서는 중지 하중도 확보됐으므로 현재 실패를 하중 부족으로 단정하면 안 된다. 원시 wrong 원장은 ring3, S3, F7, other_higher만 양성이다. 담당 패드 표본 145/273이 실제 방해 표본이라는 뜻은 아니다.','','3.5초 native의 중지/약지 선택 패드 높이는 각각 약 +2.800/+2.336mm, 방향 cosine은 0.900/0.918이다. 이상 FK가 목표로 둔 약 -0.5mm와 약 3mm 차이가 보인다. 전신 q와 기타 body 원문이 없어 같은 표본·같은 자세의 오차로 확정할 수는 없다. 손가락 요청/적용 차이, 실제각 추종 통계는 JSON에 별도로 보존했다.','','## 바꾸는 한 변수','','G0는 이전 N01의 요청각·시각 exact 복사 대조다. G1은 깊이 -1mm/인접줄 회피 여유1.5mm, G2는 깊이 -2mm/여유3.5mm를 목표로 새 grip을 탐색한다. 팔12축과 두 담당 손가락8축만 허용하며 비담당 검지/소지 각은 초기 그대로다. 양쪽 담당 패드·전체 virtual 오압현·손가락 source 교차·비담당 넥 source 교차·실제 관절한계와 quintic 속도를 검사한다. 원래 발음3~4.5초, 준비0.5~2.5초, 해제4.5초 이후를 유지한다. A0는 이전 T1 요청 경로 그대로 복사해 seed17 재현용 입력만 준비한다.','','+0/+1.5/+3mm 평행이동 검사는 높이 민감도 검사다. native 팔/기타 움직임의 복원이나 부하 인증이 아니다. 넥과 담당 끝마디의 source 교차는 접촉 후보로 기록하고, 비담당 마디의 넥 교차 및 손가락 간 source 교차가 있는 후보는 선택하지 않는다. 경로 source 검사는 명시된 이산 시점이므로 연속 충돌 부재 증명이 아니다.','','## 확정할 수 없는 것과 다음 확인','','body netforce는 접촉 상대나 실제 줄 압력을 구분하지 못한다. 하중 있는 몸체의 전체 표면에 가상 줄 접촉을 적용하는 보수적인 현재 판정은 그대로 유지한다. 이전 raw 전신 q/body 부재 때문에 약 3mm 차이 원인을 추정으로 단정하지 않는다.','','새 native 재생에서 0/2.5/3/3.5/4.4초 실제 q105·qd105·body·contact force·요청각·적용각·목표별 geometry/load/facing/wrong source를 저장한다. G1/G2 정적 통과는 native 성공이 아니다. 새 재생에서 두 음 clean·잘못된 접촉·유지/해제·안정성까지 통과해야 후속 학습을 허용한다.','','입력 exact 비교와 변조 거부는 검증/입력CPU검증.json, 후보별 실패/성공 CPU 수치는 검증/참조에 있다. 원문·기존 모델·기존 실행 자료는 수정하지 않았다.']
    (STUDY/'분석/사전진단.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'completed':True,'contributors':contributors,'source_count':len(pins)},ensure_ascii=False))

if __name__=='__main__':main()
