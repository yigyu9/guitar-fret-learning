# 실제 하중 접촉의 끊김: 읽기 전용 감사

V2 noisy에서 저장된 env0의 audible candidate 누락11개는 모두 distal 몸체의 측정 합력이 **정확히0N**인 끝점이다. 위치·높이·방향 기하는 계속 통과했다. 기록에서 넘은 gate는0.01N 경계의 작은 수치 출렁임이나3mm 거리 컷오프가 아니라 exported body-resultant의 unloaded flag다. 합력은 접촉 파트너·현별 압력·음향을 식별하지 않으므로 이를 현 압력0의 직접 측정으로 확대하지 않는다.

합력이0이라는 것은 pairwise 접촉이 없다는 증명이 아니다. 여러 접촉력의 벡터 상쇄, 접촉 파트너, 현별압력과 실제음향을 이자료로 분리할 수 없다. source `scene.py`는 Isaac Gym net-contact-force tensor를 refresh한 뒤 native human body 값을 논리몸체로 복사한다. physics240Hz·substeps1·CC_LAST_SUBSTEP이며 저장trace는60Hz 제어 이후끝점만 보존한다.60Hz 평균하중이나중간4개240Hz접촉이력은 아니다. reset행은force0으로mask되지만 감사의audible끝점은실제physics이후이고표면행은valid/post_failure검사로구별했다.

## 원 판정과 실제로 넘은 gate

`contact.py:554..649`의 positive는 동일한 원 distal 표본 하나가 아래를 동시에 만족하고 담당 distal 몸체에 하중이 있을 때 참이다.

- 목표 현까지 평면 내 횡거리≤3mm, 프렛 셀의 양쪽 경계에서2mm 안쪽.
- source playing plane 부호 간격[-1,+3]mm, inward facing cosine≥0.1.
- 담당 distal 몸체의 net force norm≥0.01N (`environment.py:552`).
- 최종 candidate는 positive AND NOT wrong (`environment.py:663..668`). FingerSkillEnvironment는 실제 assigned-pad/다른손가락 higher-fret wrong 출처를 적용한다.

최근접 `surface_distance`는 접근용 진단이며 유클리드 거리3mm를 직접 자르는 candidate gate가 아니다. 최근접 표본 하나의 gap/cos가 전체128표본 ANY 판정을 대신하지도 않는다. 저장 native body pose·live 기타·원128표본으로 모든354끝점의 기하를 CPU 재구성한 candidate가 두 조건·3음 모두 원 trace와 정확히 일치했다.

| 목표 | trace 열 / 원source | 물리 목표 | noisy 누락/끝점 | 기하·방향 미달 | unloaded 누락 |
|---|---|---|---:|---:|---:|
| A4 | 0 / 4 | 현3·프렛4·검지 | 1/11 | 0 | 1 |
| B7 | 1 / 7 | 현2·프렛5·검지 | 6/46 | 0 | 6 |
| B8 | 2 / 8 | 현2·프렛5·검지 | 4/21 | 0 | 4 |

모두 `human/LH:index3` 하중이며 deterministic env0는 같은78끝점에서 누락0이다. 추가로 env0..3의 A audible44끝점에서 noisy누락15개(환경별1/6/2/6)는 모두 saved geometry/facing 통과·unloaded다. deterministic은44끝점 모두 loaded이고 합력0.1204..0.1790N이다. 유효 facing 표본 cosine은 이창에서 약0.676 이상으로0.1 컷오프에 가깝지 않다. 전체128환경과 저장하지 않은240Hz 끝점까지 같은 원인이라고 확정하지 않는다.

## 실제 plane gap와 target 추종

아래는 noisy env0 각음의 loaded/unloaded 그룹 평균이다. nearest gap는 최근접 표본이고, eligible minimum은 횡거리·프렛셀·방향을 통과하는 표본들의 최소 gap다. 두 선택 표본은 다를 수 있다. 모든 단위는mm다.

| 음 | loaded nearest gap | unloaded nearest gap | loaded eligible minimum | unloaded eligible minimum |
|---|---:|---:|---:|---:|
| A4 | +0.21438 | +0.23277 | -0.30827 | -0.21728 |
| B7 | +0.18020 | +0.24390 | -0.25427 | -0.23062 |
| B8 | +0.22683 | +0.26337 | -0.14397 | -0.11181 |

unloaded에서 평균 gap가 더 바깥쪽이지만 loaded/unloaded 범위는 겹친다. eligible source 표본은 unloaded에서도 plane보다0.09..0.30mm 안쪽일 수 있다. 따라서 모든 패드가 떠 있다는 설명이나, 이값을 그대로 실제 collision penetration/현 압축깊이로 해석하는 설명은 성립하지 않는다. source plane/유한 pad 표본은 실제 solver 접촉점·접촉법선·압력을 직접 저장한 자료가 아니다. 기준이 접촉에 취약한 경계 근처에서 움직인다는 가설은 관찰과 양립하지만 **under-compressed라는 확정 또는 필요한 preload mm 추정은 불가능**하다.

actual−finite target 평균(도), 축순서 index1_x / index1_z / PIP / DIP:

| 음 | deterministic loaded | noisy loaded | noisy unloaded |
|---|---|---|---|
| A4 | -0.099 / -10.869 / -0.014 / -0.005 | +0.077 / -11.118 / -0.165 / +0.156 | +0.284 / -11.104 / -0.192 / +0.155 |
| B7 | +0.561 / -10.701 / -0.205 / -0.184 | +0.852 / -10.937 / -0.299 / -0.015 | +1.418 / -10.905 / -0.001 / +0.044 |
| B8 | +0.534 / -10.711 / -0.040 / -0.014 | +0.758 / -10.945 / -0.100 / +0.232 | +1.059 / -10.986 / +0.799 / +0.441 |

큰 index1_z 편차는 deterministic에서도 존재하며 새 잡음 효과로 돌리지 않는다. index1_x의 noisy−deterministic actual 차이는 loaded평균+0.321°, unloaded+0.339°로 범위가 크게 겹친다.78끝점에서 이 차이와 nearest gap 변화의 상관은+0.191, eligible minimum gap 변화와+0.163, force norm과-0.031이다. 목표index1_x잡음과실제차이의상관은+0.466이다. 네축이 동시에 교란되고 유한PD/필터/접촉 동역학이 작용하므로 독립 index1_x의 미분부호나 force 인과방향은 알 수 없다. 이자료로 preload용 index1_x의 증감부호를 선택하면 추측이다.

## 240Hz 연속성과 해제 latch

음의 clean은 현재·직전 candidate 모두 참인240Hz 구간만 적산한다. candidate가 한 번 끊겨도 continuous clean_streak가 리셋된다. 원 left_fraction0.4에서 필요한 연속길이는 A4 0.06812초, B7 0.31116초, B8 0.13932초다. 따라서60Hz에서 관찰한 간헐적 unloaded만으로도 달성률이 평균 clean보다 더 민감할 수 있다. 이 감사는240Hz의 누락개수를 복원하지 않는다.

A released latch는 ever가 있고 음 끝 이후100ms 안에 candidate가 true→false로 변할 때만 켜진다. noisy가 음 끝 전에 이미 접촉을 잃어 계속 false면, 실제로 나중에 unloaded여도 latch가 안 켜질 수 있다. noisy의102/128해제를 나머지26손가락이 물리적으로 계속 눌렀다는 뜻으로 해석하지 않는다.4환경 N구간의loaded0/후보0 관찰과128개 latch 미달은 다른 측정이다.

## 다음 방향

실제 load 유지가 목표여야 한다. full joint range·기존 속도/0.25Nm effort cap·실제 접촉기준을 유지하고, 기존 candidate/상대속도/표면delta/높이·joint 관측을 사용하는 유한한 학습 보정으로 audible동안 안정적으로 누르고 음 끝 뒤 해제하도록 하는 방향이 맞다. 보상은 이미 clean hold·연속 streak와 실제해제를 측정하므로 기준을 낮추거나 탐색범위를 좁히는 해법부터 선택할 근거가 없다.

preload는 검토할 물리적 가설이다. 실제 접촉면 법선 방향으로 유한 목표 여유를 확보하면0하중 토글을 줄일 가능성이 있다. 그러나 현재자료만으로 필요한 mm/각도/축부호를 정할 수 없다. 실제 surface Jacobian 또는 독립 native 응답으로 inward 방향을 확인한 뒤 유한 preload 한값을 선언해 원접촉·해제·실패·effort조건으로 검증해야 한다. 깊은 침투나 큰 힘 자체를 보상하지 않고, 안정적 유한하중과 해제를 함께 학습하는 것이 목적이다. 이 감사에서는 추가 GPU/격자/잡음삭제 실험을 실행하지 않았다.

`audit.py`는 CPU 재현만 수행한다. `analysis.json`은 모든 audible끝점·그룹별범위·상관·source mapping을, `verification.json`은 입력14파일의 전후SHA256과5개 자체검사 통과를 보존한다. 원소스·봉인입력·V2산출은 변경하지 않았다.
