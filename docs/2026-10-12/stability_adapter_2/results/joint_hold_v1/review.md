# joint_hold_v1 별도 변경 검수

2026-10-06. 검수자: 별도 change-reviewer. 구현과 native 원자료는 읽기 전용으로 확인했다.
검수자가 생성한 파일은 이 기록뿐이며 native 물리 재실행/새 조건은 추가하지 않았다.

## 요약 판정과 범위

Controller/runner/비교·plot 코드·테스트·6개 native 원자료·결과 문서·두 그림: **문제없음**.
후속 media 검수와 provenance 보완 확인을 마쳤다. 남은 Critical/Warning/Suggestion 없음.
관절 hold 오차 개선을 확인했으나 손 지지/기타 안정 유지 성공은 아니다.

## 확인한 변경

- `/home/ajou/yigyu/3/stability_adapter_2/joint_hold_residual.py:19`:
  `e=q_play−q`, 양의 P=1/I=2/s 부호가 기준각 복귀 방향이다.
  proposed 적분으로 계산한 raw residual과 두 단계 clipping 후 실제 적용 residual을 비교한다.
  오차가 포화를 더 밀어내면 기존 integral을 유지하고 최종 목표를 다시 계산한다.
  보정 cap ±0.15와 최종 model∩C02±0.3 범위를 모두 anti-windup에 반영한다.
- `/home/ajou/yigyu/3/stability_adapter_2/run_joint_hold.py:53`:
  240Hz 물리의 매4번째 직전 상태로 60Hz 목표를 갱신하며 양팔24에만 residual을 전달한다.
  하나의 main66 목표를 합성하고 fingers42·torso9·하체 목표는 유지한다.
  `set_main_offsets`는 position target만 제출한다. 각도/root/기타 state 재주입,
  손 부착, native gain 변경, 동적 strap rest 길이 또는 기타 직접 복원 힘은 없다.
- controls의 error/integral/target은 physics 이전에 기록된다. 240Hz의 held record 반복에 대한
  포화 sample 수는 독립 60Hz update 수와 다르며 비교 JSON이 이 의미를 명시한다.

## 독립 검증

- controller unit tests4개를 독립 실행해 통과했다. 별도 actuator cap/final hard cap,
  반대 방향 적분 unwind, invalid shape/NaN/dt 거부를 확인했다.
- 6개 run의 전체 saved actualq에서 60Hz P/I·조건부 적분·blocked flag·raw residual을
  독립 재계산해 정확히 일치했다. 최종 float32 target 차이는2e−7rad 미만이다.
  각 목표의 두 범위와 unchanged 비팔 목표, initial 전체state/PD·bounds/goal/LA/SHA도 확인했다.
- short/0.5s OFF의 상태·trace·contact·leg torque는 이전 p08_load00과 exact 일치했다.
  OFF/ON 초기 state와 긴 실행의 short prefix 검사도 통과한다.
- 비교의 initial/final hand와 source convex-hull QP12세트를 재계산해 정확히 일치했다.
  comparison 입력 SHA와6개 run의 runtime SHA도 일치한다. 원자료는 변경하지 않았다.
- 양팔 raw 최대 편차(OFF→ON)는0.1s6.642245→5.849519°,0.5s18.314300→12.594604°,
  1s20.997021→14.313614°다. ON 포화 physics sample 수는 각각8/92/212개다.
- 기타 최대 오차는0.1s 양쪽6.878064mm/1.520538°로 같다.
  0.5s61.482752mm/8.876739°→61.462498mm/8.872952°는 매우 작은 변화다.
  1s264.206678mm/48.065151°→196.035023mm/33.993888°는 개선됐으나 큰 오차가 남는다.
- LH–기타 raw contact row는6개 모두0이다. 1s source 손–넥 거리는
  OFF270.834901mm/ON156.395205mm로 여전히 멀다.
  모든 실제 샘플의 palm-normal proxy min은0.926704지만 anatomical sign은 미검증이다.
  actual arm scalar-limit 위반 최대0.029066°는 OFF/ON 공통이며 위반0으로 주장할 수 없다.

## 해결한 Warning

기존 제안/PLAN의 최종 FK·기하·작업조건/변화율 계약과 현재 clipping-only 구현을 구별하도록 요청했다.
`/home/ajou/yigyu/3/stability_adapter_2/JOINT_HOLD_RESIDUAL_PROPOSAL.md` 마지막 문단과
comparison scope가 이번 actuator 진단에는 FK task rejection·목표 변화율 검사가 미구현임을
명시한다. 검사 통과/연주 호환/안정 성공을 주장하지 않으며 후속 제어에서 별도 구현·검증한다.

## 후속 media·문서·provenance 검수

- `plot_joint_hold.py`, 결과 README와 VISUAL_REPORT 15절을 읽고 두 PNG를 직접 확인했다.
  graph의 mm/deg 단위, arm actual−원래 목표 편차, controls의 pre-step 시점과 포화 표시가 정확하다.
  source pose 그림은 공통 시작과0.5/1초 OFF/ON의 실제 저장 pose를 같은 bounds/view로 재구성한다.
  그림 title의 종료값과 표/graph의 전체 구간 최대값을 구분한다.
  ON 1초 종료 위치오차 약195.5mm는 구간 최대196.035mm와 다른 값이며 오류가 아니다.
- `/tmp` 재생성에서 graph2062×1352, pose2211×1432가 원PNG와 픽셀까지 정확히 일치했다.
  새 물리 실행/원자료 변경은 없다. 두 그림은 native renderer나 지지력·clearance 인증이 아니다.
- 첫 plot manifest가 실제로 읽는 현재 config/XML/mesh의 fresh SHA를 포함하지 않아 보완을 요청했다.
  `/home/ajou/yigyu/3/stability_adapter_2/plot_joint_hold.py:172`에서 실제 geometry asset 목록을 구하고
  `:216`에서 fresh SHA를 저장하도록 보완됐다. `plot_manifest_v2.json`의 입력31개, plot source6개,
  config/XML/mesh40개가 현재 파일과 일치한다. `/tmp` 두 출력 SHA는 원PNG SHA와 각각 동일하다.
  이전 manifest/PNG는 그대로 보존하며 README가 v2를 최신 provenance로 안내한다. 이 Warning은 해결됐다.
- 최초 source snapshot26개의 보관본 SHA, 그 시점의 현재 파일과6개 runtime SHA 검증을 확인했다.
  이후 문서/plotter 수정은 이전 source snapshot을 변경하지 않는다. 실제 물리 runtime은 그대로다.
  protected87/Aug19 49파일 보존 기록의 변경 목록은 모두 비어 있다.
  보호 검사의 사전 상태는 부모가 소유하며 검수자는 이를 새로 생성하지 않았다.

## 다음 palm-position 제안의 설계 검토

`PALM_POSITION_RESIDUAL_PROPOSAL.md`는 사용자 확인 전 제안으로만 검토했다.
Jacobian 계측/새 ON controller/rollout은 실행하지 않았다.

- 먼저 fixed-root Jacobian layout·origin/COM·world frame을 fresh native FK 유한차분과 대조하고
  검증 실패 시 position controller를 실행하지 않는 gate가 적절하다.
- world error의 부호, 위치 least-squares와 PI regularizer의 단위가 정합한다.
  명시적인 목적함수와 solver bounds(model∩C02 box∩총cap∩직전target 변화율),
  proposed integral→solve→blocked→rollback→resolve 순서를 명확히 하도록 한 제안이 반영됐다.
- 기존 PI/동일 rate PI/동일 rate position 보정의 세 대조조건으로 task와 rate 효과를 구분한다.
  왼팔12만 position task를 받고 오른팔12는 PI이며 fingers42·torso9·하체/native gain/LA/root/기타는 보존한다.
  향후 연주에는 지지 목표를 연주 목표에서 갱신하며 영구 world 고정 손으로 승계하지 않는다.
- Anti-windup은 capped regularizer만으로 판단하지 않고 clipping 전 raw `e+2I`와 실제 최종 적용량의
  차이를 사용한다고 제안 문서에 명시된 것을 확인했다. 총cap의 적분 누적을 감지하는 기존 계약과 일치한다.
  Jacobian calibration과 실제 제어 변경은 사용자 확인 이후 별도 검수한다.

최종 문서 확인: `source_manifest_final.json`의7개 현재 파일/`source_final` 보관본 SHA가 모두 정확히 일치하며 최초 source26개 SHA와6run runtime SHA도 보존됐다. README:24/VISUAL:548의1초 ON R_Shoulder65·RH:thumb2 35·RH:thumb3 78행과 OFF0행, 양쪽 R_Hip239행은 raw contact 독립 집계와 일치한다. 이를 지지력/개선 인과로 단정하지 않고 README:9의 열도 ‘왼손–기타 접촉 행’으로 구분한다. VISUAL:554는 최신 v2 manifest를 연결하며 두 proposal의 완료/승인 대기 상태와 raw anti-windup 설명도 정합한다. 최종 판정 문제없음; 새 제어/실험은 실행하지 않았다.
