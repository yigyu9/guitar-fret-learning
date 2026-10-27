# Root 고정 전신 관절 제어 계약 검수

2026-10-15. change-reviewer가 신규 music_pipeline_v3/control.py·test_control.py, 구현 계획, 결과 README와 root의 CPU 검증 기록을 읽기 전용으로 검수했다. 본 검수 파일만 작성했다. 구현·기존 자산·소비된 소스·과거 결과는 수정하지 않았으며 테스트나 native를 직접 실행하지 않았다.

## 요약 판정

문제없음. 현재105채널 목표/유한 PD 명령의 CPU 계약 범위에서 미해결 Critical 또는 Warning을 발견하지 못했다. 새 사용자 방향에 맞는 인터페이스 준비이며 실제 root-only-fixed native 환경 전환이나 전신 지지 성능이 검증된 결과는 아니다.

## 구현 확인

- [이름·역할 계약](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v3/control.py:13)은 기존 상체81 이름과 양쪽 Hip/Knee/Ankle/Toe의24개를 합친 정확한105개 집합을 요구한다. root와81개 입력을 거부한다. 정책 목표39개와 기준 자세 유지 목표66개가 겹치지 않는다. 상체의42개 유지 목표에 하체24개가 추가되며, 정책 출력 자체를105개로 늘린 것은 아니다.
- [상체 변환 재사용](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v3/control.py:55)은 제공된 native 이름 순서에서 upper81을 추출해 동결된 v2 codec에 전달하고 결과를 같은 인덱스에 다시 배치한다. 기존39행동의 범위·평활화·rate cap이 유지된다. 하체를 포함한 held66은 외부105차원 q_ref를 그대로 목표로 사용하고, 이전 목표가 오염되면 거부한다. 실제 q/state를 덮어쓰는 기능은 없다.
- [외부 제어 파라미터](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v3/control.py:40)는 q_ref·native 한계·rate·Kp/Kd·effort limit 전체105개를 요구한다. 기준각이 native 범위를 벗어나거나 Kp/effort가 양수가 아니거나 Kd가 음수인 경우를 거부한다. 하체 기준각을0으로 채우거나 새 자세를 자동 선정하지 않는다. metadata에 전체 순서와 제어 파라미터·0범위 축을 남기고 외부 입력 배열 변경이 계약에 반영되지 않도록 복사·read-only 처리한다.
- [PD 명령](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v3/control.py:98)은105개 실제 scalar 각도·속도와 목표로 `clip(Kp*(target-q)-Kd*qdot, ±effort_limit)`을 계산한다. 일정 목표에서도 교란·속도에 따라 복원·감쇠 명령이 달라진다. 출력은 계산된 명령 Nm이며 측정 토크가 아니다. 유한 입력의 overflow는 유한 effort cap으로 포화하고 indeterminate NaN은 거부한다.
- [torques의 목표 검증](/home/ajou/yigyu/3/stability_adapter_2/music_pipeline_v3/control.py:105)은 held66의 정확한 기준각과 active39의 유효 범위를 확인한다. 사전 검수에서 확인된 active 범위 누락은 첫 CPU 실행 전에 root가 보완했고, 변조된 active target을 거부하는 회귀 검사가 포함됐다. 소비된 소스를 사후 수정한 결과가 아니다.

## 자산·채널 수의 의미

원본 [smpl_mpl_hands_body.xml](/home/ajou/yigyu/3/tab2body/assets/smpl_mpl_hands_body.xml)에는105개 named scalar joint와 별도의 Pelvis freejoint가 있다. 이번 계약의105개 출력에는 root가 없다. 하체24개 중 L/R Knee_y/z·Toe_y/z의8개는 원래 range=0이며, 이를 허용해 anatomical limit을 보존한다.

**105개 목표/명령 채널과97개 비영 가동 범위를 구분해야 한다.** 0범위8축을 새로 자유화하거나105개 모두 독립적으로 움직이는 축이라고 주장하지 않는다. 실제 native importer의 이름·한계·채널 수는 후속 연결에서 다시 확인해야 한다. XML 구조 확인만으로 native DOF·PhysX 접촉·실제 전신 가동을 인증하지 않는다.

기존 fixed-lower는 기록된 하체 링크 변환을 baked한 별도 자산이다. 원본에 상체81 각도만 복사하고 하체0을 채우면 이전 자세가 재현된다는 주장은 없다. 새105차원 초기 상태와 root 기준 몸·발·기타 배치의 대조가 필요하다는 문서 설명이 맞다.

## 실제 검증 기록

[cpu_v1/result.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wholebody_control_v1/cpu_v1/result.json)과 tests.log에서5개 테스트 통과를 확인했다. XML 이름/0범위, 이름 순서 변경,39/66 소유권, 하체를 포함한 복원·감쇠·포화, 입력 오류와 held/active 목표 오염, copy/read-only 및 유한 출력 조건을 검사한다. 기준각·gain·교란은 합성 fixture이며 물리 제어기 튜닝 결과가 아니다.

사전/사후 입력46개 SHA map이 같았고, 현재 파일 digest를 독립 대조해 모두 사전 값과 일치했다. 원본 human XML과 선언된37개 mesh가 포함되어 있다. root의 보존 wrapper는 이전 음악 파이프라인55개 입력과 기존 native1,333개 입력도 변경 없음을 확인했다. 새로운 native 실행은0회다.

## 문서와 후속 연결 범위

[결과 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wholebody_control_v1/README.md)는 다음 경계를 명확히 한다.

- root만 전역 고정하는 조건은 새 native adapter가 구현·검증해야 한다. 원본 Pelvis freejoint나 현재 fixed-lower 실행을 이번 CPU 모듈이 실제로 전환한 것은 아니다.
- held 목표에 대한 전신 feedback과 모든 관절 목표를 RL이 결정하는 전신 학습은 다르다. 현재 정책 권한은39개이며 나머지66개는 기준 자세 추종이다.
- 유한 PD는 중력·접촉의 정상상태 오차와 effort 포화로 자세 유지에 실패할 수 있다. CPU 토크 식과 native solver의 position PD가 동일하다고 가정하거나 두 경로를 중복 적용하지 않는다. 실제 drive mode·추종 오차·포화·명령/측정 토크·기타 지지는 후속 측정 항목이다.
- root는 외부 반력을 제공하므로 자유 보행·부유 root 균형 성과로 확대하지 않는다. 원래0범위8축도 실질적인 운동 제어 기여로 집계하지 않는다.
- 기존81채널 checkpoint와 같은 제어 계약으로 재개하지 않고 새 control metadata·105차원 실제 상태·reset·관측 ABI를 확정해야 한다. 과거 fixed-lower 안정성·음악 결과는 그대로 이전 조건의 결과다.

현재 논문 설명은 root-fixed 전신 제어를 목표로 하는 구조와 CPU 계약 구현에 한정한다. Methodology 후보 문장은 실제 native 연결·검증 후 사용하도록 구분되어 있으며, 이번 테스트를 실제 전신 연주·지지 성공으로 과장하지 않는다. 이 범위에서 최종 보존 감사 진행을 막는 사항은 없다.
