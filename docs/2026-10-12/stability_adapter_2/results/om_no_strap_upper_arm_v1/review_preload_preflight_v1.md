# 오른팔 preload·PI 사전 검수

판정: **문제없음 — 실행용 runner v6/계획 V6·V7의 제한된 네 번째5초 진단을 막는 Critical 없음.** 미결 Critical 0건, Warning 1건, Suggestion 0건. 기존 v5 기록 오류는 보존된 새 v6에서 해결됐다. 읽기 전용 코드/입력 및 순수 수치·인메모리 AST 반례를 확인했으며 추가 native·학습·원본 수정 없이 이 리뷰만 작성했다.

[목표 IK:29](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v6.py:29)는 초기 subset 기준점의 body-local 좌표를 고정하고 초기 기타 source 표면의 normal 안쪽8mm를 희망점으로 사용한다. 오른팔12 목표만 q_ref±0.12rad∩effective/native 한계에서 계산하며 점 오차2mm 이상이면 거절한다. 실제 초기 q·기타 p/q를 덮어쓰지 않는다. subset에서 구한 기준점은 전체 capsule 표면보다 약0.258600mm 안쪽일 수 있음을 순수 기하로 확인했으며, V7와 `reference_point_scope`는 이를 body-local motor 기준점으로 정확히 제한한다. 실제 contact point·관통8mm·측정 압력은 아니다.

[제어:47](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v6.py:47)는 원 neutral monitor를 한 번 호출해 상태 로그만 남긴 뒤 반환 constant action을 버리고 PI action 하나를 반환한다. Kp1/Ki1/s·dt1/60 적분과 오른팔12 residual/integral±0.4rad clamp, 나머지69개 보정0, absolute goal+residual의 effective/native clip·정규화·기존 단일 contract.targets/rate/4physics 경로를 확인했다. 실제 제출 target은 다음 trace 행과 대응한다. 기존240Hz 관측·strap OFF·left parked·카메라/read-state 불변 검사도 유지된다.

[필터 읽기:40](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v6.py:40)는 실제 actor body shape ranges/filter를 읽고 R_Shoulder shape 존재·G:body63개·각 mask AND0을 검사한다. 새 v6는 assert 전에 raw filter 파일을 저장해 차단 근거를 보존하며 property setter는 없다. mask 검사 통과만으로 실제 접촉·지지력 형성을 인증하지 않는다.

기록 정정: 기존 v5는 상속 metadata의 마지막 단계에서 attempt.control이 constantPD로 덮였다. [v6 final_save:14](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v6.py:14)는 patch 전 원 save를 보존하고 최종 기록 직전에 실제 preload+rightPI+armrate3를 명시한다. 실제 AST 함수 체인을 인메모리 spy로 호출해 단일 save·올바른 control·공유 closure V6/V7 SHA 추가를 확인했다. 재귀나 실행 후 출력 수정은 없다. 사전 입력 두 기록(3개+2개 파일)은 현재 SHA와 일치하며 config 차이는 arm rate1→3뿐이다.

Warning 1건:

- [계획 V6:9](/home/ajou/yigyu/3/stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V6.md:9): preload 목표·PI·팔 rate를 함께 바꾼다. 단독 효과로 귀속하지 않으며, 현재 기타 frame에 대한 지지점 feedback도 아니다. 초기 world 희망점에서 정한 관절목표를 추종하므로 몸통/기타가 움직이면 실제 기준점 관계가 달라질 수 있다. 실제 left 비접촉·right 접촉·기타 최대/종료 이동/SO3를 함께 판단한다.

Critical: 없음. Suggestion: 없음. 초기 state/PD/질량·forcecall0·shape readback·IK 오차·실제 target/rate·속도·endpoint·보존은 native 결과에서 확인할 범위이며 압력·안정·연주 성공은 미리 승인하지 않는다.

검수 SHA256: 실행용 v6 `062c741a193930fff027292b03d2219262d2f6bf0ef44c985d489680e58f87f9`; 기록 보완 계획 V7 `398c17ccfdb2eb3b5d9428c353690c37ccd8108b0b855073b4b3b6886b1fe034`.
