# right_elbow_y_negative_v1 별도 변경 검수

2026-10-06. 별도 change-reviewer. 수정 소유는 이 review.md뿐이다.
공유 작업자의 코드·문서·원자료·이전 review/snapshot을 수정하거나 되돌리지 않았다.
검수자는 새 native 초기화·source search·physics trial을 실행하지 않았다.

## 계획·5개 입력·초기 audit 판정

**문제없음**. 현재 초기 범위의 남은 Critical/Warning/Suggestion 없음.
동적 결과·미디어·최종 문서는 아래 후속 검수에서 확인했다.

- `/home/ajou/yigyu/3/stability_adapter_2/RIGHT_ELBOW_Y_NEGATIVE_COMPARE.md:6`–`:16`의
  reference와 Y−0.00125/0.0025/0.005/0.01rad 입력, accepted 작은 |delta| 최대3개 및
  후보가 없으면 native 미실행 조건은 기존 초기각·PI 승인 범위와 정합한다.
  0.5초 양오차 개선만1초,1초 개선만 OFF 진단하며 새 controller/gain/gate/성공 threshold를 도입하지 않는다.
- input JSON5개는 R_Elbow_y 하나만 nominal delta로 변경하고 나머지 named 각·setting은 reference와 exact다.
  기존 audit_arm_initial_inputs.py와 compare_arm_initial_trials.py는 이전 elbow source_final 사본/manifest SHA 및
  현재 source SHA가 모두 일치한다. 공용 모델/기존 검사 수학을 바꾸지 않는 재사용이다.
- 완료된 initial_inputs.json의 전체 native q vector를 독립 계산했다.
  reference는 fine candidate_02의 저장 native q와 exact이고 각 후보는 R_Elbow_y 한 축만 다르다.
  actual delta는−0.001250029/−0.002500057/−0.004999995/−0.009999990rad이며 nominal과2e−7rad 이내다.
  C02±0.3rad∩model·팔 밖 q/proximal body·기타 state/+5mm 고정 goal·PD·root·route/LA·LH gate·
  vel0·0step/state불변 등의 초기 계약과 모든 input/source SHA 현재 readback이 일치한다.
- reference 및 네 음수 후보의 unsigned RH:palm/G:body source 간격은
  2.256704/2.178539/2.100229/1.945430/1.663483mm다.
  −0.00125만 전신 음수 pair0으로 accepted이며 더 큰 음수3개는 각각 source 음수 pair1로 거부된다.
  unsigned palm proxy가 양수여도 전체 source gate를 대신하지 않으며 실제 cooked clearance·지지 인증으로 쓰지 않는다.
- native_selection.json은 accepted y_minus00125 하나만 선택하여 계획의 작은 |delta| 순서/최대3 조건과 정합한다.
  거부3개 native 결과를 추정하거나 gate를 완화하지 않는다.

검수자가 수정한 프로젝트 파일은 이 새 검수 기록뿐이다.

## 4개 ON 원자료·판정 검수

**문제없음**. 현재 동적 결과·판정 범위의 남은 Critical/Warning/Suggestion 없음.

- 변경하지 않은 공용 compare의4개 native/global row 계약을 확인했다.
  선언된4개 output path/count와 실제 rows가 exact이며104개 명시 input SHA가 현재 파일과 일치한다.
  root의 실제 pure CLI repeat 전체 comparison JSON도 current와 exact인 것을 직접 읽었다.
  파생 comparison/media/docs는 입력에 포함되지 않는다.
- short/0.5초 각각6/30개 ON PI update의 stored pre-step actual error·적분·raw δ·clip·hardbox·
  blocked rollback 후 재계산·saturation을 독립 계산해 record와 exact 일치했다.
  final target은 initial±0.15rad 및 C02/model diagnostic box 안이며 non-update sample의
  target/integral은 이전 control record와 exact다. 초기 q/vel은 accepted audit full vector/vel0와 일치한다.
- 두 기간의 reference raw5(states/trace/contacts/leg_torques/controls)는 이전 fine c02 ON과 exact이고
  각0.5초 raw5는 해당 short prefix와 exact다.
  short reference6.872016mm/1.519281°, 후보6.871872mm/1.519261°;
  0.5초 reference34.975339mm/4.871416°, 후보35.237610mm/4.909962°를 raw에서 재계산했다.
  차이+0.262271mm/+0.038546° 및 decision의 미채택·1초/OFF 미실행이 현재 계획과 정합한다.
- contact row/unique sample/firstlast도 raw에서 독립 확인했다.
  short는 모두 hip23행/22sample뿐이다.0.5초 reference thumb3는119행/37sample/84–120step,
  thumb2는6행/4sample/85–88step; 후보 thumb3는97행/30sample/85–120step,
  thumb2는1행/1sample/86step이다. LH/어깨 관측0이며 행/시점을 힘·원인·연속 지지로 단정하지 않는다.
  포화는 short8/0.5초92 physics samples이고 actual scalar-limit 위반은
  reference0.030294°/후보0.030293°다. target bounds와 actual state/안정성 성공을 구분한다.
- 소단계 계획 `:32`–`:42`, PLAN32 및 adapter README의 source 거부3개 미실행·fine c02 유지,
  현재1초 성능 미측정과 다음 late-behavior 직접 진단 제안을 구분한 설명이 정합한다.
  향후 다른 기간의 결과를 현재0.5초 판정에서 추정하지 않으며 새 controller/gain/gate/goal을 적용하지 않는다.

최종 미디어·결과 문서는 아래에서 확인했다. 새 native 실행·이전 파일 수정 없이 이 review.md만 갱신했다.

## 최종 v2 미디어·문서 검수

**문제없음**. 전체 요청 범위의 남은 Critical/Warning/Suggestion 없음. 이 검수 기록은 최종본으로 동결한다.

- 새 `plot_saved_arm_trials.py`는 실제 duration 그룹 수로 행을 만들고 각 기간의 x축 범위와
  실제 이름/ON·OFF 표시를 사용한다. global/row 계약 및 명시 입력 SHA를 그림 생성 전에 확인한다.
  현재 canonical `artifacts_v2`는 4개 ON 결과의 0.1/0.5초 두 기간을 정확히 표시하며,
  저장된 기타 위치·회전 오차 측정 그래프임을 명시한다.
- 결과 README의 실제 지원 CLI를 새 `/tmp/right_elbow_y_negative_review_reproduction_v2_20261006`에서
  독립 실행해 exit0을 확인했다. canonical PNG를 직접 시각 확인했으며 재생성 PNG는
  1901×1257 RGBA 픽셀 및 파일 바이트가 모두 exact다.
  canonical manifest의 comparison1개·embedded 입력104개·producer1개·output1개 SHA를
  현재 파일에서 다시 읽어 모두 일치함을 확인했다.
- README의 표 머리말 `기간`, 이미지 설명 `0.1/0.5초 두 기간별`, canonical v2 링크와
  VISUAL_REPORT 24절의 네 수치·접촉/포화·미채택 및 1초/OFF 미실행 설명이 원자료와 정합한다.
  0.5초 결과로 장시간 안정성을 주장하지 않으며 PI 관절각 보정과 기타 pose feedback을 구분한다.
- 최초 producer 사본과 artifacts/artifacts_v1의 기존 PNG·manifest 보존을 확인했다.
  새 native 실행, 원자료/공용 모델/제어 코드 수정, 이전 검수 기록 변경은 하지 않았다.
