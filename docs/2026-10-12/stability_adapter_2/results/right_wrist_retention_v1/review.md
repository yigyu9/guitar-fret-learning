# right_wrist_retention_v1 별도 변경 검수

2026-10-06. 별도 change-reviewer. 수정 소유는 이 review.md뿐이다.
다른 작업자의 코드·문서·원자료·기존 보관본은 읽기 전용이며 되돌리지 않았다.
검수자는 새 native 초기화·search·physics trial을 실행하지 않았다.

## 계획·초기7개 입력 판정

**문제없음**. 현재 코드·계획·입력 범위의 남은 Critical/Warning/Suggestion 없음.
동적 결과·미디어·최종 문서는 아래 검수에서 확인했다.

- `/home/ajou/yigyu/3/stability_adapter_2/RIGHT_WRIST_RETENTION_COMPARE.md:7`–`:20`은
  fine candidate_02 주변 Wrist_x만±0.0025/0.005/0.01rad의7고정 입력을 만들고,
  기존 source/LH/native bounds gate를 유지한다. 최대3개 짧은 ON 후보·0.5초 비교와
  양오차 개선 최대2개만1초/OFF 진단하는 범위는 기존 초기각·PI 승인 범위와 정합한다.
  거리만으로 실제 접촉·유지 성공을 선언하지 않는다.
- `/home/ajou/yigyu/3/stability_adapter_2/make_right_wrist_inputs.py:26`–`:42`가 C02 native 초기 q와
  현재 기준 q/props/body/goal/route를 읽고 `:46`–`:62`에서 Wrist_x 하나만 변경·대조한다.
  C02±0.3rad∩model, 비선택 q/proximal body·기타 초기 states/고정 +5mm goal·PD·
  고정 절대LA/route·vel0·0steps/state불변을 확인한다. `:64`의 source 음수0/LH 조건은 유지된다.
- initial_inputs.json7개 recipe의 집합/nominal delta를 독립 대조했고 actual delta는
  각±0.0025/0.005/0.01rad와2e−7rad 이내로 일치한다. Wrist_x 외 named angle 및 나머지 setting은 기준과 exact다.
  reference Wrist_x의 nominal JSON 차이4.77e−9rad는 저장 native float32 q를 입력으로 재사용한 변환이며
  실제 native q를 변경하는 값이 아니다. 초기 계약과 source/input SHA readback은 전부 true다.
- 기준/−.01/−.005/−.0025/+.0025/+.005/+.01의 unsigned RH:palm/G:body source 간격은
  각각2.256704/2.371586/2.313745/2.285141/2.228443/2.200303/2.144673mm다.
  +.01만 전신 source 음수 pair1로 거부되고 나머지6개가 통과한다.
  source 가까움은 PhysX cooked clearance·접촉력·실제 지지·자유 기타 안정성 인증이 아니다.
- 기존24팔 PI±0.15rad/60Hz/gain/cap, torso9·finger42·C02하체/root·자유기타·
  원본 cable law와 고정 length를 유지하며 새 controller/학습/동적 strap/pose 덮어쓰기를 도입하지 않는다.

수정한 프로젝트 파일은 이 검수 기록뿐이다.

## saved-only helper와0.5초8개 실행 검수

**문제없음**. 현재 helper·8개 원자료·기간 연장 선정의 남은 Critical/Warning/Suggestion 없음.

- `/home/ajou/yigyu/3/stability_adapter_2/compare_wrist_retention.py:28`–`:69`는 저장 native raw6만
  읽어 accepted recipe·Wrist_x 외 초기각·mode·고정length·PD/model/controller·관절/δ bounds·
  정확한 매4step ON schedule·sample count·초기 audit/current source·long prefix·OFF paired 초기state를 대조한다.
  `:81`–`:89`는 fixed required short set와 선언 path/count를 검증하고 실제 초기 audit/raw6/commands/
  audit source/외부 기준 raw5/helper만 입력 SHA로 기록한다. downstream comparison/media/docs를 포함하지 않는다.
- 보존된 comparison_05s의8 rows/global checks와 모든 입력 SHA를 확인했다.
  short4개 및0.5초4개 ON의6/30개 update에서 actual error·적분·clip·blocked rollback 후 재계산을
  saved pre-step q로 독립 계산해 모든 control record와 exact 일치했다.
  final target은 C02/native model diagnostic box와 initial±0.15rad 안이다.
- raw에서 위치·회전 최대오차와 contact row/unique physics sample/firstlast를 재계산해 일치했다.
  0.5초 기준34.975339mm/4.871416°, minus0025 35.206641/4.912436,
  minus0050 35.481509/4.991410, plus0025 34.743287/4.817860이다.
  plus0025만 두 최대오차를 함께 줄여1초 대상이 된 extension_selection 기록이 정확하다.
  이는 기간 연장 진단이며 새 controller·gate·성공/채택 선언이 아니다.
- 모든 short contact는 hip23행으로 손/어깨0이다.0.5초 reference의 thumb3/2는119/6행,
  minus0025 95/3, minus0050 120/7, plus0025 119/1행이다. LH/어깨 관측0이며 행 수를 힘/원인으로 단정하지 않는다.
- 실제 pure helper CLI를 read-only symlink raw fixture에서 실행해 hold_05s/minus0025 한 실행 누락을 검증했다.
  /tmp/right_wrist_retention_missing_half_reviewer_20261006의7 rows는 row 계약을 통과하지만
  declared_run_coverage_exact=false로 종료1이며 누락을 green으로 인정하지 않는다.
  새 native 실행 없이 fixture/output을 /tmp에만 만들었다.

추가1초·OFF 원자료와 최종 미디어·문서는 후속 검수 범위다.

## 전체13개 실행·1초/OFF·decision 검수

- 전체 comparison의13개 row/global 계약은 모두 true이며 초기8개 row는 보존된 comparison_05s와 exact다.
  명령13개의 output path 집합/개수는 실제13개 row와 exact다. 모든 명시 입력 SHA가 현재 파일과 일치한다.
- 추가1초 ON 양쪽60 update까지 actual PI 수식을 독립 재계산해 exact 일치했다.
  OFF3개 모든 physics sample의 final_arm_targets_rad는 해당 run 초기24팔 각과 exact이고
  update=false, integral/applied delta/saturation=0이다. OFF가 residual을 은밀히 적용하지 않는다.
  ON/OFF final target bounds, exact4step schedule, sample counts 및 모든 긴 raw5 short prefix를 확인했다.
  각 기간 reference ON raw5는 이전 fine candidate_02와 exact이며 OFF paired 초기 native state 계약도 통과한다.
- 1초 기준 ON76.099207mm/14.183879°, plus0025 ON84.746456mm/16.983471°,
  plus0025 OFF137.369031mm/33.307159°를 raw에서 독립 재계산해 일치했다.
  ON 후보−기준 +8.647249mm/+2.799591° 및 thumb3 마지막−19step이 decision과 exact다.
  같은 후보에서 PI가 OFF보다 낫다는 결과를 이전 기준보다 초기각이 좋아졌다는 주장과 구분한다.
- 전13개 contact row/unique physics sample/firstlast를 raw에서 재계산했다.
  1초 thumb3 기준 ON187행/69sample/84–160step(.350–.666667초),
  후보 ON168행/58sample/84–141step(.350–.5875초), OFF133행/41sample/108–148step이다.
  후보 ON thumb2는1행/1sample/85step, 기준은6행/4sample/85–88step이다.
  모든 LH/어깨 관측0이며 행/시점을 연속 지지·힘·인과·관통 깊이로 단정하지 않는다.
- decision의 comparison SHA와 보관된1초 rows가 현재 comparison과 exact이며
  후보를 채택하지 않고 이전 fine 기준을 유지하는 계획 `:43`–`:51`과 정합한다.
  minus 후보의1초가 미실행이므로 그 기간을 일반화하지 않으며 새 feedback/gain/모델/gate를 적용하지 않는다.

현재13개 원자료·수치·기간/후보 판정의 남은 Critical/Warning/Suggestion 없음.
최종 미디어·문서는 제작 후 검수한다. 새 native 실행 없이 이 review.md만 수정했다.

## 최종 미디어·문서 검수 판정

**문제없음. 남은 Critical/Warning/Suggestion 없음.**

- `/home/ajou/yigyu/3/stability_adapter_2/plot_wrist_retention.py:22`–`:42`는0.5초 ON4개와
  1초 reference ON/plus0025 ON/OFF3개를 saved time·m→mm·degree로 표시한다.
  sharex=False의0.5/1초 독립 범위·범례·실선/파선이 raw와 일치하며 source renderer/새 native physics가 아니다.
  `:64`–`:71`에서13개 row/global 계약 및158개 명시 입력 SHA를 plot 전에 검증한다.
  기존 output을 거부하고 media/docs를 원자료 comparison 입력으로 수집하지 않는다.
- 결과 README `:34`–`:37`의 지원 CLI를 fresh /tmp/right_wrist_retention_review_reproduction_20261006에서
  실행해 exit0 및1902×1336 전체 pixel exact를 독립 확인했다. PNG도 직접 읽어 축/범례/곡선 비교를 확인했다.
  manifest의 comparison 포함159개 direct 입력, embedded158개 source/raw 입력,
  producer1개 및PNG1개 SHA를 현재 파일과 대조해 모두 일치했다.
- 결과 README `:11`–`:25`, VISUAL_REPORT22절 및 adapter PLAN30/README 현재 note,
  소단계 계획의13run·7static 범위/초기각·PI·접촉/미채택 설명을 확인했다.
  단기 오차 개선은 유지 성공이 아니며 기존 PI는 관절각 오차 보정으로 기타 p/q feedback과 구분한다.
  plus0025는1초 두 오차가 악화되어 채택하지 않고 이전 fine 기준을 유지한다.
  minus 후보의 미실행1초 행동을 단정하지 않으며 새 controller/gain/gate를 도입하지 않는다.
- 현재 입력 audit 및 execution에 연결된 공용 model·runtime·고정 초기조건의 hash/readback과
  이전 reference raw5 exact, 보존된 comparison_05s8 rows exact를 확인했다.
  전역 기존 자료87개/August49개의 최종 보존·source snapshot 집계는 root의 별도 마무리 증거와 구분한다.

검수자가 수정한 프로젝트 파일은 이 review.md뿐이다. 구현·기존 원자료·그림·공용 모델을 수정하거나
다른 작업자의 변경을 되돌리지 않았으며 native physics trial을 추가하지 않았다.
