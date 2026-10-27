# 왼손 OFF source V2/V3 변경 검수

요약 판정: 문제없음. 목표방향과 최적화 여유 변경이 계획의 물리적 범위와 일치한다. 소비본을 수정하거나 source/native를 재실행하지 않았다.

Critical: 0

Warning: 1

- [PLAN_V3:1](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_OFF_CURRENT_PLAN_V3.md:1), [PLAN_V3:14](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_OFF_CURRENT_PLAN_V3.md:14): 복사된 V2제목과search_v2 출력경로가남아있다. **소비계획은 보존하고 후속기록에서 V3 실제출력search_v3와 :16의수치여유변경을 명확히 안내한다.** source가실제로잘못된경로에쓰는문제는아니다.

Suggestion: 0

- [sourceV2:43](/home/ajou/yigyu/3/stability_adapter_2/search_left_hand_off_current_v2.py:43): 목표는 −Gfront100/150mm, −humanright40/60mm,world−Z80/100mm다. right축은RHip−LHip이므로 휴머노이드왼쪽부호가맞다. source row의requested_forward는음수이고label은back100/150으로표기한다. 사람3mm검사두proxy 명칭을추가해 이전검수의scope경고도해결됐다.
- [sourceV3:48](/home/ajou/yigyu/3/stability_adapter_2/search_left_hand_off_current_v3.py:48): 변경은soft clearance목표3.0→3.1mm뿐이다. :57의hard≥3mm,LEFT활성geom20mm/query0,전체sourceclear·capsule0.05mm·palm오차5mm·모델한계·frozen69 gate는유지한다. 허용조건을epsilon으로완화한것이아니다.
- 실제V2두행은전체clear/LEFT근접0/frozen69임에도proxy2가2.999864/2.999996mm여서엄격gate에서거절된다. V3의proxy2는3.099988/3.100002mm이고두행수락이현재gate와맞다. 원V2와거절결과는보존됐다.
- V2/V3의모든후보각도를독립대조해 actualfrozen69 exact와native모델bounds통과를확인했다. source각입력989/990개SHA가현재파일과일치하고AST/소비source·계획SHA가맞다. V3candidate의G초기p/q와세cached오른지지metadata가baselineexact이며off flag=true다.
- runtime tracking-off/기존fourpatch와모든gain/가상요청cap·왼팔gravity/PD구조는 [이전검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/review_preflight_v1.md) 그대로다. t0왼손분리진단이며 실제G39/지원강체/69각과LEFTcontact0/추종force-task0·5초유지는 후속native검수대상이다.

- V2 source SHA256: `0483624b00f78a4ecefc41fe47e6c6ee425bd4801ff5357c9c195332a2a8b983`
- V2 plan SHA256: `274c62f741a7cfcdba549e39bd590cc1a80f7656f7a45b267132f21503215cea`
- V3 source SHA256: `7f9339dd2f412a2866d1a5d951852de02a06d25115b4709182298d68b730e61a`
- V3 plan SHA256: `d85cffe848df414c29b86e98d6dadcb1be2406d3038884215d13eb21b3ef2c12`
