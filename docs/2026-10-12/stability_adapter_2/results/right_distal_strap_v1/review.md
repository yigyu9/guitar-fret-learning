# right_distal_strap_v1 별도 변경 검수

2026-10-06. 별도 change-reviewer. 구현·원자료는 읽기 전용이며 수정 소유는 이 검수 기록뿐이다.
검수자는 새 native 초기화/physics trial을 실행하지 않았다.

## 계획·초기 입력 판정

**문제없음**. 현재 초기 입력 범위에서 Critical/Warning/Suggestion 없음.
OFF/ON 원자료·선정·긴 비교와 미디어·최종 문서는 아래 검수에서 확인했다.

- `/home/ajou/yigyu/3/stability_adapter_2/RIGHT_DISTAL_STRAP_COMPARE.md:7`의 동일 candidate_01 초기각,
  기타 +5mm 초기 p/q/고정 목표 및 기존 PI/PD/solver/하체/root/손가락/몸통 보존 조건이 이전 승인 범위와 정합한다.
  변경은 실행 중 고정되는 절대 rest length이며 새 feedback/gain/동적 strap/고정·부착을 도입하지 않는다.
- 기존 pose_strap_inputs.py `:81`의 strap phase를 재사용한다.
  기록된5개 입력의 named 초기각/+5mm·초기 route·전체 source geometry·LH metric이 exact 일치하며 모든 초기 계약이 true다.
  legacy와 load_00n 설정은 exact 동일하고 중복 native 실행 대신 보존만 하는 계획이 타당하다.
- L0=1.1010801317960974m, k=6000N/m로 rest=L0−T0/k를 독립 대조했다.
  0/5/10/20N의 rest는 각각1.1010801317960974/1.1002467984627642/
  1.0994134651294307/1.097746798462764m이고 모두 유효한 양수다.
  초기 법칙 장력은0/5/10/20N과1e−10N 이내로 일치한다.
- 원본 cable law는 길이가 rest를 초과할 때 k·extension+c·Ldot를0~300N에 clip하며 그 외에는0이다.
  초기 장력 recipe를 실행 중 일정 장력 제어로 해석하지 않으며 실제 장력은 운동에 따라 변한다.
- 초기 source/LH gate를 유지하고 관통 깊이/PhysX clearance/실제 지지 성공을 주장하지 않는다.
  입력 생성기의 source/input/asset SHA를 현재 파일에서 확인해 모두 일치했다.

다른 작업자의 구현·기존 원자료·보관본을 수정하거나 되돌리지 않았다.

## 비교 코드·12개 원자료와 회귀 검수

- 새 compare_fixed_strap.py는 저장 JSON만 읽는 NumPy 후처리다. 물리 실행/target/state 쓰기를 도입하지 않는다.
  초기 전체 state·입력 장력·fixed length·native PD/solver/모델/goal·PI 범위/스케줄·초기 audit·runtime SHA·
  긴 prefix와 contact row/unique physics sample 구분을 확인한다. 외부 0N 기준 경로와 raw8 SHA도 기록한다.
- 최초 `/home/ajou/yigyu/3/stability_adapter_2/compare_fixed_strap.py:27`의 report 없는 run skip에 대해
  short 누락을 green으로 처리할 수 있는 coverage Warning을 제시했다.
  현재 `:76`, `:79`에 short 0/5/10/20N×OFF/ON exact set 및 선언 명령의 전체 path 집합/개수 검사가 추가됐다.
  최초 comparison/source를 보존하며 canonical comparison_v2의12 rows는 이전 결과와 exact 일치한다.
- 검수자가 10N ON 한 실행만 뺀 read-only `/tmp` fixture를 fresh output으로 독립 실행했다.
  exit1, all_eight_short_conditions_present=false와 declared_runs_exactly_present=false를 확인해 Warning을 해소했다.
  prefix 파일 누락으로 먼저 실패한 이전 fixture를 coverage 증거로 사용하지 않는 기록도 정확하다.
- 실제 short8개와0.5초4개의 모든 native/파생 row 계약 및 길이/장력 label을 확인했다.
  모든12개 ON PI update의 e=q_play−q_actual·적분·최종 clipping·조건부 blocked/rollback 후 재계산을
  저장 pre-step actual q에서 독립 계산해 record와 exact 일치를 확인했다.
  최대 기타 p/q·팔 drift·장력, contact 행 수/unique sample/firstlast를 raw에서 재계산해 모두 일치했다.
- 0N OFF/ON short raw4는 이전 right_distal_v1/joint_hold와 각각 exact 일치하며,
  0N0.5초 raw4도 이전 같은 기간/모드와 exact 일치한다. 긴 states/trace/contacts/controls/leg_torques short prefix도 exact다.
- 초기8개 수치와 최초 양모드 p/q 동시 비악화 선정0개를 독립 확인했다.
  별도의5N0.5초 진단을 그 기준 통과로 표현하지 않는 계획 `:34`–`:40`은 정합한다.
  0.5초0N OFF54.500076mm/7.900382°, ON35.847644mm/5.052139°;
  5N OFF54.519729mm/8.027734°, ON35.572192mm/5.114377°로 raw와 일치한다.
  두 오차 동시 개선이 없어1초 연장을 멈추고0N 진단 기준을 유지하는 판정과 정합한다. 실제1초 run은 없다.
- canonical comparison의 모든 입력 SHA를 현재 파일에서 확인해 일치했다.
  검수자가 native 실행을 추가하거나 원자료를 수정하지 않았다. 현재 남은 Critical/Warning/Suggestion 없음.

## 최종 미디어·문서 판정

**문제없음**. 남은 Critical/Warning/Suggestion 없음.

- `/home/ajou/yigyu/3/stability_adapter_2/plot_fixed_strap.py:33`–`:41`의 saved time,
  위치 m→mm 및 회전 degree 매핑, phase별 0.1/0.5초 축, load 색상과 OFF/ON 선 모양을 raw와 확인했다.
  `:88`–`:90`은12개 row뿐 아니라 global/row 계약을 모두 확인한 뒤 그림을 생성한다.
  source geometry나 새 native physics를 생성하지 않으며 기존 output을 거부한다.
- canonical PNG를 직접 확인하고 결과 README `:49`–`:54`의 지원 CLI를 fresh
  `/tmp/right_distal_strap_review_reproduction_20261006`에서 실행해 exit0 및2128×1415 전체 pixel exact를 확인했다.
  범례·축·주석이 읽히며 두 phase를 분리해 비교한다.
- short 네 load의 OFF/ON 기타 p/q 시계열은 각각 exact이지만 전체 trace는 모두 다르다.
  README `:18`, `:42`와 VISUAL_REPORT `:624`가 일치를 두 기타 지표로 한정하므로 과장하지 않는다.
  0.5초 수치·엄지 contact 행 수·양오차 tradeoff·1초 미연장·안정 자세 미채택 설명이 raw 및 계획과 일치한다.
  고정 rest length와 변하는 실제 strap tension, contact 행과 고유 sample/힘/지지의 구분도 명시한다.
- canonical manifest의 raw 입력55개, plotter1개, embedded execution/source 입력87개,
  출력 PNG1개의 SHA를 현재 파일에서 대조해 모두 일치했다.
  곡선만 생성하므로 새 geometry asset readback을 요구하지 않는 설명이 타당하다.
  이전 producer와 PNG는 artifacts_v1/source_plot_v1의 이전 manifest SHA와 각각 일치해 보존을 확인했다.

이번 검수에서 쓴 프로젝트 파일은 이 review.md뿐이다. 구현·원자료·계획·이미지·기존 보관본을 수정하지 않았다.
