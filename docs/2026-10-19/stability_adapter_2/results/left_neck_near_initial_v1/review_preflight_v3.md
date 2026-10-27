# 사전 코드 검수 보완 — 실제 초기 pose의 source 재감사

요약 판정: **문제없음.** 추가 Critical 0 / Warning 1 / Suggestion 0. 새 실행용runner2의 초기 재감사와 소비본 분리는 정합하다. 아직 source2 후보 계산 중이므로 native 후보 수락/결과 성공은 승인하지 않는다.

- [runner2:93](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v2.py:93)은 actual native 초기전체state0와 현재OM 자산으로 기존source_scene/source_audit를 실행한다. human XML에서 구성한 parent-map은 기존 비인접 body tree 규약과 맞다. [runner2:97](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v2.py:97)의 native state exact 불변 assertion, 초기audit 기록 및 [runner2:124](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v2.py:124)의 source_clear gate가 함께 추가됐다. 기존FK/face/PD/mass 및 fixed48/G초기 검사도 유지한다.
- diff는 이 readonly초기audit·기록·gate뿐이며 인간/기타pose·q/속도·controller/gain·single owner·물리/setter 변경이 없다. 초기capture 뒤 거절하는 기존경로도 그대로다. 새runner2 AST 통과.
- [분리 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/runner_preflight_version_v1.json:1)의 원runner1을 직접SHA대조했다. source2 inputs_before에 원runner1의207066… SHA가 있고 현재bytes와 exact다. 새runner2는 당시source 입력목록에 없으며 전체현재source2 입력SHA 불일치0이다. 임시 원파일 변경을 최종소비본 수정으로 남기지 않고 exact 복원/별도추가로 분리했다. native 실행은 아직0이다.

Warning 1 — actual native **pose**를 입력으로 사용해도 거리/교차판정은 기존 convex source proxy다. PhysX cooked 비접촉·선택facet의해부학적pad·연속시간 contact 인증은 아니다. 후보수락/최종float32모델·고정48·원면gap 및 실제초기/5초/pair 실패판정은 결과가 나오는대로 별도 검수해야 한다. 기존[사전 검수1](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/review_preflight_v1.md:1)/[검수2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/review_preflight_v2.md:1)의 scope도 유지한다.

추가 source/native/정책추론/학습·기존소스 수정0. 코드 diff·기록·입력경계만 읽기 검수하고 소유한 새 리뷰만 작성했다.

검수 SHA256:

- 보존runner1: `20706636076b71bd44cb6a792e9e8e268695f5380ff698565a31b4ded2a63a7d`
- 새 실행runner2: `1337e4a462be2e49331632198590096a8645f48d200703613f5d45780cae91cb`
