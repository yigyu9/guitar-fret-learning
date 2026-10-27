# 현재 초기 자세의 왼손 위치 보정 비교안

2026-10-07. **사용자가 ‘3조건 비교 진행 승인’으로 아래 비교 조건을 승인했다.**
이전 p08 제안은 보존한다. 이번 입력은 trials/quiescent_3s_v1/reference.json이다.
현재 초기 FK 좌표 대조와 동일 PI 0.1초의 Jacobian/속도 계측을 근거로 삼는다.
초기 위치·회전을 크게 이탈한 후기 기타 자세로 유지 목표를 바꾸지 않는다.

## 근거와 목적

기존 PI의1초 기타 오차는73.268255mm/13.439339°이며 LH접촉0·큰 이탈이 남는다.
초기 FK에서는 raw Jacobian을 위치 좌표 미분으로 바로 쓸 수 없었다. 왼팔의
Thorax/Shoulder/Elbow/Wrist 3좌표별 SO(3) left tangent 변환과 native COM 기준
source 중심 이동 후 미분 오차가 최대0.274299mm/rad로 줄었다.
동일 PI 0.1초에서는 refresh한 raw Jacobian×full105 native velocity의 COM 속도 오차가
최대LH1.500569mm/s/RH1.371527mm/s였다. 상태·trace·control prefix는 기존 run과 같았다.
refresh 전 buffer는 t=0에0, 이후 직전 refresh의 값이었다. 매 제어 시점에 refresh한다.
이 결과는 정확한 항등식이나 향후 모든 자세의 검증이 아니다. 최초 비교는0.1초로 제한한다.

왼손 source hull 체적 중심의 world 위치를 초기값에 가깝게 유지하는 목표 보정을
관절 PI와 결합한다. 이는 실제 손/기타 고정·강제 부착이 아니라 PD 목표각 계산이다.
source 중심은 해부학적 중심·접촉점·COM이 아니다. 기타 p/q feedback은 이 단계에 없다.

## 확인받을 변경과 비교 조건

| 조건 | 왼팔12 | 오른팔12 | 새 최종 목표 변화율 제한 |
|---|---|---|---|
| PI | 기존 승인 관절 PI | 기존 승인 관절 PI | 기존대로 없음 |
| RATE_PI | PI, 새 변화율 제한만 적용 | PI, 같은 제한 | 0.02rad/60Hz update |
| PALM_RATE | 위치 task + PI regularizer | RATE_PI와 동일 | 같은0.02rad/update |

같은 초기q/절대LA/PD/solver/기타 목표로 세 조건을 각24 physics steps 비교한다.
위치 task 효과는 PALM_RATE–RATE_PI, 변화율 효과는 RATE_PI–PI로 구분한다.
Torso/Spine/Chest9·finger42·C02하체 목표를 유지하고 실제 움직임은 측정한다.
fixed human root, 자유 기타 +5mm 초기 p/q, 주요66관절 연결을 유지한다.

## 하나의 최종 목표와 계산

이번 무연주 q_play는 초기각, p_goal은 초기 source palm 중심이다.
최종 연주에서는 p_goal을 연주 목표와 함께 갱신해야 하며 영구 world anchor로 승계하지 않는다.
각60Hz update에서 현재 native q_actual·p_actual을 읽고 Jacobian을 refresh한다.
왼팔12의 velocity Jacobian 각3열에 B(q_actual)=SO(3) left tangent를 오른쪽 곱한 뒤
COM에서 source 중심으로 옮겨 위치 좌표 미분 A(3×12)를 만든다.

위치 보정은 다음 bounded least-squares를 푼다.

`||A(q_play + delta - q_actual) - 2(p_goal - p_actual)||² + (0.05m/rad)² ||delta - delta_PI||²`

2는 위치 오차의 무차원 배율이며 velocity gain이 아니다. delta_PI는 기존 PI 계산을
기존 총 보정/model/C02 box로 clip한 후보이며, solve에는 clipping 전 raw PI도 기록한다.
delta의 bounds는 총 보정±0.15rad∩native 한계∩C02±0.3rad∩직전 최종 목표±0.02rad다.
모든 bounds는 delta 좌표로 옮긴다. 각 축의 하한은
`max(-0.15, q_native_min-q_play, q_C02-0.3-q_play, q_final_prev-q_play-0.02)`,
상한은 `min(0.15, q_native_max-q_play, q_C02+0.3-q_play, q_final_prev-q_play+0.02)`다.
오른팔 RATE_PI도 같은 bounds를 사용한다. 최종 q_play+delta 하나만 기존66 목표에 합친다.
상태·pose를 쓰거나 기타에 인위적 복원력을 적용하지 않는다.

적분은 기존 gain1/2를 유지한다. e=q_play−q_actual의 적분을 제안하고 최종 bounded
목표를 계산한 뒤, `e*(raw_PI-delta_applied)>1e-12`인 축의 이번 적분 증가를 되돌린다.
되돌린 축의 mask는 이번 update 안에서 단조롭게 추가하며 재solve한다. 새 blocked 축이
없을 때 종료하므로 최대24개 축을 되돌리며 최초 solve 포함 최대25회다.
이미 되돌린 축을 다시 적분하지 않는
보수적 anti-windup이며 원본 PI 조건의 구현은 그대로 둔다. solver 실패/nonfinite는
trial을 실패로 저장·중단하고 임의 다른 controller로 전환하지 않는다.

## 소단계 체크리스트

- [x] 사용자 확인: 새 위치 task·0.02rad/update 제한·regularizer/배율·최종 목표 anti-windup.
- [x] 제한/형상 중심 변환/적분 복구를 pure numerical cases로 검증하고 별도 코드 검수.
- [ ] 현재 초기 source/LH 조건을 확인한 뒤 PI/RATE_PI/PALM_RATE 각0.1초를 실행한다.
  기존 PI는 저장 prefix와 대조하고 새 조건의 실제 상태/목표/접촉/장력/포화를 기록한다.
- [ ] 실제 palm 방향 proxy·국소 넥 위치·기타 p/q/속도·관절 범위·solver 기록을 검토한다.
  기존 위쪽 반구 proxy를 벗어난 결과는 채택하지 않는다. 새 해부학적 hard limit은 넣지 않는다.
- [ ] 유망한 경우만0.5초/1초 연장을 검토한다. 그림·설명·로그·독립 검수를 누적한다.

허용 성공 수치와 연주 호환성은 아직 합의·검증되지 않았다. 이 단계는 손 위치의 유지가
기타 이탈을 줄이는지의 제어 비교이며 안정성·지지·연주 성공을 미리 선언하지 않는다.

추가 [저장 Jacobian 선형 범위 분석](PALM_TASK_AUTHORITY.md)에서0.1초 초기 손 위치 복귀에
필요한 세 축 변위는 기존 보정 box의 각 독립 범위 안에 있었다. 동시달성·비선형 FK·
물리 지지의 증명은 아니며 이 결과로 새task/변화율 제한 조건을 변경하지 않는다.

[초기 source 간격의 저장 상태 관찰](LEFT_EARLY_SOURCE_DIAGNOSTIC.md)도 수행했다.
선택한 첫0.1초의 위쪽 normal proxy/국소 높이 조건이 유지됐지만 palm–neck hull 간격은
0.545306→29.787930mm로 벌어졌고 완료step LH contact 행은 없었다. 자세 조건만으로
지지가 유지된다고 가정하지 않는다. 이후 사용자가 위3조건 비교를 승인했으며 조건은 그대로다.
