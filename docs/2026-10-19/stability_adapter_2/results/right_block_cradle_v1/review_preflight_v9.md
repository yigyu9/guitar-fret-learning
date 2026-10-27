# 사전 검수 — Thorax 접근량8mm와 가상 요청20N

요약 판정: **문제없음. Critical 0 / Warning 2 / Suggestion 0.** 지정 static_Thorax20 설정의 bounded5초 진단을 막는 추가 코드 오류는 발견하지 않았다. 실제 두 블록 접촉·작은 몸통 변화·팔꿈치 독립성은 미검증이다.

- config는 같은 candidate/reference/body150/1·초기81/G·left task·33EFFORT/48POSITION을 유지한다. 변경은 proximal_point_parameters의 R_Thorax cap20N/depth.008m, R_Shoulder cap10N/depth.004m다. 이전 Shoulder 조건은 그대로다.
- [helper4](/home/ajou/yigyu/3/stability_adapter_2/right_block_effort_v4.py:29)는 각 reference의 depth로 초기G-local 목표를 계산하고 해당 cap로 force norm을 제한한다. 두 점 모두20N으로 바꾸지 않는다. currentG 목표/COM 속도·3/6 Jᵀ·old task 감산·body9 task·native effort cap·단일human81/원guard는 이전 제어와 같다. bodyhelper3/runner7은 새 부모 import만 변경한다.
- [분석기5](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_block_cradle_v5.py:69)는 각 reference cap로 force를 재계산한다. BODY9 scalar 최대는240Hz body_rows와최종 state를 포함해.08rad 기준을 검사하고60Hz 최대/Chest world 회전 최대를 별도로 저장한다. 원 raw projection과 endpoint-clamped 접촉 분류도 구분한다. 실제 최종33 effort/48 POSITION 감사 경로를 유지한다. 이 분석 코드의 실제 실행 결과는 아직 검수하지 않았다.
- 계획·helper4/bodyhelper3/runner7/분석기5 AST와 config 차이를 확인했다. 원 소비 source/실패/이전 조건을 수정하지 않았다.

Warning 1 —8mm는 인간 motor 목표의 inward offset이며 실제 관통깊이·접촉력 측정이 아니다.20N과 Shoulder10N은 각 가상 요청 cap이고 최종 관절 cap은 별도다. 접근량과 cap을 동시에 변경하므로 효과를 어느 한 parameter만의 인과 결과로 단정하지 않는다.

Warning 2 — source 근접·상완 접촉 또는 body scalar.08rad 기준만으로 오른 두 블록만의 받침을 인증할 수 없다. 두 부위의 실제 동시 접촉/양성 rawlambda·근위영역·왼thumb/허벅지 관여·G 중심/SO3 및 같은 초기/제어의 elbow 동작 비교를 함께 확인해야 한다.240Hz 최대도 solver 내부 연속 최대가 아니며 scalar q 변화와 world 몸통 회전은 다른 양이다.

검수는 변경 코드/계획·per-reference 설정·선언된 분석 수식/AST에 한정했다. 추가 native/학습/추론과 다른 담당 파일 편집은0이다.

검수 SHA256:

- 계획V7: `0ff448f101e6272e053498c3e9f3a8b583334343bb2b2be5b9b5de142c1b785b`
- point helper4: `7e4069dde8330d56c08a7e51a66ce7e86f4f1e1da2ab4f8201d7d6fd3e0d3810`
- body helper3: `0d30700a58b69861e67aac8188db41b3c31deecd53c196290436aecf7db07e5a`
- runner7: `80108d29f7efb6da1ed579890fe7e9196d9463a1fcaa6afd64e595535c6776e2`
- 분석기5: `20a5a578d0e743080b479734d9b649c2341b6043e0b0f53335865aa1ffc0a5b6`
- config: `07f50f05190431f3f06a4f78889f869ac7311529a0db8e8c6bff569e43e558f5`
