# small_preload_v1 별도 변경 검수

2026-10-06. 별도 change-reviewer. 수정 소유는 이 새 review.md뿐이다.
공유 코드·문서·원자료·기존 동결 기록을 수정하거나 되돌리지 않았다.
검수자는 새 native 초기화·source search·physics trial을 실행하지 않았다.

## 계획·0/1/2N 입력·새 초기 감사기

**문제없음**. 현재 요청 범위의 남은 Critical/Warning/Suggestion 없음.
동적 실행·최종 판정·미디어는 아래 후속 검수에서 확인했다.

- `/home/ajou/yigyu/3/stability_adapter_2/SMALL_PRELOAD_COMPARE.md:7`–`:26`은
  동일 Wrist−0.005 자세에서 기존0–5N 안의1/2N 길이만 비교하는 계약을 명시한다.
  기존0N 세 기간 raw5 재현, 짧은 어깨 접촉 확인 후 후기 기간 직접 측정,
  1초 양오차 개선 후보 최대2개만 OFF 비교, 진단 기준과 안정·연주 성공 구분이 구체적이다.
  24팔 PI/66 연결·fingers42/몸통9/C02하체 목표·root·기타+5mm p/q·PD/solver를 유지한다.
- 세 JSON을 독립 대조했다.0N은 이전 wrist_pose_strap_v1의0N 입력과 byte exact다.
  1/2N은 LA=L0−T0/6000만 변경하고 모든 다른 설정이 exact다.
  L0=1.1010801317960974m이며1N1.1009134651294308m,2N1.1007467984627641m다.
  초기 장력 설정을 runtime 일정 힘으로 해석하지 않는다.
- `/home/ajou/yigyu/3/stability_adapter_2/audit_strap_initial_inputs.py:22`–`:65`는
  실제 fresh 환경의 전체 initial q/body states·기타 states/goal·PD properties·route/66 layout을
  기준과 비교하며 vel0·모델 한계·기존0–5N 길이/장력 범위와0step/state 불변을 검사한다.
  기존 source 음수 pair0/LH 위쪽 반구/국소 넥 조건을 유지하고 첫 법칙 장력을 직접 계산한다.
  explicit 입력/기존 source/자기 코드 SHA를 시작·끝 확인하며 결과 덮어쓰기를 거부한다.
  기존 comparator의 phase/records/checks/settings/initial law/source SHA schema와 정합한다.
  AST 문법 검사를 통과했다.
- 완료된 strap_inputs.json의 세 record 모두 accepted/초기 계약 통과이고 source/input SHA61개가
  현재 파일과 일치한다. 첫 법칙 장력0/1/2N은1e−9N 이내이며 source 음수 pair0,
  LH up-dot0.926704·국소 넥 아래24.622mm 조건을 유지한다.
  source query를 PhysX cooked clearance·실제 관통 깊이·지지력 인증으로 쓰지 않는다.
- 기존 pose_strap_inputs/compare_strap_initial_trials/generic plotter/PI runner/controller는
  이전 wrist_pose_strap_v1 frozen source_final 사본과 현재 바이트가 exact다.
  새 감사기와 입력/계획만 추가했으며 기존 물리·제어·검사 수학은 수정하지 않았다.

## 9개 ON 동적 원자료·선정 판정

**문제없음**. 현재 동적/판정 범위의 남은 Critical/Warning/Suggestion 없음.
최종 현재 문서·미디어는 아래에서 확인했다.

- comparison.json의9개 global/row 계약과 명시 입력 SHA139개가 현재 파일과 일치한다.
  선언 command output9개와 실제 rows path/count가 exact다. 실제 전체 initial native state/q/vel0는
  모든 길이 조건에서 동일하고 길이 외 settings·PD/caps/limits·goal/solver·PI 구조와 주기를 유지한다.
  새 auditor의 source SHA도 현재와 일치하며 기존 검사기/실험 코드를 바꾸지 않는다.
- 저장 pre-step actual q에서 각6/30/60번 ON update의 e·적분·raw e+2I·cap/최종 hardbox·
  applied delta 기준 blocked rollback 후 재계산·포화를 독립 계산해 exact 확인했다.
  update는4 physics ticks마다이며 나머지 sample은 target/record를 유지한다.
  actual arm drift와 scalar-limit 위반을 native q에서 독립 계산해 모든9개 row와 exact 일치했다.
  실제 scalar-limit 위반 약0.030295–0.030298°는 target bounds 통과와 구분한다.
- 0N 세 기간 raw5는 이전 negative_pose_late_v1 Wrist−0.005 ON과 exact다.
  모든 긴 기간 raw5는 동일 길이 short prefix와 exact이고 위치/정규화 quaternion 상대각은
  저장 좌표에서 독립 계산해 trace와 일치했다.
- 첫 장력0/1/2N, run 내 고정 LA 및 모든 physics tick의 실제 장력을 독립 대조했다.
  직전 저장 route points/velocities로 L/Ldot을 계산하고 L>LA일 때
  clip(6000(L−LA)+120Ldot,0,300), 그 외0을 적용하면 다음 trace의 실제 적용 장력과1e−8N 이내다.
  현재 post-step 길이와 직전 tick의 장력을 혼동하지 않는다. 각1초 최대 장력은
  15.034899/15.463361/15.991668N이며 초기1/2N을 일정 힘으로 해석하지 않는다.
- 1N은0.1초6.841501mm/1.519078°,0.5초35.468898/4.990968로0N보다 두 최대 오차가 작지만,
  1초79.221741/15.027785로0N73.660431/13.502121보다 모두 크다.
  2N도1초120.773180/30.086380로 두 오차가 크다.
  off_selection=[]/OFF 미실행·새 길이 미채택·0N 진단 reference 유지는 계획과 정합한다.
  초기 개선으로 후기 성공이나 장시간 유지 성능을 추정하지 않는다.
- contact 행/unique physics sample/firstlast 및 포화를 raw에서 독립 집계해 row와 exact 확인했다.
  1초0/1/2N thumb3는221/194/137행,78/74/53sample,86–163/86–160/86–138step이며
  thumb2는7/4/6행,6/4/4sample이다. LH/어깨/몸통 contact 관측은0이다.
  모든1초 ON 포화212 physics samples이고 종료 속도와 큰 drift가 남는다.
  관측 행·끝점은 힘·인과·연속 지지 인증이 아니다.
- decision의 다음 작은 Wrist 초기각 진단은 향후 fresh source 검사 후 기존 C02±0.3/model box에서
  시행할 방향이다. 이번 결과에 새 초기각 실행·제어/gain·기타 goal·p/q feedback·학습을 추가하지 않는다.

## 최종 미디어·문서 검수 및 동결

**문제없음**. 전체 요청 범위의 남은 Critical/Warning/Suggestion 없음. 이 검수 기록은 최종본으로 동결한다.

- 결과 README의 지원 CLI를 새 `/tmp/small_preload_review_reproduction_20261006`에 독립 실행하여
  exit0을 확인했다. canonical PNG를 직접 시각 확인했고 실제 세 기간의3×2 패널·세 길이 ON
  곡선/범례·기간별 x축·위치mm/회전degree가 저장 trace와 정합한다.
  PNG1902×1884는 재생성본과 RGBA 픽셀 및 파일 바이트가 exact다.
  manifest comparison1개·embedded 입력139개·producer1개·output1개 SHA가 현재 파일과 모두 일치한다.
- README의9개 표·3개 절대 길이·runtime 최대 장력·접촉/포화와 누적 VISUAL_REPORT27절,
  소단계 계획 결과절·PLAN35·adapter README를 대조했다.
  adapter README:90의 `0.5초만` 표현은0.1초 개선 관측을 누락하여 지적했고,
  현재 `0.1/0.5초에 조금 줄었고`로 교정되어 Warning을 해소했다.
  초기0/1/2N 입력3건과 ON9개,24팔 PI/주요66 연결·다른 관절 초기 목표 유지 설명이 맞다.
  고정 LA/변하는 힘·target bounds/actual q·contact 관측/지지 인증과 다음 진단을 구분한다.
  OFF 미실행/새 길이 미채택/0N 진단 reference 유지 및 안정·연주 미달성 설명은 원자료와 정합한다.
- CHANGED_FILES의 현재 링크와 실제 줄 번호를 확인했다. source_final_manifest/verification/inventory
  3개 링크는 부모가 검수 완료 후 생성할 예정 파일로 구분했으며 최종 보존본 readback은 후속 읽기 확인 대상이다.
  README의 재생성 출력은 비어 있는 새 경로를 사용한다는 보완도 확인했다.
  새 native 실행·원자료/기존 동결 기록 변경 없이 이 review.md만 작성했다.
