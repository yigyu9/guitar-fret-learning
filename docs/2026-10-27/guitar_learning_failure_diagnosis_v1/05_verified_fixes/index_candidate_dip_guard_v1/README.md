# 검지 candidate 중 DIP 양의 목표증분 억제

root 승인 PLAN의 두 조건만 실행한다. 원 B300 strict/fresh=False·128cap 검증·원 evaluator/compact_episode와 source핀 경로를 재사용한다. GPU는 root만 실행한다. active/B producer/봉인/원자료를 수정하지 않는다.

`passthrough`와 `candidate_dip_no_positive_increment`는 closed-loop 비교다. current candidate & ~wrong인 유효 first-attempt 행에서만 DIP의 추가 양의 target증분을0으로 한다. 음/0증분·다른104열은 원함수의 같은snapshot 결과와exact다. 실제q를 덮어쓰거나 억제한증분을 재누적하지 않는다. body 합력/자연스러움/학습·free-guitar 효과는 인증하지 않는다.

CPU 준비: `probe.py --self-test`, `probe.py --prepare`. 두 GPU 명령은 독립 준비검수·최종 봉인 뒤 `cpu_inputs/commands.json`에 있는 `probe.py --execute passthrough`, `probe.py --execute candidate_dip_no_positive_increment`이다. 출력은 새 `runs/<condition>/`이며 기존 경로/symlink는 gate/native import 전에 거부한다.

기존 source/model/strict loader를 그대로 두고 실행개입은 `execution_override.json`에 별도 선언한다. 원 `evaluation.json`의 policy_performance 필드는 원 evaluator의 출력으로 보존하지만 개입 run을 무개입 정책성과로 해석하지 않는다. `dip_control60.npz`는 전128의 first_attempt mask/clock/candidate/wrong/gate/old·raw·final DIP/검증잔차만 담는다. 완료 뒤 retry는 mask=False이고 집계에서 제외한다. 일반실패 endpoint는 first=True/post_failure=True로 남는다. step 예외로 미완료된 control이 있으면 별도 `dip_aborted_control.npz`이며 정상 endpoint로 집계하지 않는다. 상세body/q/force는 원 env0 trace뿐이다.

`dip_guard_report.json`은 model/RNG/updates 불변·scoped복원/오류를 기록한다. 원 base diagnostic_report/report/input-before/after·128×105 cap·90pair 검증/sceneclose는 덮어쓰지 않는다. 다음실제분석은256전체 첫시도/실패와 원9보상, 음전/음중/음후 PIP/DIP·motion·손목·합력, 개입지속/펴짐명령통과를 비교해야 한다. 새 passthrough와 기존 B300의 ledger/trace 차이도 보존한다. 현재 native/성과는 아직 미검증이다.
