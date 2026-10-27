# 사전 검수 — 오른 어깨에서 팔을 조금 앞으로

요약 판정: **문제없음.** canonical source2의20mm 후보 정지5초 진단에 추가 실행 차단은 없다. Critical 0 / Warning 1 / Suggestion 0. source1 두 후보는 미수락·미채택으로 보존한다.

- [source2:18](/home/ajou/yigyu/3/stability_adapter_2/search_shoulder_forward_v2.py:18)의 변수는 R_Shoulder3이며 현재19° 기준±.12rad와 모델 한계 교집합이다. 두 저장 후보의 나머지78 scalar 및 기타초기 p/q list가 seed와 exact다. genuine FK와 저장 pose 재대조 최대 위치오차2.26e−16m, 모델 한계·각도 범위를 통과했다. 기타 앞판의 수평 normal은 world+Y다. Shoulder suffix를 world 회전축으로 설명하지 않는다.
- [source2:25](/home/ajou/yigyu/3/stability_adapter_2/search_shoulder_forward_v2.py:25)는 어깨 원호를 고려해 전방 projection을 목표로 하고 직교변위를 최소화한다. [source2:26](/home/ajou/yigyu/3/stability_adapter_2/search_shoulder_forward_v2.py:26)의 새 gate는 전방오차<2mm/직교변위<12mm다. 재계산한20mm 후보는 전방19.749420mm/오차 .250580mm/직교8.445535mm,10mm는9.893096mm/오차 .106904mm/직교4.002326mm다. sourceclear·전체 capsule≥.05mm·근위30%<3mm·전완≥12mm도 통과한다.
- [source2:27](/home/ajou/yigyu/3/stability_adapter_2/search_shoulder_forward_v2.py:27)는 변경된 팔에 부정확했던 기존 right12각/bounds/posture_shape/hand error를 제거하고 현재shoulder bounds·delta·오차 정의·직교·palm 변위를 저장한다. source1의3D 목표오차3.726275/7.757456mm 거절을 성공으로 바꾸지 않고 새 계획/출력으로 구분했다.
- [runner2:13](/home/ajou/yigyu/3/stability_adapter_2/run_shoulder_forward_v2.py:13)와 [runner2:133](/home/ajou/yigyu/3/stability_adapter_2/run_shoulder_forward_v2.py:133)은 현재PLAN2/search2를 연결한다. 직전upright runner와 비교해 phase/계획/search 경로 외 controller/guards는 같다. 인간상완 초기world점 cap10N·forearm force0·right12 EFFORT/other69 POSITION·root/하체 고정·strap OFF·자유 기타·single torque owner·mixed readback/state guard를 유지한다. 직접 기타 force/attachment/실행중 state write가 추가되지 않았다.

Warning 1 — [계획V2:3](/home/ajou/yigyu/3/stability_adapter_2/SHOULDER_FORWARD_PLAN_V2.md:3)의 전방 projection 오차는 이전3D 목표오차와 다르다. 전방19.75mm에 직교8.45mm가 동반되므로 정확한20mm 평행이동으로 표현하지 않아야 한다. 어깨 원점은 source에서 그대로이고 초기 어깨 회전이 팔을 이동시킨 것이다. 고정78 scalar는 Shoulder 아래 Elbow/Wrist/손의 world pose 고정을 뜻하지 않는다. source clearance는 native cooked·지속 접촉·지지력 인증이 아니며 actual 초기/종료 elbow·palm 및 이전19° 비교·기타/접촉 gate는 후속 native 결과에서 판단해야 한다.

검증 범위: 입력633 SHA 현재 일치, config→candidate SHA 일치, 관련Python3개 AST 및 FK/변위/고정·모델 대조. 추가 native/학습/소스·기존 파일 수정0. root가 시작한 native의 결과 판정은 포함하지 않는다.

검수 SHA256:

- 계획V2: `a4c81bdfeda69a711138400ca93d90471757e48b2afa72a60626a6a60748d25c`
- source2: `3215b245ebd585c3533021369dddff9eac667f061954fd4f0c3627445ce92b02`
- runner2: `2d7c63d0cfb91c313795dbeb518572a8f17e49d86680284be73c2cf09b742a9e`
- analyzer1: `e1670fb50a9c8a100afa57ce4921819c53763a4f304ab1c7bc226540f5c764f3`
- search2 JSON: `20334d0ebb09ee7cf5b47361195f15fd2d3f9220a45f48440e801093409333ad`
- 20mm candidate: `85ba4aeee67928bcd004291a28ddfbba1c744806f4c1105f17d479f7b04e9023`
- 20mm config: `76b9e81686a590b15f341da68e29fb7b06b30855a05f7452d65250f98eb8badb`
