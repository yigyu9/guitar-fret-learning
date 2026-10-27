# Loaded back-facing 음성 사례: 다음 진단 준비 메모

문서 계획만 작성했다. GPU 실행·새 원자료 재처리·활성 소스 수정은 하지 않았다. 검증 완료된 live111,616표본 감사와 정적37×67 감사는 다시 실행하지 않았다.

## 현재 판단

**현재 palmar 표본의 위치 기하=true·facing=false는 수학적으로 배제되지 않는다. 그러나 원래 관절 범위와 충돌을 만족하는 실제 하중 상태에서 도달 가능한지는 미확인이다.** 기존0개 결과는 불가능 증명이 아니다. 다음 시험은 판정 문턱을 바꾸기보다 방향을 독립적으로 바꿔야 한다.

기존 정의는 할당 말단 resultant≥0.01N, 같은 유효 pad 표본 중 하나 이상이 원래 cell/3mm lateral/높이[−1,3]mm 조건을 통과하고, **그 위치 조건을 통과한 모든 표본이** facing cosine≥0.1을 실패하는 상태다. nearest 표본의 cosine 하나가 낮다는 사실만으로 이 조건을 만족하지 않는다. dorsal 면의 실제 접촉과 이 registered-palmar 음성 조건도 동일하지 않다.

### 자유 강체 기하에서는 가능한 이유

`fingertip_pad._sample_patch`는 모든 등록 triangle normal에 `normal_z≤0`을 요구한다. 기타 press-plane 단위 법선을 n이라 하고, distal-local z축을 −n으로 보내는 회전 R을 생각하면 모든 등록 normal m에 대해 `−(R m)·n=m_z≤0<0.1`이다. 유효 표본 하나를 선택해 그 회전 후 위치를 원래 finite string/cell 내부·평면 높이1mm에 맞추는 평행이동을 정하면 위치 조건은 참이고 facing은 거짓이다. 여기서 사용한 것은 기존 표본/평면 정의에 대한 존재 논증이며, 시뮬레이터 상태나 합성 접촉을 만들거나 저장하지 않았다.

이 구성은 임의 SE(3) 자세의 존재만 보인다. 사람의 연결 관절, 손바닥·다른 손가락 간섭, 기타 convex collision, 하중의 실현 가능성을 포함하지 않는다. 실제 dorsal 쪽이 넥에 닿으면 반대편 palmar patch는 손가락 두께만큼 위로 올라가 높이3mm 창을 벗어날 수도 있다. 반대로 palmar patch를 back-facing인 채 평면 가까이 두면 몸체가 넥을 관통해야 할 수도 있다. 현재 그 두께·충돌 제약을 전체 가동범위에서 증명한 자료는 없으므로 **물리적으로 불가능하다고 결론내리지 않는다**. 완전180° 반전보다 측면에 가까운 경계 방향에서 이 조건이 먼저 나올 가능성도 가설로 남긴다.

### 기존 궤적이 검사하지 않은 방향

v2 teacher는 guitar-local wrist 위치와 quaternion을2초 ramp 뒤 고정하는 팔12축 feedback이다. release128개는 그 wrist 목표를 공유하면서 중지4축을 reference↔035로 이동한 조건이다. 즉 wrist 방향을 독립적으로 스윕한 실험이 아니다.

| 중지 축 | 현재 action 하한 | 035 | reference | 상한 (rad) |
| --- | ---: | ---: | ---: | ---: |
| middle1_x | −0.698132 | 1.105276 | 1.120066 | 1.570800 |
| middle1_z | −0.349066 | 0.339686 | 0.198395 | 0.349066 |
| middle2 | 0 | 0.669367 | 0.994033 | 1.570800 |
| middle3 | −0.087266 | −0.086164 | 0.043064 | 1.570800 |

reference↔035의 PIP/DIP 요청 차이는 각각 약0.325/0.129rad다. 기존 분석의 env6 실제 q4 range도 약[0.035,0.100,0.324,0.129]rad다. 이 좁은 궤적에서 wrist 목표는 고정이지만, 실제 distal 방향이 고정되었다고 입증한 것은 아니다. 관절각은 실제로 변했다. 따라서 현재0개를 ‘방향이 거의 안 변해서’라고 인과 확정할 수 없고, **방향 노출이 제한되었다는 설명을 먼저 분리 검사**한다.

직접 바꿀 변수는 distal 방향에 영향을 주는 middle1_x/middle2/middle3, 그리고 고정 teacher wrist orientation이다. middle1_z는 주로 횡방향 정렬을 바꾸므로 첫 방향 시험에서는 reference값을 유지한다. wrist에 Euler각을 그대로 더하지 않고, 기타 좌표의 원래 string 방향 u 또는 평면 내 직교축 v=n×u에 대한 quaternion 회전을 사용한다. 단순히 n 주위로 yaw만 바꾸면 normal의 평면 법선 성분을 충분히 바꾸지 못할 수 있다.

## 최소 후속 GPU안 — 별도 승인 전 실행 금지

원래 중지 row8 `event-000052/string-3/note-53` 하나, 기타 고정, 기존035 reset, native 범위·PD·힘·충돌·안전·판정·4 substeps/control을 그대로 쓴다. 새 teacher 방향/접근 조건은 **새 진단 프로토콜의 입력**으로 모두 기록한다. 기존 reference/teacher/체크포인트 bytes를 고치거나 이전 strict 동일 과제라고 가장하지 않는다. 정책 학습·PPO·보상 변경은 필요 없다.

첫 배치는 아래8조건×2회=16개 첫 시도로 제한하는 안이다. 조건 배정은 env_id%8, 반복은 env_id//8로 실행 전에 고정한다. 양/음은 해부학 명칭이 아닌 명시한 기타 좌표축의 부호다. 결과를 보고 각도·조건·반복 수를 늘리지 않는다.

| 조건 | 중지4축의 유한 목표 | wrist 방향 목표 |
| --- | --- | --- |
| 0 | 원래 reference | 원래 teacher; 기존2초 ramp/hold 대조 |
| 1 | 원래 reference | 원래 teacher; 아래 clearance 접근만 적용한 대조 |
| 2 | middle1_x/middle2/middle3를 각각 기존 하한, middle1_z는 reference | 원래 teacher |
| 3 | reference에서 middle3만 기존 상한 | 원래 teacher |
| 4·5 | 원래 reference | u축 +90° / −90° × 원래 teacher quaternion |
| 6·7 | 원래 reference | v축 +90° / −90° × 원래 teacher quaternion |

조건1~7은 처음부터 몸체를 돌려 주입하지 않는다. 기존 유한 팔 제어로0→2초에 wrist 목표를 원래 위치+n×15mm의 clearance 위치와 지정 방향으로 이동하고,2→2.8초에 위치만 원래 teacher 위치까지 접근해 원래 음 끝 뒤까지 유지한다. 모든 준비 물리 tick과 실제 종료를 기록한다. clearance15mm가 전체 손의 충돌 회피를 보장하지 않으며, 부딪히거나 원래 종료 조건에 걸리면 해당 실패를 남긴다. 조건0과1을 둬 접근 시간 변경 자체가 positive를 없앴는지도 구분한다. 원래 local press2.9787/onset3.0/end3.1174초를 재시간화하지 않는다.

±90°는 **요청하는 wrist pose 차이**이며 실제 관절에90°를 직접 더하는 명령이 아니다. 기존 팔 action 범위는 native 전체 범위보다 좁을 수 있다. 예를 들어 현재 L_Wrist_y action 범위는[−0.785398,−0.435194]rad다. 기존 Jacobian feedback·arm3rad/s·tick당 보정0.5°·기존 action clamp를 그대로 적용하고, 큰 방향 요청을 못 따라가면 방향 미도달로 기록한다. 손가락은 기존4rad/s inverse codec을 사용한다. action clamp를 풀거나 PD/힘을 올려 도달을 보장하지 않는다.

이 첫 배치는 ‘범위 내에서 방향을 충분히 바꿀 수 있는가’를 확인하는 최소 구분 시험이다. 각 조건의 실제 손끝 위치가 원래 cell에 닿는다는 사전 보장은 없다. 새 forward-kinematic 위치 보정·더 큰 wrist 이동·새 target·더 긴 시간창은 이 배치에 몰래 추가하지 않는다. 위치 미도달이면 다음 별도 계획에서만 원인과 필요한 위치 이동을 검토한다.

### 실제 피부 반대편 접근과 판정 실패를 혼동하지 않기

- 방향 변경은 먼저 넥에서 떨어진 clearance 구간에서 요청하고, 이후 원래 넥 표면으로 유한 접근한다. 실제 native finger mesh의 등록 palmar 영역과 그 반대편을 영상/원래 mesh 좌표로 함께 확인한다. 새 가상 dorsal 표본을 성공 판정에 넣지 않는다.
- ‘반대편 피부가 넥 쪽을 향함’, ‘반대편 mesh가 넥 hull에 가까움’, ‘그 distal body가 loaded임’, ‘등록 palmar 음성 조건 만족’을 서로 다른 관측으로 기록한다. 실제 dorsal 접촉이어도 palmar position=false라면 원하는 음성 witness는 미확보다.
- GPU resultant로 접촉 pair나 실제 현 압력을 인증하지 않는다. 피부/넥의 native 접촉 상대까지 확정하려면 별도의 실제 pair 증거가 필요하다. 이번16환경 설계만으로 pair 인증이나 이전212N 전체 몸체 이슈 해결을 주장하지 않는다.

### 사전 판정과 필요한 기록

각 조건은 실패를 제외하지 않은2개 분모로 아래 gate를 순서대로 남긴다. 최소 한 표본 사례와, 있으면13개 연속 endpoint의50ms span을 구분한다. 핵심 음성 정의는 기존 조건 그대로다.

1. 유한 명령·기존 bounds/rate/PD/힘 유지, 실제 wrist/선택 관절의 방향 목표 오차. 요청은 컸지만 실제 방향이 바뀌지 않았다면 **제어/방향 도달 실패**다.
2. actual position geometry 노출과 nearest 거리/높이, 위치를 통과한 각 표본의 facing cosine. 방향은 바뀌었지만 cell/높이에 못 왔으면 **위치 도달 실패**다.
3. position=true & facing=false지만 resultant<0.01N이면 **음성 기하는 도달·하중 미도달**다. 하중을 만들었다고 합성 처리하지 않는다.
4. position=true & facing=false & resultant≥0.01N이고 해당 물리/손목 실패 전이면 **원래 음성 witness 확보**다. positive/candidate=false와 actual clean·달성·9항 보상도 함께 기록한다. 원래 reward값을 임의로0으로 요구하지 않는다.
5. 조건 내내 same-sample facing이 남으면 **이번 방향 범위에서 음성 미확보**다. 물리적으로 불가능하다는 뜻이 아니다. 모든 실패 종료 시점 뒤 자료는 성공 수에 넣지 않는다.

240Hz에는 첫 시도 mask·시계·q4/target4·distal/guitar/wrist pose·할당 distal force **벡터와 norm**·same-sample 위치/facing mask·높이/거리/cosine·종료 전 상태를 저장한다. 60Hz에는 wrist 요청/실제 오차, action clipping, 원래 ledger와9항 보상을 남긴다. 기존 helper와 독립 pose→pad 재구성, 새 출력만 사용, pre/post source/config/script SHA, scene 종료·finite·clock 검사를 유지한다. 실행 전 별도 검수와 GPU 승인이 필요하다.

## 아직 이용하지 않은 과거 자료의 파일 목록 확인

이번에는 파일 존재와 기록 코드의 capture scope만 확인했다. 아래 NPZ 내용을 새로 열어 광범위 판정을 돌리지 않았다.

| 과거 경로 | 기존 감사와 관계·후속 활용 한계 |
| --- | --- |
| `01_control/{incremental,position}/trace60.npz`, `trace240.npz` | negative37×67 감사의 입력 목록에는 없다. 기록 코드상 모든84행의 q/force와 env0의60Hz body_state가 분리되어 있다. 다른83행에240Hz body pose가 있다고 간주할 수 없다. 압현 target을 향한 팔 안내도 없으므로 후보 기하·하중이 있는지는 미확인이다. |
| `01_control/fixed/{incremental,position}/trace60.npz`, `trace240.npz` | 마찬가지로 기존 negative audit 대상 밖이다. 기타 고정 제어 비교의 원자료이며 실제 target-facing 증거 존재는 미확인이다. 모든행 DOF/force만으로 방향 음성을 인증하지 않는다. |
| `01_control/thumb/{limited_rear_probe,deeper_rear_probe}/physics_env0000.npz` | 기존 negative audit 입력 목록 밖이다. 엄지 rear 시험 자료이므로 중지 row8 negative를 포함한다는 보장은 없다. 필요한 실제 중지 pose/force/neck 상태가 동일 endpoint에 있는지부터 별도 좁은 확인이 필요하다. |
| `02_contact_reward/static_*`, `teacher_*/trace240.npz` | 기존 감사가 glob으로 이미 확인한 범위다. 이번0개 문제를 피하려고 ‘새 미사용 증거’로 다시 세지 않는다. 같은 실행의 poses60/teacher_trace60은 별도 반복 실험이 아니다. |
| `02_contact_reward/ledger_fixed_B_fast_normal_guard/{trace240,control60,teacher_trace60}.npz` | 기존 실제-clock 원장 검사에 포함되거나 같은 실행의 보조자료다. 새 독립 negative가 있다고 주장하지 않는다. |

따라서 현재 남겨 둘 결론은 **기하 정의 자체의 논리적 모순은 없지만 원래 관절·충돌·실제 하중까지 포함한 reachable loaded-back-facing은 미확인**이다. 별도 승인된 좁은 유한 방향 시험으로 도달/기하/하중 gate를 분리하는 것이 다음 단계다.

근거: 현재 `guitar_learning/gpu/fingertip_pad.py`, `short_finger_learning/{runtime,wrist}.py`, 원 run_01 training_contract·settings 및 기존 cases.json, negative_snapshot_audit precommit·summary·감사 코드의 입력 목록, stage1 control capture 코드. 검증된 실제 live 감사 결과는 [facing_negative_audit.json](facing_negative_audit.json), 보상·분모는 [RESULTS.md](RESULTS.md)를 따른다.
