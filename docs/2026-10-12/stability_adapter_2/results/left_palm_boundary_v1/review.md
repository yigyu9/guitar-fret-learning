# 왼손 초기 형상 간격 경계 비교 — 독립 통합 검수

검수일: 2026-10-07 KST. 별도 change-reviewer가 이번 입력·저장 실행·문서·미디어를 검수했다.
쓰기 범위는 이 파일뿐이며 원자료·코드·기존 동결 검수 기록을 수정하지 않았다.
새 native simulation, 초기 환경 생성, source geometry query는 실행하지 않았다.

**요약 판정: 문제없음. 남은 Critical / Warning / Suggestion 없음.**

## 초기 조건과 실행 범위

- [계획의 초기 범위](/home/ajou/yigyu/3/stability_adapter_2/LEFT_PALM_BOUNDARY_COMPARE.md:5)대로 기준 포함 8개 설정을 대조했다. 기준은 기존 설정과 byte가 같고 각 후보는 전체 105개 중 지정한 왼팔 한 축만 바뀌며 나머지 104개 q가 같다. native float32 반올림을 구분했다.
- 저장 C02 q와 native model bounds에 직접 대조해 full q가 기존 C02±0.3/model 교집합 안임을 확인했다. 기타 전체 초기 body state·목표 p/q, proximal 8개 body, PD 속성·cap·solver·route/절대 LA가 유지됐다. 초기 DOF q는 목표와 같고 속도는 0이다.
- 초기 검사 68개 SHA가 현재 파일과 같다. 8개 계약 검사와 LH 위쪽 반구·국소 높이·projection/source gate를 저장 검사값에서 재판정했다. L_Elbow_y−0.003125와 L_Wrist_y−0.0375는 각각 음수 pair 2개로 거부됐으며 native 실행 목록에 없다.
- 기준 포함 통과 6조건의 ON 18회, 선정 2조건의 OFF 6회만 실행됐다. 명시 command 경로·개수와 실제 24개 run이 정확히 같다. 실제 symlink 3개가 기록된 원본으로 해석되고 각 기간 기준 raw5는 원본과 같다.
- audit/comparator/plotter/runner/PI 다섯 재사용 파일은 직전 frozen source 사본과 byte가 같다. 새 controller, gain, gate, model 또는 목표 변경은 없다.

## 독립 저장 자료 검증

- 24개 run의 3,072 physics samples를 읽고 ON의 PI update 576회를 구현 호출 없이 별도 수식으로 계산했다. e=q_ref−q, 적분·최종 clipping·조건부 rollback과 blocked/saturated를 포함한 여섯 저장 벡터가 정확히 같다. 60Hz update 사이 기록은 유지되며 native float32 최종 목표는 허용 오차 안에서 같다.
- OFF는 보정·적분·포화가 0이고 초기 arm 목표를 유지한다. ON/OFF의 전체 초기 native state가 짝별로 같다. 팔24 보정 cap ±0.15 rad와 최종 C02/model target box 및 240Hz/60Hz 스케줄이 유지됐다.
- 주요 66 관절 연결 중 팔24만 PI를 적용한다. 손가락42·몸통9·C02 하체는 PD 목표를 유지하며 실제 상태 고정이 아니다. runner의 비팔 목표 유지·state-write 없는 target 적용 검사도 통과했다.
- 모든 저장 시점의 humanoid root state가 같다. 기타 위치·속도를 native 저장 body state와 대조하고 위치 목표 오차·quaternion geodesic 회전 오차를 재계산했다. 초기 기타 quaternion과 +5mm 목표 p/q가 유지됐다.
- 매 tick 적용 tension을 직전 저장 route 위치·속도로 원본 k=6000/c=120/최대300 N slack 법칙에서 재계산해 일치시켰다. 절대 LA는 고정이며 초기 법칙 장력 0 N을 runtime 일정 힘으로 해석하지 않는다. post-step 길이와 적용 힘의 시점 차이를 구분했다.
- 접촉 행 수·고유 physics samples·첫/마지막 step, held sample 포화 수, 실제 arm drift/scalar-limit 차이와 native landmark 기반 palm-up proxy 최솟값을 재집계했다. 장기 raw5는 각 short prefix와 정확히 같다. 236개 명시 입력 SHA 및 native report runtime SHA가 현재 파일과 같다.

## 선택과 물리 해석

- [초기 표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/README.md:5)의 source 최소값 8개와 [저장 trace 표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/README.md:22)의 최대 p/q 값 24행을 원자료와 대조했다. signed query는 PhysX cooked clearance·관통 깊이·접촉·지지력 인증이 아니다.
- 1초 양오차 개선 후보 세 개를 기준 최대값으로 정규화한 합으로 다시 정렬했다. Wrist_x−0.0125와 Elbow_y−0.0015625 두 조건만 OFF 비교한 선택이 계획과 같다.
- Wrist_x−0.0125 ON 73.268255309 mm/13.439338517°는 기존 기준보다 0.392175468 mm/0.062782228° 작다. 동일 초기각 OFF는 144.267967167 mm/36.395295962°다. 새 각도를 다음 진단 기준으로만 사용하는 결정과 맞으며 안정 연주 자세 채택을 뜻하지 않는다.
- 모든 1초 LH/어깨 contact 행은 0이다. ON 포화는 각 212 held physics samples, OFF 포화는 0이며 큰 종료 속도와 drift가 남는다. 원자료의 tension/속도 범위와 실제 scalar-limit 위반 0.030286–0.030300°는 문서와 맞다. target bounds 통과와 actual state 위반, contact 수와 지지력 인증을 분리한다.
- 소단계 결과, PLAN §40, adapter README, VISUAL_REPORT §32의 결론이 같다. 다음 fixed LA 0/1/2 N 초기 법칙 비교는 새 full pose에서 다시 감사하는 미래 단계이며 다른 왼손목 pose의 이전 strap 성능을 승계하지 않는다. 기타 p/q feedback·새 제어·학습은 구현하지 않았다.

## 최종 문서·미디어 확인과 동결

- [지원 CLI](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/README.md:65)를 별도 빈 `/tmp/left_palm_boundary_reviewer_plot_20261007` 경로에서 실행해 exit 0을 확인했다. 1902×1884 canonical PNG와 재생성 PNG의 byte와 RGBA pixel이 정확히 같다.
- canonical 이미지를 직접 확인했다. 세 기간의 x축과 mm/degree 단위, 여섯 ON 조건·두 OFF 조건 범례, 동일 초기조건의 실선/점선 및 저장 곡선이 맞고 주요 곡선·설명 잘림이 없다. native renderer가 아닌 저장 CPU PhysX 측정 trace 그래프다.
- canonical과 재생성 manifest의 embedded 입력236, comparison1, producer1, output1 SHA를 실제 파일과 직접 대조했다. 현재 생성된 README/CHANGED_FILES 절대 링크와 실제 줄 anchor가 존재한다.
- VISUAL_REPORT:742의 초기조건 수 표현은 ‘기준을 포함한 6개’로 정정돼 초기 audit와 일치한다. README:57의 실제 scalar-limit 위반 수치도 확인했다. 남은 지적은 없다.
- checklist·인덱스 검수 상태와 예정 snapshot/verification/inventory는 부모의 후속 metadata 정리 범위다. 현재 이 검수 기록을 동결하며 snapshot 수집 뒤 추가 수정하지 않는다.
