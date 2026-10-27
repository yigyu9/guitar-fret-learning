# right_clearance_v3 별도 변경 검수

2026-10-06. 별도 change-reviewer. 구현·원자료는 읽기 전용으로 확인했다.
검수자가 수정한 파일은 이 기록뿐이며 native 초기화/physics trial은 추가 실행하지 않았다.
독립 형상 재계산은 저장 native pose로 구성한 CPU source query만 사용한다.

## 코드·입력·동적 원자료 판정

**문제없음**. 코드·입력·원자료·미디어·문서의 Critical/Warning/Suggestion 없음.
세 후보를 채택/연장하지 않는 현재 판정과 정합한다. 새로운 feedback은 승인 대기 상태다.

- `/home/ajou/yigyu/3/stability_adapter_2/make_right_clearance_inputs.py:51`의 변경은
  fine3 recipe 추가와 총10개 scope 표기에 한정된다. v2 보관본과의 diff를 확인했고 gate/native 환경은 변경하지 않는다.
- v3의 첫7개 평가가 v2와 exact 일치하며 v2 generator 보관본 SHA가 이전 audit와 일치한다.
  10개 설정의 비right named 각도·LH metric/L_Wrist 위치·절대 LA/+5mm 목표·±0.3rad bounds·
  fine C02 기준 Thorax_y/Shoulder_x 보정과 나머지 candidate_01 각도를 독립 대조해 일치했다.
  accepted 판정은 기존 source 음수 pair/LH 조건과 일치하며 실제 출력 입력4개도 audit와 exact 일치한다.
- fine3 초기 RH:palm/G:body unsigned proxy는12.064576/20.827387/38.250420mm,
  R_Shoulder/G:body는2.909802/2.662764/5.564788mm이며 source 음수 pair는 모두0이다.
  이 정적 proxy를 실제 접촉/지지력/PhysX clearance 인증으로 사용하지 않는다.
- 저장된 네 native 실행은 각각25 states/trace와24 contacts다.
  모든 native run/파생 row check를 확인하고 gains/kd/caps/drive modes/solver/model bounds/source·
  기타 목표/초기 fullstate·human root·비right 초기각·절대 LA/route가 기준과 같은지 독립 대조했다.
  기준 states/trace/contacts/leg_torques는 이전 joint_hold_v1/short/off와 exact 일치한다.
- 비교 helper `/home/ajou/yigyu/3/stability_adapter_2/compare_right_support.py:31`의
  파생 summary, 초기 전체 source gate, 초기/종료 손 proxy와 오른손 hull 결과를 저장 pose에서 재계산해 모두 exact 일치했다.
  원 contact 행에서 body별 계수를 재계산했고, LH normal의 전체25표본 최소0.926703584를 native body 위치에서 직접 재계산했다.
- 기타 최대 오차는 기준6.878064mm/1.520538°, ty0175_sx0175 8.581359mm/2.157702°,
  ty0175_sx015 9.867470mm/2.467039°, ty015_sx010 6.875701mm/1.519469°로 raw trace와 일치한다.
  근접 두 후보에 오른어깨 contact2행씩, 마지막 후보/기준에는0행이며 LH/RH 손은 모두0행이다.
  부위 contact 행 계수는 지지력/변화 원인을 증명하지 않는다.
- 마지막 후보의 감소2.362974µm/0.00106913°를 의미 있는 개선으로 채택하지 않는 계획의 해석이 타당하다.
  long_trial_count=0/not_applicable_no_long_runs로 장기 유지나 prefix 검증을 주장하지 않는다.
- 입력 생성기 AST 문법검사, search의60 source SHA, comparison 입력 SHA와 보관 source 사본 SHA를 확인했다.
  최초 계획서 snapshot은 결과 추가 이전 버전이며 현재 문서와 역사 SHA가 달라지는 이유를 구별한다.

검수 범위 밖의 다른 작업 트리 변경은 수정하거나 되돌리지 않았다.

## 미디어·문서 최종 검수

- `/home/ajou/yigyu/3/stability_adapter_2/plot_right_clearance.py:35`의 네 trace 곡선·최대값·단위를
  원 JSON과 대조했다. 두 ty0175 run의 어깨 접촉 marker는 각각 실제 raw step3/5 시점과 일치한다.
  기준과 ty015_sx010의 곡선이 거의 겹치는 그림은 미세 차이를 의미 있는 개선으로 해석하지 않는 문구와 정합한다.
- 같은 파일 `:82`의 reference/ty015_sx010 초기·step24 source 재구성은 공통 world bounds/view를 쓴다.
  그림 두 장을 직접 확인했고 RH:palm/G:body witness·기타 body/neck·오른팔/손 색상과 표시 수치가 일치한다.
  `:109`의 computed_zorder=False 및 높은 witness zorder는 가독성용 annotation이다.
  결과 README `:43`과 VISUAL_REPORT `:600`은 실제 앞뒤 가림을 표현하지 않는다고 명시한다.
- 지원 CLI를 `/tmp/right_clearance_review_reproduction_20261006`에 독립 실행해 exit0을 확인했다.
  canonical native_curves 1963×1362와 source_poses 1703×1415가 각각 재생성 PNG와 픽셀까지 exact 일치한다.
  재생성은 저장 원자료/source 형상만 사용하며 native physics는 실행하지 않는다.
- canonical manifest의 raw input19/embedded search60/helper6/fresh geometry asset40/output2 SHA를
  현재 파일에서 readback해 모두 일치했다. 이전 artifacts_v1 PNG2개와 당시 plotter 사본도 원 manifest SHA와 일치한다.
- 결과 README `:3`, `:11`, `:22`, `:29`, `:43`, `:50`과 누적18절 `:590`, `:600`의
  실행 수·원자료 수치·선별 조건·기타 고정 목표·접촉 한계·source/native 구분·재현 명령을 확인했다.
  “추가 native 실행 없음”은 보고서/그림 생성 과정에 한정하며 이미 완료된 네 실험과 혼동하지 않는다.
- preservation_validation의 기존 보호87파일/August19 자료49파일 및 v2 원자료 보존 검사가 모두 true임을 확인했다.
  후보 채택/연장·하체 진단 재개·승인 대기 feedback의 실행을 주장하지 않는다.
