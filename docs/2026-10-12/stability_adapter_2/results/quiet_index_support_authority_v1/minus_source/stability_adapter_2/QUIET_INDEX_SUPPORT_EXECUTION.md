# Quiet 검지 목표 응답 실행 범위

[제어권 계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_INDEX_SUPPORT_AUTHORITY_PLAN.md:1)의 두 조건만 실행한다. 초기 입력은 기존 `trials/initial_middle3_alignment_v1/middle3_initial_at_goal.json`을 그대로 읽는다. LH:index3 초기각은 0.12326771765947342 rad, 기본 held 목표는 0.1394716501235962 rad다. 기본 목표에 +0.005 또는 −0.005 rad를 2~2.5초 동안 선형으로 더하고 5초까지 유지한다. 60Hz 목표 합성 뒤 native float32 관절 한계를 검사하고 clipping하지 않는다. 기존 손목 sinusoid와 나머지 80관절 목표는 동일하다.

새 runner는 기존 5초 wrist runner를 별도 파일로 복사해 사용하며 기존 소스는 수정하지 않는다. 새 직접 초기 검사는 `run_source_hand_initial.audit_initial`을 재사용한다. 이전 제안의 FK `source_state`를 사용하지 않고 실제 초기 관절·body state로 검사한다. 원 quiet 초기81각, PD, root/하체, 기타 fullstate, LA를 대조한다. 원본 native 초기값과 report는 이전 봉인 inventory의 SHA로 확인한다.

입력 보존은 실제 읽는 데이터·새 leaf·원계획·trial·재귀 local import 소스·고정 모델 manifest와 그 입력·공용 자산/mesh·글꼴을 대상으로 한다. 이전 proposal에 누적된 14,015개 ancestry 경로를 새 trial마다 복제하지 않는다. 이는 이전 기록 삭제나 checkpoint qualification 우회가 아니며 기존 봉인 자료는 보존한다. 이번 새 runner는 이전 proposal의 hash map을 소비하지 않는다. 원 quiet 데이터와 runtime 입력의 SHA는 실행 전후 및 저장 사본으로 검증한다.

각 조건은 별도 명령으로 한 번만 실행하며 기존 log/inputs/invocation/output/실행결과가 있으면 재실행하지 않는다. 오류·SIGTERM·초기 gate 거절은 partial과 실제 step 수로 기록하고 자동으로 처음부터 재시작하지 않는다. 두 실행은 독립 초기화이며 연속된 10초로 연결하지 않는다. root/하체는 물리적으로 고정되고 기타는 자유 상태다. 기타 힘은 기존 수동 스트랩만 사용한다. 손 강제 부착·시작 후 pose/state 쓰기·actor/training은 없다.

1. 새 runner/wrapper AST와 독립 검수 → 초기/held 조합·ramp·other80·read-only 확인.
2. `run_quiet_index_support_phase plus`, 이어서 `minus` → 각 1회 초기화, 통과 시 1200step/151frame/스트랩 포함 두 카메라.
3. 저장된 명령/상태/trace의 0~2초 prefix exact, t5 world p/회전log 유한응답, 초기오차·후기변화·접촉/제약을 분석한다.
4. 결과 그림/영상과 실제 줄 색인을 추가하고 다음 보정 방향을 정한다. 성공·정식 자연스러움·연주 호환을 임의 선언하지 않는다.

실행 전 작성한 leaf다. 이후 상태 갱신은 main README/PLAN과 새 결과 기록에 추가하고, 소비된 이 문서는 수정하지 않는다.
