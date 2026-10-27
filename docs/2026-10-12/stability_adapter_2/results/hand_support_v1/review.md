# hand_support_v1 별도 변경 검수

2026-10-06. 검수자: 별도 change-reviewer. 구현·원자료는 읽기 전용으로 확인했다.
이번 검수자가 생성한 파일은 이 기록뿐이다. 새 native rollout 또는 ON 제어 실험은 실행하지 않았다.

## 요약 판정

구현·원자료·그림: **문제없음**. 남은 Critical/Warning 없음.
문서 표현과 마지막 snapshot 갱신 항목도 해결됐다. 남은 Suggestion 없음.
물리적 지지·안정 유지 성공은 아니다. 이 단위 이후 승인된 관절 보정은 joint_hold_v1에서 별도 검수한다.

## 확인 범위와 독립 검증

- `search_hand_support.py`, `compare_hand_support.py`, `plot_hand_support.py`,
  `HAND_SUPPORT_INITIAL_POSE.md`, `JOINT_HOLD_RESIDUAL_PROPOSAL.md`, 결과 README와 VISUAL_REPORT 14절.
- 유효 `search_v2` 159개 초기 설정과 순위/선택 ID 70/72/79를 대조했다.
  LEFT arm 유효 12관절의 승인된 ±0.3rad 범위만 변경하며 오른팔·손가락42·몸통9·C02 하체·root·기타/PD 조건을 유지한다.
  각 후보는 별도 환경의 0-step 초기 상태이며 탐색 중 동적 pose를 재주입하는 방식이 아니다.
- broad-cutoff backend signed query의 부호 불일치를 독립 확인했다.
  geom55는 cutoff0.1/0.2/1m에서 +63.977/−94.407/−162.899mm다.
  이 query를 사용한 첫 검색/입력/소스는 보존되며 native 후보 실행/선정 근거에서 제외됐다.
- 새 6변수 unsigned convex-hull QP는 outward face half-space 제약을 사용한다.
  baseline/선택3개의 witness feasibility와 별도 vertex-support 거리 하한을 대조했다.
  baseline64.025621mm, 선택3의 3.139057/3.269733/2.388134mm와 독립 하한의 차이는 최대 약5.10μm였다.
  이 값은 source 형상의 근접 대리지표이며 PhysX clearance·접촉 깊이·지지 힘이 아니다.
- 10개 native run에서 전체 summarize 지표와 초기/종료 source QP를 다시 계산해 comparison.json과 정확히 일치했다.
  네 coupling 입력은 평가70 또는69의 같은 초기각/형상/hand/query/route를 복사했고,
  rest=route−계획장력/6000 식, trial 입력 파일 내용과 recipe SHA가 정확히 일치했다.
  실행 중 길이는 고정하며 변경된 Thorax 경로를 명시적 절대 rest 길이 후보로 비교한다.
- 모든 native/invariant check, 이전 reference의 상태/접촉/trace/torque exact 재현,
  장시간/짧은 실행의 같은 초기 prefix, comparison 입력 SHA를 확인했다.
  하체 운동/접촉은 물리에 남고 평가 순위에서만 제외된다.
- 0.5초 p08/p3의 기타 최대 오차61.482752/61.483890mm, 회전8.876739/8.876374°,
  최종 source 손–넥 거리146.549949/148.497807mm, LH–기타 raw contact row0을 확인했다.
  가까운 초기 배치가 지속 지지로 이어지지 않았다는 설명과 일치한다.
- 두 PNG를 직접 시각 확인했다. `/tmp` 임시 재생성에서 곡선2059×1507,
  source pose2319×1535가 기존 이미지와 픽셀까지 정확히 일치했다.
  그림은 saved native trace/pose의 CPU source 형상 재구성이며 native renderer 출력이 아니다.
  plot manifest 입력89개/출력2개 SHA와 AST3개를 확인했다. 원자료/이미지는 변경하지 않았다.
- source snapshot36개 보관본의 기록 SHA를 확인했다. 보호87파일/Aug19 49파일 보존 JSON은 전 항목 true다.
  보호 검사의 사전 상태는 부모 에이전트가 소유한 기록이며 이 검수자가 새 사전 상태를 만들지 않았다.
- 잔차 제안은 `e=q_play−q`의 양의 P/I, 하나의 q_final, 팔24만 보정/손가락42·몸통9 목표 유지가 정합한다.
  두 단계 clipping의 delta_applied 기반 anti-windup, 이번 무연주 진단에만 C02±0.3 적용,
  최종 FK/작업 조건 계약을 명시하도록 한 검토 제안은 반영됐다. 이 단위에는 구현/ON trial이 없다.

## 해결된 Suggestion / 마지막 정리

- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:532`:
  서로 다른 t=0/0.5초를 “같은 world bounds와 카메라 시점”으로 비교한다고 교정된 것을 확인했다.
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/source_manifest_final.json`:
  원래 manifest/source는 보존하고 source_final/에 계획3개와 plotter의 최신 보관본을 추가했다.
  네 파일의 보관본/현재 파일이 새 기록 SHA와 일치한다. native runtime/source·원자료는 변경되지 않았다.
