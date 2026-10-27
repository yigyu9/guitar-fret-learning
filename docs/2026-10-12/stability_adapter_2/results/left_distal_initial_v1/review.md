# 왼팔 distal 초기각 비교 — 독립 통합 검수

검수일: 2026-10-07 KST. 별도 change-reviewer가 이번 입력·저장 실행·문서·미디어를 검수했다.
쓰기 범위는 이 파일뿐이며 코드·원자료·기존 검수 기록은 수정하지 않았다.
새 native simulation, 초기 환경 생성, source geometry query는 실행하지 않았다.

**요약 판정: 문제없음. Critical / Warning / Suggestion 없음.**

## 범위와 초기 계약

- [소단계 계획](/home/ajou/yigyu/3/stability_adapter_2/LEFT_DISTAL_INITIAL_COMPARE.md:5)의 9개 입력과 저장 ON 18개를 대조했다. 기존 audit/comparator/plotter/runner/PI 다섯 파일은 직전 frozen source 사본과 byte가 같다.
- 기준 설정은 기존 `negative_pose_late_v1/wrist_minus0050`과 byte가 같다. 각 후보는 전체 105개 q 중 지정한 왼팔 elbow/wrist 한 축만 약 ±0.025 rad 바뀌며 나머지 104개는 같다. native float32 반올림을 구분했다.
- 저장 C02 초기 q와 native model bounds에 직접 대조해 9개 초기 full q가 C02±0.3/model 교집합 안임을 확인했다.
- 9개 초기 검사 계약과 69개 source SHA가 일치한다. proximal 8개 body, 기타 전체 초기 body state·고정 목표 p/q, PD 속성·effort cap·solver·초기 route/absolute LA가 유지됐다. 초기 q와 목표가 같고 초기 DOF 속도는 0이다.
- source gate와 LH 위쪽 반구·국소 높이·projection 조건을 저장 검사값에서 재판정했다. L_Elbow_x 양의 후보, L_Elbow_y 음의 후보, L_Wrist_x 음의 후보는 각각 음수 pair 2/4/2개로 거절됐고 native 실행 목록에 없다.
- 기준과 통과 후보 5개만 세 기간에 실행됐다. 세 명령 목록의 경로·개수 집합이 실제 18개 run과 정확히 같다. 참조 symlink 3개는 기록된 원본으로 해석되며, 기간별 기준 raw5와 원본 raw5가 같다.

## 저장 물리·제어 검증

- 18개 run의 2,304 physics samples에서 60Hz PI update 576회를 구현을 호출하지 않고 별도 수식으로 계산했다. e=q_ref−q, 조건부 적분·rollback, 최종 clipping, blocked/saturated 값과 저장 여섯 벡터가 정확히 같다. update 사이 보정 기록은 유지되고 native float32 최종 목표는 허용 오차 안에서 같다.
- 24팔 PI의 ±0.15 rad cap과 최종 C02/model target box, 240Hz/60Hz 스케줄이 유지된다. 주요 66 관절 연결에서 손가락42·몸통9·하체는 목표를 유지한다. runner의 비팔 목표 검사와 state-write 없는 target 적용 계약도 통과했다. 이는 실제 관절 상태 고정이라는 뜻이 아니다.
- 모든 저장 시점의 humanoid root state가 초기와 같다. 기타 위치·종료 속도를 native 저장 state와 대조하고 목표 위치 오차·quaternion geodesic 회전 오차를 재계산했다. 공용 +5mm 목표와 초기 기타 quaternion은 바뀌지 않았다.
- 매 tick의 적용 tension을 직전 저장 route 위치·속도에서 k=6000, c=120, 최대 300 N의 원본 slack/tension 법칙으로 재계산해 일치시켰다. LA는 모든 tick에서 고정이다. 초기 법칙 장력 0 N은 runtime 일정 힘을 뜻하지 않으며 post-step 길이와 해당 tick 적용 힘의 시점 차이를 구분했다.
- 접촉 행 수·고유 physics sample 수·첫/마지막 step, held physics sample 포화 수와 actual arm drift/scalar-limit 차이를 원자료에서 재집계했다. 모든 1초 run의 LH/어깨 접촉 행은 0, PI 포화는 각 212 samples다.
- 장기 raw5는 각 조건의 0.1초 prefix와 정확히 같다. 198개 명시 입력 SHA 및 각 native report runtime SHA가 현재 파일과 일치한다. 기존 결과를 다시 쓰거나 downstream 산출물을 입력으로 수집하지 않는다.

## 수치·판정·표현

- [결과 안내의 초기 표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/README.md:5) 9개 최소 LH:palm signed 값과 [trace 표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/README.md:23) 18개 최대 p/q 값을 원자료와 대조했다.
- L_Wrist_y−0.025의 최소 source signed query는 0.072962668 mm지만 native LH 접촉은 없다. source query를 cooked clearance·관통 깊이·지지력으로 해석하지 않는다.
- 기준 1초 최대 오차 73.660430777 mm / 13.502120746°보다 새 후보 다섯 개 모두 위치·회전 오차가 크다. OFF 선택 집합이 비어 있고 후보 미채택·기준 유지 결정은 계획과 맞다.
- 1초 종료 선속도 0.297622–0.460234 m/s, 각속도 1.204088–2.748397 rad/s, 최대 tension 15.028950–15.099994 N과 실제 scalar-limit 차이 0.030273–0.030515°가 문서와 맞다. target bounds 통과와 actual state 위반을 분리한다.
- 소단계 계획 결과, PLAN §39, adapter README, VISUAL_REPORT §31은 같은 결론을 설명한다. 기준도 안정 연주 성공이 아니며 기타 p/q feedback이나 새 controller를 구현했다는 주장이 없다.
- 다음 LH 단일축 7개 delta는 현재 기준에서 native/C02 승인 box 안이지만 성능·source 통과는 아직 측정되지 않았다. 미래 계획이 이번 완료 실행과 분리돼 있다.

## 최종 미디어·문서 확인 및 동결

- [지원 CLI](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/README.md:56)를 별도 빈 `/tmp/left_distal_reviewer_plot_20261007` 경로에서 실행해 exit 0을 확인했다. canonical PNG와 재생성 PNG는 1902×1884 크기, RGBA pixel, 파일 byte가 모두 같다.
- canonical 이미지 직접 확인: 세 기간별 x축, mm/degree 단위, 기준·통과 후보 여섯 범례와 각 저장 trace가 맞고 주요 곡선·설명 잘림이 없다. 그림은 저장 CPU PhysX 측정 trace 그래프이며 renderer 출력이 아니다.
- canonical 및 재생성 manifest의 embedded 입력 198개, comparison 1개, producer 1개, output 1개의 SHA를 실제 파일과 대조했다.
- 현재 README/CHANGED_FILES의 생성된 절대 경로와 줄 anchor가 존재한다. 인덱스의 review 상태와 예정 snapshot/verification/inventory는 부모의 후속 metadata 정리 항목이며 아직 검수된 보존 자료라고 주장하지 않는다.
- 검수 완료: 문제없음. 이 기록을 동결하며 이후 snapshot 수집 뒤에는 추가 수정하지 않는다.
