"""Render a concise final presentation from already-checked analysis JSON."""
import hashlib
import json
from pathlib import Path

PHASE=Path(__file__).resolve().parent
source=PHASE/'stage1_final_analysis_v1.json'
raw=source.read_bytes()
data=json.loads(raw)
assert data['validation_passed'] and data['final_requested']
output=PHASE/'stage1_final_summary_v1.md'
lines=['# Stage1 최종 분석', '',
    '시간창 ±0.5초에서 각 손12 updates·7,200전이를 완료했다. 학습 episode는 양손 각각24/24 성공했고 물리 실패는 없었다. 별도의 결정적 native 평가도 각2/2 통과했다. 평가 checkpoint counter12·완료학습12·설정12가 일치한다.', '',
    '| 손 | 회차 | audible 유지율 | 최초 down 절대오차(ms) | 추가 down / up | 기타 최대 이동(mm) | 발 최대 이동(mm) |',
    '|---|---:|---:|---:|---:|---:|---:|']
for role,r in data['roles'].items():
    for e in r['native_evaluation']['episodes']:
        error=e['first_target_down_abs_error_s']
        lines.append('| %s | %d | %s | %s | %d / %d | %.6f | %.6f |'%(role,e['episode']+1,
            '%.6f'%e['audible_hold_fraction'] if role=='left' else '해당 없음',
            '%.6f'%(error*1000) if error is not None else '해당 없음',
            max(0,e['target_direction_crossings']-1),e['up_crossings'],
            e['safety240']['guitar_displacement_max_m']*1000,e['safety240']['foot_displacement_max_m']*1000))
left=data['roles']['left'];right=data['roles']['right']
pre=right['stage1_preflight']['episodes'][0]['first_target_down_abs_error_s']
post=right['native_evaluation']['episodes'][0]['first_target_down_abs_error_s']
fractions=[e['hold_reward_outside_audible_fraction'] for e in left['training']['episodes'] if e['committed']]
lines+=['', '오른손 최초 목표 down 오차는 같은 stage1 계약의 이전 사전평가 %.6fms에서 %.6fms로 %.6fms 감소했다. 첫 crossing과 best가 동일하다. 추가 down1회와 반대 up1회는 남았다. stage0에서 stage1 사전평가로 바뀐 값은 단계 관측·판정이 달라진 결과이므로 PPO 개선량에 합산하지 않는다.'%(pre*1000,post*1000,(pre-post)*1000), '',
    '왼손 audible 유지율은 이미100%%인 상태를 유지했다. 학습 hold 보상의 audible 밖 성분은 평균 %.3f%%다. stage0의 약91%%와 총보상을 직접 비교하지 않는다. 시간창 수축으로 보상 적분 구간과 추가 crossing 분류도 바뀌었다.'%(sum(fractions)/len(fractions)*100), '',
    '현재 보상은 action_change·terminal_failure와 timing 항으로 구성되며 release는 측정 이력일 뿐 명시적 해제 보상은 없다. 긴 단음 접촉 유지를 연주 시간 정밀성으로 해석하지 않는다. 필요한 시점의 해제·다음 프렛 전환·목표 다양화와 불필요 타현 억제를 별도로 평가할 필요가 있다. 현재 근거만으로 네트워크 확대나 안전 기준 완화를 우선하지 않는다.', '',
    '최종4개 episode 각각300제어 tick·1,200개240Hz 표본에서 시계/step 연속성, 비용 적분, 행동 범위와 반대손0, 실제 crossing 깊이·속도, 원 joint music 분리를 확인했다. 모든 표본의 any-support와 양발 접지율은100%였다. 가슴/삼중 접촉은 진단이며 지속 필수조건이 아니다. 원 joint music50/100ms는 모두0으로 손별 타이밍 단계 성공과 구분한다.', '',
    '| 손 | 실제 actor LR | KL retry 합계 | accepted KL 최대 |',
    '|---|---:|---:|---:|']
for role,r in data['roles'].items():
    s=r['training']['training_summary']
    lines.append('| %s | %s | %d | %.8f |'%(role,s['actual_actor_lr']['minimum'],s['retries_total'],s['accepted_KL']['maximum']))
lines+=['', '결론은 고정 단음·동일 시작 조건에서 기존 성공을 유지하면서 오른손 오차를 소폭 줄였다는 범위다. 일반화·음향·양손 결합 성공 또는 다음 단계 승격을 입증하지 않는다.', '',
    '[전체 수치·입력 SHA](%s)'%source,
    '[수집과 update 시간](%s)'%(PHASE/'collection_update_walltime_v1.md'),
    '![KL·실제 LR·critic](%s)'%(PHASE/'stage1_final_analysis_v1.png'), '',
    '표시 수정본: 기존 분석 JSON과 산출물은 보존했다. 입력 JSON SHA256: `%s`.'%hashlib.sha256(raw).hexdigest()]
with output.open('x') as stream:stream.write('\n'.join(lines)+'\n')
print(output)
