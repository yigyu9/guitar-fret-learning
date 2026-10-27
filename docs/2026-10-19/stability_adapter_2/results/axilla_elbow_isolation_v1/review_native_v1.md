# 정지·팔꿈치 운동 native 독립 검수

판정: **문제없음 — 한 초기값의 정지 및 ±2°/±5° 한 주기 진단 범위.** Critical 0 / Warning 2 / Suggestion 0. 저장 원자료와 코드의 CPU 수식·해시를 대조했으며 신규 물리·학습을 실행하지 않았다. 그림·최종 문서·전체 보존 봉인은 후속 최종 리뷰/root 감사 범위다.

## 실제 기록·진입 gate

- [분석 v2:24](/home/ajou/yigyu/3/stability_adapter_2/analyze_axilla_elbow_isolation_v2.py:24)의 초기 q81 exact를 유지하고 기타 위치의 float32 roundtrip 차이 5.960464e−8m(1 ULP)를 확인했다. 별도 명시된 norm<1e−7m 허용과 기록이 맞다. 앞선 출력 부모 폴더 부재/위치 exact assert 실패는 보존된 분석 실패이며 새 native 실패로 계산하지 않는다. 나머지 명령·상태 검사를 완화한 변경은 없다.
- 세 완료 기록은 각 1200 physics/300 control/5초·151프레임이며 forearm force0, right12 노력·모델 clip·물리당 단일 actor 제출/other69 POSITION readback/state guard를 유지했다. 1200개씩 상완 task+기록 gravity+posture 합산을 재계산하여 최대 8.89e−16Nm 차이/float32 제출 exact, child Jacobian 열 최대0을 확인했다. 이는 전체 gravity/Jacobian 독립 물리 인증은 아니다. native attempt 입력 882/884/885개 현재 SHA 불일치0, 영상 SHA 일치.
- [정지 gate:20](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/summarize_results_v1.py:20)를 raw trace/endpoint에서 독립 재계산해 true를 확인했다. 정지 BB 중심 이동1.621526mm/SO3 0.661582°, 2.5초 이후 최대 변화0.000552mm/0.000210°. 상완1187/1200, 오른 Hip1196/1200, 왼팔·손/Head/오른 원위 팔·손0/1200이며 R_Thorax도0이다. 마지막0.5초 상완120/120·2→2.5초 변화 기준도 통과한다.
- [운동 release:11](/home/ajou/yigyu/3/stability_adapter_2/prepare_axilla_elbow_motion_v1.py:11)는 실제 정지 gate와 후보 SHA를 확인하고 같은 후보에 운동 진폭·근거 경로/SHA만 추가한다. 5° 새 runner는 계획 경로·허용 진폭만 변경했고 모델 한계 안이다. 이 진입 기준은 임시 motion 진단 gate이며 안정 초기 자세의 일반 인증이 아니다.

## 같은 시간 운동 비교

세 조건의 전체 native 초기 state와 2.5초까지 trace exact를 직접 대조했다. [비교 v1:15](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/compare_elbow_motion_v1.py:15)의 동일 시각 정지 대비 응답·회전을 원자료로 재계산했다.

| 목표 진폭 | 실제 정지 대비 왕복 응답 | 명령과 상관 | 증분 추종 RMSE | 같은 시각 정지 대비 BB 최대 차이 | SO3 최대 차이 |
|---|---:|---:|---:|---:|---:|
| ±2° | 4.033391° | 0.999960914 | 0.016954° | 0.000976mm | 0.000402° |
| ±5° | 10.082998° | 0.999959880 | 0.042524° | 0.027241mm | 0.009348° |

두 운동의 sinusoid q 목표·해석적 목표 속도·posture·상완 요청힘·합산/clip을 240Hz 행에서 재현했다. 실제 운동에도 원위 오른팔/손·Head·왼팔/손 접촉0이다. ±5° 조건의 초기 대비 최종 BB 이동1.644817mm/SO3 0.670713°는 별도 지표다. 한 DOF·0.5Hz·한 주기의 이 모델/초기값에서 작은 영향이 관측됐다는 결론까지만 지지한다.

## 실제 근위 접촉과 해석 제한

Warning 1 — [지역 판정:22](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/analyze_contact_region_v1.py:22): source 기준은 **0~30%**이고 실제 classifier는 **0~35%**다. raw localPos+offset/world/G 좌표와 캡슐 축 투영을 재계산하여 세 조건 모두 35% 지정영역 presence1171/positive raw lambda1166, **30% 지정영역0/1200**을 확인했다. contact fraction 최소0.341293, feature pair 최대 약1.25e−7m/캡슐 반경 차이 최대0.610439mm로 기록과 일치한다. 35% 접촉을 30% 목표·해부학적 겨드랑이 접촉 성공으로 확대하지 않는다. endpoint 표본은 연속 solver 모든 접촉·힘/모멘트 기여를 인증하지 않는다.

Warning 2 — [응답 RMSE:15](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/compare_elbow_motion_v1.py:15): 이 값은 moving−static 실제 응답과 목표 증분의 오차다. absolute moving q−posture target RMSE와 다르며, 별도 재계산은 ±2° 약0.105367°/±5° 약0.108712°다. 새 비교 v2는 증분/절대 추종 정의를 구분했다. 큰 운동·다른 초기값·반복 강건성·연주로 일반화하지 않는다. J child 열0은 직접 기구학적 분리이며 간접 관성 영향 제거는 아니다.

핵심 SHA256: [2° 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/elbow_comparison_v1.json:1) `4041c9d03a31e14e8a8e7062b259e66ec67ba300c3cad44f956543f01e580f19`; [5° 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/elbow_comparison_v2.json:1) `97a3a8c51069929e2b57a40d15b9031bc06427d9af2b6053a9b09f5d6258c9e6`.
