# 분석기 사전 검수 — 정지/현재G 두 점/팔꿈치 비교

요약 판정: **수정 권장. 실행 차단 Critical 0 / Warning 3 / Suggestion 1.** 분석기2의 현재G 목표/속도·두 task 합산·old task 제거·최종 clip 경로는 정합적이다. 아래 분류·필드명·독립 검증 범위를 제한해야 하며 native 유지 성공이나 분석 실행 완료를 인증하는 판정은 아니다.

- [입력:22](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_block_cradle_v2.py:22)은 선택 native 폴더 파일/실행 attempt의 계약·형상·소스 해시와 Python 의존성을 검사하고 종료 후 다시 pin을 확인한다. 기존 정지는 thorax_point_rows, 새 현재G 조건은 two_block_rows를 별도 분기로 읽는다. 원본 파일을 수정하지 않고 새 출력 경로에 저장한다.
- [동적 분기:55](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_block_cradle_v2.py:55)는 k=0 초기 상태, k>0 직전 endpoint 상태를 사용해 제어 직전 기타/인간 point와 COM 속도를 재계산한다. currentG goal/velocity·K/D force norm cap·Jᵀ3/6 task·old fixed-shoulder task 감산과 right12 clip을 검증하고 tracking의 최종81과 exact 대조한다. static branch의 Thorax 합산도 별도로 유지한다.
- 1200physics/300control·301trace·240Hz endpoint 순서·57 POSITION/state·24 owner/model cap·scalar elbow wave target·151frame30fps·입력 불변을 확인하도록 되어 있다. 기타 BB 중심/SO3와 같은 시각 static 차이 공식은 body root quaternion의 normalized rotation과 source collision-body bbox centre를 사용한다. 새 분석기 AST 검사는 통과했다.

Warning 1 — [접촉 영역:109](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_block_cradle_v2.py:109)의 proximal30/35는 raw local contact point의 축 투영 f에 `0≤f≤.3/.35`를 적용한다. source analytic 부분캡슐은 closest-axis fraction을 endpoint에 clamp하여 근위 반구도 포함하므로 raw f<0인 접촉이 여기서는 제외된다. 의도된 raw projection window라고 명시하거나 새 버전에서 clamped fraction 규약과 맞춰야 한다. 실제 source 근위 전체/겨드랑이 접촉 인증으로 확대하지 않는다.

Warning 2 — dynamic branch에서 force_norms는 Thorax와 Shoulder 두 요청을 함께 모은다. 출력 max_Thorax_virtual_force_request_N은 Thorax 단독 최대가 아니라 두 요청 중 최대다. 이름/설명을 '두점 요청 최대'로 제한하거나 새 버전에서 개별 최대를 분리해야 한다. 둘 다 각각10N cap이라는 물리 제어 조건에는 영향이 없다.

Warning 3 — native point/velocity는 raw endpoint로 재계산하지만 J 속도오차는 저장된 jacobian_velocity_error 값≤.01 여부만 확인한다. independent `norm(J*qdot−velocity)` 재계산 통과라고 부를 수는 없다. 저장된 right row의 qdot_all_rad_s로 새 분석 버전에서 계산/기존 error 대조가 가능하다. 기존 runtime guard가 시행됐다는 사실과 오프라인 독립 재계산을 구분한다. 부모의 gravity/left scalar·wrist 제어 전체를 새 분석이 처음부터 독립 인증한 것으로 확대하지 않는다.

Suggestion 1 — motion의 static match는 현재 cap/currentG flag가 같은 첫 조건을 선택하고 full initial/first2.5s exact assert로 fail-safe 거절한다. 현재 유일한 dynamic body4 static에는 맞지만 같은 cap의 body PD 조건이 여러 개라면 적합한 static이 뒤에 있어도 먼저 잘못 고른 뒤 실패할 수 있다. 이후 범위를 늘릴 때 config/PD/전체 initial 일치로 정확히 한 쌍을 선택하는 편이 명확하다.

검수는 분석기2 코드·실제 기존 기록 schema·점/속도/토크/회전 공식·AST에 한정했다. 분석기 실행·새 native/추론/학습과 다른 담당 파일 수정은 하지 않았다. 수정이 필요하면 입력에 소비된 분석기2는 보존하고 새 버전을 사용해야 한다.

검수 SHA256: `fe3079a01711e425e990abb37e50ac17e338850830407bac4459f5a2a2bcbba3`.
