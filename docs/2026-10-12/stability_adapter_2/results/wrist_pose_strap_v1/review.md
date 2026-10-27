# wrist_pose_strap_v1 별도 변경 검수

2026-10-06. 별도 change-reviewer. 수정 소유는 이 새 review.md뿐이다.
공유 코드·문서·원자료·기존 동결 기록을 수정하거나 되돌리지 않았다.
새 native 초기화·source search·physics trial은 실행하지 않았다.

## 계획·고정 길이 입력·새 저장 비교기

**문제없음**. 현재 요청 범위의 남은 Critical/Warning/Suggestion 없음.
긴 기간 동적 결과·최종 판정·미디어는 아래 후속 검수에서 확인했다.

- `/home/ajou/yigyu/3/stability_adapter_2/WRIST_POSE_STRAP_COMPARE.md:7`–`:25`은
  새 Wrist−0.005 초기 자세를 유지하고 길이만 바꾸는 비교, 첫 장력과 run 중 고정 길이,
  기간별 진단/1초 양오차 개선 후보 최대2개 OFF, 성공 기준 미확정을 명시한다.
  24팔 PI·66 연결과 fingers42/몸통9/C02하체 목표·root·기타+5mm p/q·PD/solver가 보존된다.
- 기존 입력 생성기를 변경하지 않고 만든 strap_inputs.json의5개 record를 독립 대조했다.
  legacy와0N은 중복이며 나머지 설정은 이전 Wrist−0.005 JSON과 exact다.
  L0=1.1010801317960974m, LA=L0−T0/6000의0/5/10/20N 길이가 exact이고
  초기 법칙 장력의 부동소수 오차는1e−9N 이내다. 전신 source 음수 pair0/기존 LH 조건을 통과한다.
  모든 초기 계약과 명시 source SHA57개가 현재 파일과 일치한다.
- `/home/ajou/yigyu/3/stability_adapter_2/compare_strap_initial_trials.py:55`–`:75`의
  전체 initial targets/native state0 동일, 길이 외 settings 동일, 실제 첫 장력,
  초기 모델/팔 box·vel0·run 내 고정 길이·PD/goal/solver/PI 구조 및 기간 prefix 검사에 누락을 발견하지 않았다.
  source 초기 audit가 일부 관절 그룹만 검사하는 점을 실제 full target/state0 비교와
  외부0N raw5 재현으로 보강한다. target bounds와 실제 안정성 인증을 구분한다.
- 같은 파일`:86`–`:100`은 실제 raw6·runtime source·audit·명령·외부 reference raw5·자기 코드만
  명시적으로 해시한다. 결과 JSON 재귀 수집이나 media/decision 해시 순환을 도입하지 않는다.
  정상4개 short 비교 CLI를 새 `/tmp/wrist_pose_strap_review_short_20261006.json`으로 실행해 exit0,
  global/row 통과 및97개 입력 SHA 현재 일치를 확인했다.
- 신규 비교기의 누락 회귀를 `/tmp/wrist_pose_strap_review_missing_short_20261006`에서 검증했다.
  원자료 directory를 읽기 전용 symlink로 연결하고 선택된 load_20n만 제외했다.
  선언 명령4개를 유지하자 실제 CLI exit1이며 selected short/declared coverage 두 검사가 false였다.
  누락을 성공 판정으로 남기지 않는다. 기존 raw/code/output은 수정하지 않았다.
- 완료된 short4개의 native state0 전체가 동일하고 길이는 각 run에서 고정이다.
  실제 첫 장력0/5/10/20N은 source 법칙과 일치한다. 기타 최대 오차는 각각
  6.872551mm/1.519351°,6.799980/1.558750°,6.914132/1.691398°,7.702071/2.164250°다.
  초기 장력을 runtime 일정 힘으로 해석하거나 단기 tradeoff를 후기 성능으로 추정하지 않는다.

## 12개 ON 동적 원자료·선정 판정

**문제없음**. 현재 동적/판정 범위의 남은 Critical/Warning/Suggestion 없음.
최종 미디어·현재 문서는 아래에서 확인했다.

- comparison.json의12개 global/row 계약과 명시 입력 SHA157개가 현재 파일과 일치한다.
  선언 command output12개와 실제 rows12개 path/count가 exact다. 모든 초기 전체 native state/q/vel0가
  길이 조건 사이에 동일하며, LA만 다르고 run 안에서 고정된다.
- 저장 pre-step actual q에서 각6/30/60번 ON update의 e·적분·raw e+2I·cap/최종 hardbox·
  applied delta 기반 blocked rollback 후 재계산·포화를 독립 계산해 exact 확인했다.
  update는4 physics ticks마다이고 나머지 target/record는 유지된다. 초기 target bounds와 실제 q를 구분한다.
  actual scalar-limit 위반도 raw native q에서 재계산해12개 row와 exact 일치했다(약0.03023–0.03030°).
- 각 긴 기간 raw5는 같은 길이 short prefix와 exact이고,0N의 세 기간 raw5는 이전
  negative_pose_late_v1 Wrist−0.005 ON과 exact다. 위치/정규화 quaternion 상대각을
  독립 계산해 trace와 일치함을 확인했다.
- 모든 physics tick의 장력을 직전 저장 route points/velocities에서 독립 계산했다.
  L>LA일 때 clip(6000(L−LA)+120Ldot,0,300), 그렇지 않으면0이 다음 trace의 실제 적용 장력과
  1e−8N 이내로 일치한다. 현재 post-step 길이와 직전 tick의 힘을 혼동하지 않는다.
  첫 장력0/5/10/20N과 run 중 최대15.034899/17.578706/15.029217/53.253337N을 구분한다.
- 1초 최대 위치/회전 오차는0N73.660431mm/13.502121°,5N122.290835/32.067454,
  10N101.491973/23.490280,20N155.299893/65.533423이다.
  모두0N보다 두 오차가 작지 않으므로 off_selection=[]/OFF 미실행은 계획과 정합한다.
  decision은 기존 Wrist−0.005/0N을 다음 진단 기준으로만 유지하며 안정·연주 성공을 주장하지 않는다.
  다음1/2N 비교 방향은 기존0–5N 사이의 향후 진단이며 단조 효과나 새 제어/gain/goal을 가정하지 않는다.
- contact raw에서 행/unique physics sample/firstlast 및 포화 sample 수를 독립 집계해 row와 exact 확인했다.
  1초0/5/10/20N의 thumb3는221/128/122/61행,78/44/43/23sample,
  관측 범위86–163/87–130/89–131/94–116step이다.
  20N에서만 Torso2행/1sample/step231(0.9625초)가 있고 LH/어깨는 모든 조건0이다.
  모든1초 ON 포화212 physics samples이며 관측 수/끝점으로 힘·인과·연속 지지를 인증하지 않는다.

## 최종 미디어·문서 검수 및 동결

**문제없음**. 전체 요청 범위의 남은 Critical/Warning/Suggestion 없음. 이 검수 기록은 최종본으로 동결한다.

- 결과 README의 지원 CLI를 새 `/tmp/wrist_pose_strap_review_reproduction_20261006`에 독립 실행해
  exit0을 확인했다. canonical PNG를 직접 시각 확인했고 실제3×2 기간 패널·네 길이 ON
  곡선/범례·기간별 x축·위치mm/회전degree 단위가 저장 결과와 정합한다.
  PNG1902×1884는 재생성본과 RGBA 픽셀 및 파일 바이트가 exact다.
  manifest의 comparison1개·embedded 입력157개·producer1개·output1개 SHA가 현재 파일과 모두 일치한다.
- 결과 README의12개 표,4개 절대 길이·최대 runtime 장력·접촉 행/sample/포화와
  VISUAL_REPORT26절·소단계 계획 결과절·PLAN34·adapter README를 대조해 정합함을 확인했다.
  고정 초기 LA와 변하는 실제 힘, 초기0N과 runtime 무장력 여부를 구분한다.
  24팔 PI/main66 연결과 fingers42/몸통9/C02하체 목표 유지가 기존 계약과 맞으며,
  target bounds 통과를 actual state 고정이나 안정·연주 성공으로 해석하지 않는다.
  contact counts는 지지력·인과·연속 접촉 인증과 구분된다.
- 추가 OFF 미실행/새 길이 미채택/0N 진단 reference 유지와 다음1/2N 진단을 구분한다.
  새 제어/gain/goal이나 동적 길이를 이번 결과에 도입하지 않는다.
  새 native 실행·원자료/기존 기록 변경 없이 이 review.md만 작성했다.
