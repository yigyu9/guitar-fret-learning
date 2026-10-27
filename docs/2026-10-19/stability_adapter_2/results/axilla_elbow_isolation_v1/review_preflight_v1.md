# 겨드랑이·팔꿈치 분리 source 사전 검수

판정: **문제없음 — 두 source 거절 유지, native 진행 후보 없음.** Critical 0 / Warning 1 / Suggestion 0. 변경 계획·source 코드와 저장 결과를 읽고 수치/문법/해시만 확인했다. 신규 native·학습은 실행하지 않았다. 실행 runner/분석기는 이 검수 시점에 제공되지 않아 제어·운동 단계 승인은 포함하지 않는다.

- [회전 구성:30](/home/ajou/yigyu/3/stability_adapter_2/search_axilla_elbow_isolation_v1.py:30): 기타 BB 중심을 기준으로 front 축 회전한 뒤 중심 변위를 적용하는 `centreW + delta - rot·centre` 식이 맞다. 현재 초기 front world `(0,1,0)`에서 +8° 회전은 실제 G+Y 목 고도 +8°이며 앞판 normal을 유지한다. root 변위와 중심 변위는 다르다.
- [범위·mask:19](/home/ajou/yigyu/3/stability_adapter_2/search_axilla_elbow_isolation_v1.py:19): body9/head6/right12만 조절하고 나머지54 scalar를 고정한다. 각 그룹은 원 자연 초기값 주변 범위와 모델 한계의 교집합을 사용한다. 분산 몸통 world 목표·Head world 보정·기타 source 변환 후 audit 및 전체 analytic 캡슐 검사를 적용한다. native용 후보에는 genuine FK poses와 새 config의 후보 SHA를 저장하는 경로가 있다.
- [수락 gate:36](/home/ajou/yigyu/3/stability_adapter_2/search_axilla_elbow_isolation_v1.py:36)와 [최종 source 결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/search_v1/search.json)를 대조했다. 두 조건 source_clear=true여도 아래 실패를 그대로 거절했다. `selected=[]`, `native_runs=0`이 정확하며 입력 609개 SHA 현재 불일치 0이다.

| 후보 | 근위 0~30% source gap | 전완 gap | R_Thorax gap (8mm 미만 필요) | 팔꿈치 하방 거리 (20mm 이상 필요) |
|---|---:|---:|---:|---:|
| bend8_cradle | 1.411157mm | 14.511534mm | 34.042266mm | 15.514935mm |
| bend11_cradle | 1.361175mm | 16.209974mm | 31.252763mm | 12.639594mm |

Warning 1 — [제어·진단 계획:13](/home/ajou/yigyu/3/stability_adapter_2/AXILLA_ELBOW_ISOLATION_PLAN_V1.md:13): 상완 Jacobian의 Elbow/Wrist 열 0은 직접 기구학적 결합에 관한 검사이며, 관절 중력·자세 토크·질량/접촉을 통한 간접 영향 제거를 뜻하지 않는다. source 전완 간격과 근위 접근도 실제 cooked 접촉·힘·운동 강건성 인증이 아니다. 정지 native 조건을 통과한 뒤 실제 팔꿈치 추종량과 같은 시간의 정지 대비 기타 변화를 대조해야 한다. 현재는 native 후보가 없으므로 그 효과를 평가할 단계가 아니다.

검수 SHA256: PLAN1 `ff82420bfe3a2d186de5fb6234376bccf8141af27af0a79b6fe948cae38d3355`; source1 `1544bd1f8e9402a2211f47708421b6f09004749dcdd28021ba276c1ff1412ca1`.
