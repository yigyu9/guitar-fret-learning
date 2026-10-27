# right_support_v1 별도 변경 검수

2026-10-06. 검수자: 별도 change-reviewer. 구현·원자료는 읽기 전용으로 확인했다.
검수자가 생성한 파일은 이 기록뿐이다. 검색/native 초기화/physics trial을 추가 실행하지 않았다.
독립 재계산은 저장된 native state의 source 형상과 원자료를 사용하며 PNG는 `/tmp`에서만 재생성했다.

## 요약 판정

**문제없음**. 남은 Critical/Warning/Suggestion 없음.
이번 세 초기 후보는 기타 최대 이동·회전이 모두 악화되어 채택/장시간 연장하지 않는 판단과 정합한다.
새 palm-position feedback은 승인 대기이며 이 단위에 구현/실험하지 않았다.

## 코드·입력 계약

- `/home/ajou/yigyu/3/stability_adapter_2/search_hand_support.py`의 최소 확장을 이전 보관본과 대조했다.
  side 기본 L, hull helper 기본 LH:palm/guitar는 이전 동작과 같다.
  p08의 저장 초기 pose에서 old/new 기본 helper를 독립 호출해0.799599467mm와 전체 결과가 exact 일치했다.
- 오른팔12 초기각만 변경하며 비선택 DOF, 왼팔 p08·손가락42·몸통9·C02 하체·root·기타 전체 초기 state,
  목표/gain/solver·main66·절대 LA를 유지하는 검사와 fresh 0-step 환경 방식이 정합한다.
  config의 strap guide는 Chest/L_Thorax여서 초기 오른팔 변경은 route를 바꾸지 않는다.
- 전체185개 설정의 right-only±0.3 범위, 나머지 named 설정, LH 고정 metric/방향·국소 높이 gate,
  source-gate accepted 판정·QP feasibility·route/LA·source SHA를 독립 대조했다.
  rank와 최소0.05rad 후보 다양성 계산은 선택 ID180/166/149와 exact 일치한다.
  이 탐색은 좌표별 제한 탐색이며 전 공간 최적성/PhysX clearance를 주장하지 않는다.
- legacy `palm_neck`/log 키와 soft-up tie-break는 LH metric임을 계획·README·comparison semantics가 명시한다.
  RH:palm/G:body 거리를 탐색하되 RH에 새 +Z 제약을 추가하지 않았다. 이 Suggestion은 해결됐다.

## 원자료·비교 독립 검증

- `compare_right_support.py`와 네 run의 summarize 지표, source 초기/종료 RH hull QP,
  전 physics sample의 LH up-dot, native contact counter를 재계산해 정확히 일치했다.
- 네 run의 실제 초기 full guitar state·오른팔 밖 body state·비선택 DOF state가 기준과 exact 같다.
  모든 초기 DOF pos는 목표와 같고 velocity0이다. native gain/limits/solver/목표·고정 LA 계약도 통과했다.
- reference의 states/trace/contacts/leg_torques는 이전 joint_hold short/OFF와 exact 일치한다.
  초기 route와 절대 LA는 모두1.1010801317960974m다.
- 최대 기타 오차는 기준6.878064mm/1.520538°와 후보15.555660/15.541828/15.533629mm,
  3.494609/3.492107/3.491368°다. 기준보다 모두 악화되어0.5/1초 trial은 없다.
- RH:palm/G:body source unsigned 초기 거리는100.306162→3.230/7.044/7.180mm이며,
  가까운 배치가 native 손 접촉을 만들지 않았다. 네 조건 LH/RH hand contact row0/R_Hip23행이다.
- 각 후보의 R_Shoulder contact는 총2행으로 step3(0.0125s)과 step4(0.016667s)다.
  step3 raw initialOverlap은 약−4.092mm, step4는 약+0.150mm다.
  접촉 행/이 feature gap을 지지력·보정된 관통 깊이·악화 원인으로 단정하지 않는다.
- LH proxy up-dot 전샘플 최소0.926703584, main scalar-limit 위반의 기준0.02907°/후보약0.03054°를 확인했다.
  target bound 검사와 실제 상태의 작은 위반을 구분하며 source/anatomical/cooked-shape 한계를 명시한다.
- 기존 comparison.json은 보존됐다. comparison_v2의4개 row는 그대로 exact 같고
  long_trial_count0/long_prefix_status=`not_applicable_no_long_runs`다.
  비어 있는 long 비교를 성공 boolean으로 표시하던 항목이 실제 검색/기준 재현 검사에서 분리됐다.

## 그림·문서·출처

- plot 코드·결과 README·VISUAL_REPORT16절과 두 최신 PNG를 직접 확인했다.
  graph의 mm/deg, contact 시점과 source 그림의 reference/candidate_01 t=0/24,
  공통 bounds/view 및 RH:palm/G:body witness가 원자료와 일치한다.
  파랑은 기타 neck/body 형상이며 이전 G:body-only caption을 교정한 geometry_v2가 최신이다.
  그림은 CPU source 재구성이며 native renderer·contact/clearance 인증이 아니다.
- `/tmp` 독립 재생성 결과 graph1982×1352/source geometry_v2 1908×1532가 픽셀까지 exact 일치했다.
  이전 PNG/manifest와 source_plot_v1의 이전 plotter SHA가 보존됐음을 확인했다.
- plot_manifest_v2의 입력22개/helper6개/config·XML·mesh40개/embedded search58개/
  embedded comparison28개와 canonical 두 출력의 SHA가 현재 파일과 일치한다.
  최초 source_manifest17개는 현재 파일과 보관본의 SHA가 모두 일치한다.
  protected87/Aug19 49파일의 변경 목록은 비어 있다. 사전 보호 기록은 부모가 소유한다.
- README 재생성 명령의 미지원 `--manifest-path`를 제거하도록 요청했고 현재 명령은 parser와 일치한다.
  기본 plot_manifest.json 생성과 보관된 canonical v2 이름을 구분한다.
  부모의 documented_command_validation에서 exit0/두 PNG pixel exact를 확인했다. 이 Warning은 해결됐다.

최종 SHA readback 완료: source_manifest_final.json의8개 현재 파일과 source_final 보관본 SHA가 모두 기록값과 exact 일치한다. 추가 code/native/media 검증 없이 이 기록만 갱신했으며 최종 판정 문제없음이다.
