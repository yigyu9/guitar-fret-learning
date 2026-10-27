# 초기 자세 탐색 V2 source·V3 native 진입 검수

요약 판정: **문제없음 — 현재 생성된 적합 후보의 native 진입 계약 기준**. Critical 0건, Warning 0건. 실제 지지·잡기/해제·타현 안정성은 아직 이 사전 검수로 인증하지 않는다.

## 변경과 수학

- V1의 실제 보존된4개 audit는 Torso/Spine–L_Shoulder source 자체교차 때문에 탈락했으며 물리는0회다. 원본/partial/before/interrupted는 유지한다. [V2](/home/ajou/yigyu/3/stability_adapter_2/search_initial_pose_v2.py:35)는 같은 후보 범위·고정G좌표손목 A/회전·gain에서 왼쪽 상완–Torso/Spine capsule 회피만 추가했다.
- 각 capsule fromto 두 점을 해당 body native-calibrated FK pose로 world 변환한다. `M=[a1−a0,−(b1−b0)]`, `d=b0−a0`에 대한 `min||M*[u,v]−d||`,0≤u,v≤1은 두 유한 선분의 최단거리다. 결과에서 두 반지름을 빼므로 양수는 분리 간격이다. 축부호·좌표변환·반지름의 사용이 맞다.
- 평행 선분을 포함한300개 독립 사례에서 lsq_linear 결과를 모든 경계 최적해/내부 정상해의 최소값과 대조했다. 거리 최대 차이는7.19e−9m 미만이었다. IK residual은 gap1mm를 선호하고 최종 source eligibility는각gap>.2mm 및 기존전체 source_clear를 함께 요구한다. 실시간 힘을 추가하거나 source 검사를 cooked 연속 비관통 인증으로 바꾸지 않는다.
- 검수 시 생성 완료된 margin_only/roll_m2는 accepted/source_clear=true다. Torso/Spine gap은각각약[1.0000,1.4486]mm/[1.0000,1.0388]mm이고 L_Wrist_y 여유≈5°다. 후보별 candidate의 initial_pose_search와 해당 audit가 같다. source 전체7변형의 완료/선정 결과는 이후 report로 별도 확인해야 한다.

## V3 입력 봉인과 실행 범위

- V2 source before1,308개 입력은 현재 SHA와 전부 일치한다. 실제 human/G XML과 모든mesh106개·직접config/기하/helpers는 앞선 검수의 계약을 유지한다. V2 source와 V3 runner의 AST 문법 검사도 통과했다.
- [runner V3](/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_search_v3.py:30)는 아직 생성 중인 전체 search_v2/report.json 대신 불변 search_v2/inputs_before.json과 **해당 후보의 `<label>_audit.json`**, geometry addendum을 명시적으로 pin한다. cfg가 search_v2/<label>/config_*.json일 때 `cfg.parent.parent/(cfg.parent.name+'_audit.json')`이 정확한 실제 경로다. contract는 config/candidate/native reference를 직접 SHA로 묶으며 현재2개 후보 설정·candidate SHA가 맞다.
- 이 변경은 나머지 CPU 후보의 출력이 진행 중이어도 선택된 후보 입력을 독립적으로 닫는다. 전체7후보 report가 완료됐다고 주장하거나 아직 없는 파일을 봉인 근거로 사용하지 않는다. Geometry addendum은 V3 native before부터 명시 pin하며 V2 source before로 소급하지 않는다.
- V3는 V2 runner에 위 pinset 한줄만 바꿨고 물리/제어/카메라를 변경하지 않았다. source/runtime의 공통 A anchor `[0.0611697942,−0.0576772489,−0.0610080196]m`,G상대회전과 초기0.15 release가 맞다. 같은모델/gain/target rate/human effort cap·근위팔지지·root/하체불변·자유기타/무스트랩·자기충돌·안전중단을 유지한다. 새 기타 force/부착/상태 덮어쓰기 경로는 없다.
- 새 candidate를 static에서 실제 검사할 때 FK/모델한계/source proxy/속도0·고정lower 및 실제 LH/RH/support 접촉을 계속 확인해야 한다. source 성공이나 작은 간격만으로 왼손 독립지지/연주 준비 완료라고 부르지 않는다.

검수자는 이번 두 검수 문서 외에 소스·후보·기존 결과를 수정하지 않았다. GPU/native 물리를 실행하지 않았으며 root가 단계별 소수 시험을 관리한다.

## 검수 시점 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/search_initial_pose_v2.py`: `02da79c3a89b25df7dad7c246faf2449d8cb832824e8dcf76c7136e8807f8c51`
- `/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_search_v3.py`: `9f061dc30cecaaaaacc988eea631e5845c37b0af1170bc2f64a7dcd8b45f5b78`
- `/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_SEARCH_GEOMETRY_ADDENDUM_V1.md`: `afac8d5bd1cdd95294f086388bdf2bd8c1979a90063275491e989b7a926d7f30`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/search_v2/inputs_before.json`: `0a87b11d152e042574421d32f2def87047eee7035a8c5c2645f46df06f569593`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/search_v2/margin_only_audit.json`: `f653320429f1c12b546738a8d2a8a90d1a059be17e82c5f8e1ab0f5a604df2f8`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/search_v2/roll_m2_audit.json`: `52f73cea442cfceafb81008f812cac4e0a1a219777467cf9ed918065aa87e631`
