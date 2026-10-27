# right_distal_v1 별도 변경 검수

2026-10-06. 별도 change-reviewer. 구현·원자료는 읽기 전용이며 검수자가 수정한 파일은 이 기록뿐이다.
새 native 초기화/physics trial은 실행하지 않았다. 독립 source 형상 재계산은 저장 native pose만 사용한다.

## 코드·검색·동적 원자료 판정

**문제없음**. 이전 provenance Warning은 수정으로 해소됐으며 현재 범위의 남은 Critical/Warning/Suggestion 없음.
미디어·최종 문서까지 확인했다. 초기 source 근접의 개선을 실제 손 지지/유지 성공으로 채택하지 않는다.

- `/home/ajou/yigyu/3/stability_adapter_2/search_hand_support.py:55`의 optional distal/bounds 설정을 보관본 diff와 대조했다.
  옵션이 없으면 bound_base=base이며 이전 helper·grid·순위·gate 계산은 유지된다.
  옵션이 있으면 별도 native 초기 읽기로 C02 bound_base를 확보해 이미 조정된 시작각에 ±0.3rad를 누적하지 않는다.
- 같은 파일 `:86`은 Elbow/Wrist만 선택하고 `:107`은 나머지 초기 목표/body pose·기타 초기 fullstate/목표·
  native PD/limits·main66/torso9·절대 LA·distal route를 보존한다. 모든 query 뒤 state 불변/steps0 검사도 유지한다.
  proximal 관절 초기각 유지가 실행 중 해당 관절 제어권 제거를 뜻하지 않는다.
- 저장65개 설정의 distal6 이외 named 각도·LH metric/L_Wrist 위치·C02 절대±0.3rad·LA/+5mm·기존 gate를
  독립 대조했다. nominal3mm soft rank/다양성 선정 결과는20/29/36으로 exact 일치하며 source 음수 pair는 모두0이다.
  선택 초기 unsigned RH:palm/G:body 거리3.936732/4.537443/5.796589mm는 source proxy이며 PhysX 지지 인증이 아니다.
- `/home/ajou/yigyu/3/stability_adapter_2/compare_right_support.py:54`의 새 `--reference-run`에 대해
  최초 결과에 선택 기준 경로/외부 raw4 SHA가 없는 Warning을 제시했다.
  `:60`, `:63` 수정으로 canonical comparison_v2.json에 절대 기준 경로와 states/trace/contacts/leg_torques SHA가 기록됐다.
  네 외부 SHA와 실제 파일이 일치하며 기준 raw4가 이전 right_clearance_v3/short/ty015_sx010과 exact 일치한다.
  최초 comparison.json과 보관 소스는 유지하고 v2의 네 rows/checks는 최초 결과와 exact 일치한다.
- 네 native run의25 states/trace 및24 contacts, 초기 proximal/nonselected 각도·root·guitar 목표·gain/kd/caps/drive mode·
  solver/model limits/runtime source·LA/route 보존을 원자료에서 독립 대조했다.
  최대 기타 오차·장력·부위별 raw contact 계수 및 LH normal 전체25표본 최소를 독립 재계산해 일치했다.
- 최대 기타 오차(mm/deg)는 기준6.875701/1.519469, c01 6.876050/1.519890,
  c02 6.872301/1.519297, c03 6.876072/1.519909다. 모든 LH/RH 손·어깨 contact는0이고 hip 행은 각각23이다.
  후보 RH unsigned source 간격은 종료21.824013/21.561650/23.099410mm로 초기보다 커졌다.
  짧은 기타 오차의 미세 차이와 source 근접을 실제 지지/안정 유지 성공으로 해석하지 않는 판정이 정합한다.
- 저장 pose에서 네 run의 파생 summary·초기 전체 source gate·초기/종료 손 metric·RH hull을 재계산해
  comparison_v2와 exact 일치를 확인했다. long_trial_count0/not_applicable_no_long_runs로 장기 유지 검증을 주장하지 않는다.
- 변경 Python AST 검사, 검색 source SHA, canonical comparison 입력 SHA, 최초 보관 source 사본 SHA를 확인했다.
  helper 수정 전 보관본과 현재 provenance 수정본의 시간 차이를 구별하며 새 native 재실행이 필요 없는 수정이다.

다른 작업자의 구현·원자료·보관본을 수정하거나 되돌리지 않았다.

## 기존 승인 PI 재사용: 코드와 short 검사

- run_joint_hold.py와 joint_hold_residual.py는 최초 joint_hold_v1 source 보관본과 byte-identical이다.
  같은 candidate_01 초기각/LA에 기존24팔 PI·±0.15rad·60Hz·C02±0.3 final bounds를 재사용한다.
  proximal q_play 고정과 기존 승인 PI의 proximal 보정 허용을 구별하며 새 palm-position task/gain/제어 cap을 도입하지 않는다.
- `/home/ajou/yigyu/3/stability_adapter_2/compare_joint_hold.py:16`의 optional reference 입력 추가와
  `:61`, `:66`, `:69`의 외부 short raw4 경로/해시 기록을 보관본 diff로 확인했다.
  기본 기존 short/0.5초 역사 대조 및 six-phase/paired/prefix/수치 계산을 유지하고 AST 검사를 통과했다.
- short OFF의 states/trace/contacts/leg_torques는 이번 candidate_01과 exact 일치하며
  short OFF/ON 초기 전체 state·설정·native gains/caps/modes/solver·목표·LA·source는 동일하다.
  raw 재계산에서 arm 최대6.618858→5.832372°이고 기타 최대6.876050mm/1.519890°는 같다.
  관절오차 개선에 따른0.5/1초 진단 연장 조건과 정합하며 안정 유지 성공/새 후보 채택을 뜻하지 않는다.
- 긴 OFF/ON 원자료·전체 비교 및 미디어는 아래 후속 검수에서 확인했다. 검수자는 native 실행을 하지 않았다.

## 기존 PI 재사용: 여섯 실행과 decision 원자료

- short/0.5초/1초 OFF/ON 여섯 run의 native/목표/PD/gain/cap/solver/LA 계약과 표본 수를 확인했다.
  같은 초기 전체 state의 paired 검사와 긴 trace/states/contacts/controls/leg_torques prefix를 직접 대조해 exact 일치했다.
- 모든 ON update의 e=q_play−q_actual, e+2I, ±0.15rad/최종 hard clipping, 최종 적용량에 대한 blocked 판정,
  조건부 적분 rollback 후 재계산을 저장 pre-step actual q에서 독립 재계산했다.
  기록과 exact 일치하며 60Hz update 사이의 record hold와 전체 target bounds도 일치한다.
- 0.5초 기타 최대54.500076mm/7.900382°→35.847644mm/5.052139°,
  1초143.645622mm/35.962199°→121.298052mm/29.759157°를 raw trace에서 확인했다.
  1초 팔 최대20.981042→14.279672°이며 ON 포화8/92/212개는 held physics sample 계수다.
  실제 arm scalar-limit 위반0.030295304°는 여섯 조건 공통이다. 목표 clipping과 실제 state의 범위 통과를 혼동하지 않는다.
- decision.json의 body별 contact 행 수, 행을 가진 unique physics sample 수, first/last step/time 및
  raw initialOverlap min/max를 원 contact에서 재계산해 모두 exact 일치했다.
  1초 RH thumb3는 OFF91행/34표본(step109–142), ON127행/44표본(step86–142)이며
  ON thumb2는1행이다. first/last가 연속 접촉을 뜻하지 않으며 접촉 행은 힘/인과/지속 지지 인증이 아니다.
- 기존 p08 1초 max 값을 이전 raw trace에서 확인하고 decision/comparison의 모든 입력 SHA를 대조했다.
  초기각과 PI 조건을 구별하여 보정 유지 효과를 진단하고, 안정 연주 자세로 채택하지 않는 판정과 정합한다.

## 최종 미디어·문서 검수

- 기존 plot_joint_hold.py를 그대로 재사용하며 새 물리/제어 코드를 도입하지 않았다.
  두 PNG를 직접 확인했고 1초 trace의 p/q·arm drift·적용량/포화 계수와 source pose/strap route가 저장 원자료와 정합한다.
  source 그림의 0.5초 ON 표시는 종료34.6mm/4.6°이며 표의 최대35.848mm/5.052°와 구별된다.
  공통 bounds/camera의 CPU source 재구성이고 native renderer/cooked clearance 인증이 아니다.
- 지원 CLI를 `/tmp/right_distal_review_reproduction_20261006`에 독립 실행해 exit0을 확인했다.
  canonical trace PNG2062×1352와 source PNG2211×1432가 각각 재생성 결과와 픽셀까지 exact 일치한다.
  canonical manifest의 입력31/plot helper6/fresh geometry asset40/embedded 입력50/출력2 SHA를 현재 파일에서 readback해 모두 일치했다.
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_v1/README.md:7`,
  `:22`, `:31`, `:35`, `:47`, `:54` 및 누적 VISUAL_REPORT `:604`, `:614`의 수치·범위·재현 명령을 확인했다.
  0.1초 hand contact0와 긴 실행의 RH thumb 행을 구별하며, 마지막0.591667초는1초 run에 한정한다.
  basename joint_hold_v1의 도구 재사용 의미, 포화 physics sample과 독립 control update의 차이,
  접촉 row/sample/firstlast/힘·인과 한계가 명확하다. CLI는 새 `/tmp` 출력 폴더를 사용한다.
- 안정 연주 자세 채택·새 feedback/gain/제어cap·하체 진단 재개를 주장하지 않는다.
  후속 matched fixed strap 비교는 다음 분석 방향이며 현재 산출물에 미실행 결과를 포함하지 않는다.

최종 판정: 문제없음. 남은 Critical/Warning/Suggestion 없음. 검수자는 새 native 실행이나 원자료 수정을 하지 않았다.
