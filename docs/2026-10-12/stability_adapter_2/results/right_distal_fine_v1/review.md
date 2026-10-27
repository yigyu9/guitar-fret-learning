# right_distal_fine_v1 별도 변경 검수

2026-10-06. 별도 change-reviewer. 수정 소유는 이 review.md뿐이며 구현·원자료·기존 보관본은 읽기 전용이다.
검수자는 새 native 초기화·search·physics trial을 실행하지 않았다.

## 계획·fine 입력 탐색 판정

**문제없음**. 현재 검수 범위에서 Critical/Warning/Suggestion 없음.
동적 결과·최종 미디어·문서까지 아래 검수에서 확인했다.

- `/home/ajou/yigyu/3/stability_adapter_2/RIGHT_DISTAL_FINE_INITIAL_POSE.md:7`–`:12`의
  오른 Elbow/Wrist6만 한 sweep, 현재 best±0.005/0.01/0.025rad, C02±0.3rad∩모델,
  nominal1mm soft 선호 및0.005rad 다양성은 기존 초기각 승인 범위와 정합한다.
  기존 source negative pair0/LH 방향·국소 높이 조건을 유지하며 거리를 실제 접촉 인증으로 사용하지 않는다.
- 이전 right_distal_v1/source/search_hand_support.py와 현재 코드의 diff를 확인했다.
  `/home/ajou/yigyu/3/stability_adapter_2/search_hand_support.py:59`는 fine에서 distal-only 및
  별도 bounds settings를 요구한다. `:134`, `:139`, `:144`–`:148`, `:159`는 fine branch에서만
  nominal/sweep/현재 best 기준 증분/다양성을 바꾼다. 기본 coarse의 두 sweep·절대 C02 offset grid·3mm·0.05rad는 유지된다.
- C02 초기 native 각을 별도 읽는 `:69`–`:74`와 실제 초기값을 만드는 `:100`을 확인했다.
  best의 C02 offset에 작은 증분을 더한 뒤±0.3rad clip하고 native model bounds로 최종 clip한다.
  하체만 명시한 C02 JSON의 미지정 팔 각을0으로 가정하지 않으며 이전 저장 native 기준과 대조했다.
- 완료된 search.json의37개 평가에서 모든 계약이 true이고 비선택 named 관절각 및 나머지 설정이 baseline과 exact다.
  모든 distal C02 offset을 이전 저장 native 기준에서 독립 계산해 일치했고 최대 절대 offset은0.225000009rad다.
  baseline native 초기-state SHA는 이전 candidate_01과 exact이며 모든 source/input SHA를 현재 파일에서 확인했다.
- nominal1mm rank와0.005rad separation을 저장 평가에서 독립 재계산해 selected IDs5/21/20이 exact다.
  선택된 source unsigned RH:palm/G:body 거리는2.200303/2.256704/2.313745mm이며
  전신 음수 pair0, LH up-dot0.926703584, local height−24.622360mm로 기존 gate를 통과한다.
  이는 정적 source 가까움 진단이며 PhysX cooked clearance·실제 손 지지·안정성 성공을 뜻하지 않는다.

다른 작업자의 코드·문서·결과·보관본을 수정하거나 되돌리지 않았다.

## 짧은 비교 및0.5초 PI 원자료 검수

- short4개 native 계약 및 raw 기타 최대오차를 독립 확인했다. 기준 raw4는 이전 candidate_01과 exact다.
  후보2의6.872016mm/1.519281°는 기준6.876050mm/1.519890°보다 미세하게 작지만
  초기 손·어깨 contact0이므로 지지/안정성 성공으로 해석하지 않는 계획과 정합한다.
- `/home/ajou/yigyu/3/stability_adapter_2/compare_joint_hold.py:19`, `:25`–`:28`은
  half-second mode의 short/hold_05s×OFF/ON4개 파일을 명시적으로 모두 읽는다.
  default의 short/hold_05s/hold_1s6개 및 기존 파생 수학은 유지된다.
  검수자는 변경하지 않은 main AST/parser/read/check 흐름에서 source-replay metric만 stub한
  read-only symlink fixture로 hold_05s/on 누락을 확인했다. FileNotFoundError로 중단하고 green comparison을 쓰지 않았다.
  native 실행을 재현한 검사가 아니라 후처리 coverage control-flow 회귀다.
- comparison_05s의 실제4개 실행에서 모든 계약·paired state·short prefix가 true다.
  ON6/30개 control update의 actual error·적분·clipping·blocked rollback·재계산을
  저장 pre-step q에서 독립 계산해 모든 record와 exact 일치했다.
  실제 final target은 모델∩C02±0.3rad box 및 initial±0.15rad 안이며 runner/controller는 이전 보관본과 byte-identical이다.
- 0.5초 OFF54.280113mm/7.851534°, ON34.975339mm/4.871416°를 raw에서 재계산해 일치했다.
  contact는 OFF hip119/thumb3 55, ON hip119/thumb3 119/thumb2 6행이다.
  thumb3 첫 관측은 OFF108step(.450초), ON84step(.350초)이며 LH/어깨는0이다.
  행 수와 관측 시점을 실제 지지력·연속 유지로 단정하지 않는 계획은 정합한다.
  두 오차가 이전 배치보다 감소한 근거로 동일 승인 PI 조건의1초 진단을 추가하는 후속 범위와 정합한다.

### 해소한 Warning

- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/comparison.json:780`의
  input SHA 대상 source_manifest.json이 현재 파일과 다르다. 최초 short 비교 뒤 helper 보관 항목을 추가한 정황이다.
  최초 비교가 읽은 manifest 버전을 해당 기록 SHA와 exact인 별도 snapshot으로 보존하고 시점 차이를 명시하도록 요청했다.
  source_manifest_search.json의 SHA가 최초 comparison의 d45ce6…와 exact인 것을 독립 확인했다.
  초기3항목을 동일 serialization으로 재구성했음을 historical_manifest_validation.json에 명시해 보존했다.
  현재4항목 manifest와 최초 비교를 별도 유지하고 canonical comparison_v2를 생성하므로 Warning을 해소했다.
  저장 native 원자료·물리 수치는 변경하지 않았다. 현재 이 검수 범위의 남은 Critical/Warning/Suggestion 없음.

## 전체6개 PI 실행·decision 판정

- canonical short comparison_v2의4 rows/global checks는 최초 comparison과 exact이며 현재 모든 input SHA가 일치한다.
  보존한 comparison_05s의4 rows는 전체6개 comparison의 첫4 rows와 exact다.
  명령에 선언된 short4+PI4+1초2개의 path 집합/개수는 실제10개 native report와 exact다.
- 추가1초 OFF/ON까지6개 모든 ON PI 갱신을 앞선 방식으로 독립 재계산했다.
  ON6/30/60개 갱신, native 보존 계약·target 경계·포화8/92/212 physics sample 집계가 기록과 일치한다.
  실제 팔 scalar model-limit 위반 최대0.030294°는6개 모두 동일하며 target 범위 통과와 actual state를 구분한다.
- 1초 OFF143.674455mm/36.215772°, ON76.099207mm/14.183879°와 이전 배치의
  OFF143.645622mm/35.962199°, ON121.298052mm/29.759157°를 각각 raw에서 재계산했다.
  개선은 ON에서 관찰되며 OFF의 두 최대오차는 이전보다 커졌다. 전체 안정성 성공으로 일반화할 수 없다.
- decision.json의 모든 contact 행/고유 physics sample/첫·마지막 step/time를 독립 재계산했다.
  1초 thumb3는 OFF113행/36sample/108–143step(.450–.595833초),
  ON187행/69sample/84–160step(.350–.666667초)다. ON thumb2는6행/4sample/85–88step이다.
  LH/어깨 관측0 및 마지막 contact 관측 이후 유지 실패를 고려해 안정 연주로 채택하지 않는 판정이 타당하다.
- full comparison과 decision의 모든 입력 SHA는 현재 파일에서 일치한다.
  후보2를 다음 초기각 진단 기준으로 남기는 범위는 기존 승인 각도/고정 길이/PI와 정합하며
  새 palm controller·gain·gate·학습·물리 설정을 도입하지 않는다.

현재 코드·원자료·판정 범위의 남은 Critical/Warning/Suggestion 없음. 최종 미디어·문서 검수는 후속으로 남는다.

## 최종 미디어·문서 중간 검수

- plot_right_distal_fine.py의 세 기간 축은 sharex=False로 각0.1/0.5/1초 범위를 유지한다.
  current/previous6 rows 및 current static4 rows의 global/row 검사를 모두 확인한 뒤 생성한다.
  raw 기타 candidate-goal p/q를 mm/degree로 그리고, 저장 초기/24step source 형상과
  comparison의 unsigned RH:palm/G:body 값·witness만 같은 view/bounds에 표시한다.
  주황 witness는 computed_zorder=False의 overlay이며 native clearance나 접촉 증명이 아님을 명시한다.
- 두 PNG를 직접 읽고 결과 README `:46`–`:52`의 실제 지원 CLI를 fresh
  /tmp/right_distal_fine_review_reproduction_20261006에서 실행해 exit0 및
  곡선2062×1591/형상1512×1296 전체 pixel exact를 확인했다. 새 native physics는 실행하지 않았다.
- direct manifest raw75개·producer/helper7개·fresh geometry config/XML/mesh40개·출력2개 SHA는 전부 현재 파일과 일치한다.
  static search59 SHA 및 current PI49 SHA도 일치하며 이전 PI의 두 변경 code SHA는 당시 보관본과 exact다.
  artifacts_v1의 당시 plotter와 두 PNG도 이전 manifest SHA와 일치한다.
- contact_drift scope는 ON의84/160step을 OFF에 같은 시각으로 비교하며 OFF 자체108/143step을
  명시하도록 보완됐다.6개의 저장 post-step q/기타 지표와 직전 control held saturation 및 입력 SHA를 확인했다.
  실제 CLI missing_half_regression의 exit1/FileNotFoundError/no-green 기록도 확인했다.
  계획의 마지막 접촉 다음 구간을161–240step으로 고친 경계 표현을 확인했다.

### 해소한 canonical provenance Warning

- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/comparison_v2.json:755`의
  artifacts/plot_manifest.json 예상 SHA340b31aa…는 현재 canonical이나 artifacts_v1 보존본과 일치하지 않는다.
  결과 폴더의 JSON에서 같은 SHA의 버전을 찾지 못했다.
  `/home/ajou/yigyu/3/stability_adapter_2/compare_right_support.py:60`이 파생 미디어 manifest까지
  rglob 입력으로 넣어 재생성 producer와 시점 의존 참조를 만든다.
  예상 버전을 보존·설명하거나 새 비교 provenance에서 파생 media 입력을 제외하고 이전 결과는 보존하도록 요청했다.
  현재 물리 원자료/수치 오류가 아니라 재현 입력 버전 추적 문제다.
  해당 과거 manifest 버전은 복원되지 않았다는 한계를 README와 VISUAL21에 명시하고,
  comparison_v2는 역사 기록으로 보존하며 현재 provenance로 사용하지 않는다.
  현재 compare_right_support.py `:60`–`:64`는 실제 search/source·native raw5·외부 raw4·helper만 해시한다.
  default 검사·수학은 유지되고 새 comparison_v3의 rows/global checks는 v2와 exact다.
  upstream87 SHA가 현재 파일과 모두 일치하며 downstream comparison/artifact/docs를 포함하지 않는다.
  새 canonical producer가 comparison_v3와87 upstream을 직접 읽어 hash를 확인하므로 현재 재현성 Warning을 해소했다.

## canonical v3 최종 검수

- 결과 README 지원 CLI를 fresh /tmp/right_distal_fine_review_reproduction_v3_20261006에서 다시 실행했다.
  exit0, 곡선2062×1591/형상1512×1296 전체 pixel exact이며 producer 수정은 물리 수치·그림 내용을 바꾸지 않는다.
- canonical manifest의150 upstream/raw 파일·7 producer/helper·40 fresh config/XML/mesh·2PNG SHA는 모두 일치한다.
  embedded static87/search59/current PI49 SHA도 현재와 일치한다.
  이전 PI의 두 변경 helper는 당시 archive SHA로 대조했고 v1/v2의 plotter·PNG는 각 과거 manifest와 exact다.
- 문서의10개 새 native 실행과 이전6개 저장 run 구분, 두 초기각만 변경,
  기타 +5mm 고정 목표·고정 rest·기존 PI/PD/solver 보존, 최대오차 표·포화·actual limit·접촉 행 통계를 확인했다.
  이전보다 개선된 ON 결과와 남은76mm/14°·LH0·포화212·마지막 접촉 이후 악화를 함께 설명하며
  안정 연주 채택이나 native geometry 인증을 주장하지 않는다.

결과 README `:41`의 artifacts_v2 설명을 provenance 입력 수집 수정 전으로 고친 문구를 확인해 마지막 Suggestion을 해소했다.
postprocessing_dependency_validation의 media 재생성 뒤 comparison_v3_repeat 전체 JSON이 최초 v3와 exact임을
검수자가 직접 읽어 확인했다. 산출물 변경이 원자료 비교 입력/수치에 영향을 주는 순환 의존성이 제거됐다.

**최종 판정: 문제없음. 남은 Critical/Warning/Suggestion 없음.**
과거 v2의 복원하지 못한 intermediate manifest 한계는 숨기지 않고 보존 기록에 명시한다.
현재 v3는 독립 입력·원자료·수치·producer·미디어·문서 재현성을 확인했다.
검수자가 수정한 프로젝트 파일은 이 review.md뿐이며 새 native physics 실행이나 다른 작업자의 변경 되돌리기는 없었다.
