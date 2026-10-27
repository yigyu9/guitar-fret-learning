# right_wrist_local_v1 별도 변경 검수

2026-10-06. 별도 change-reviewer. 수정 소유는 이 새 review.md뿐이다.
공유 코드·문서·원자료·기존 동결 기록을 수정하거나 되돌리지 않았다.
새 native 초기화·source search·physics trial은 실행하지 않았다.

## 계획·단일 축 입력·초기 audit

**문제없음**. 현재 요청 범위의 남은 Critical/Warning/Suggestion 없음.
동적 실행·실제 reference symlink·최종 판정·미디어는 아래 후속 검수에서 확인했다.

- `/home/ajou/yigyu/3/stability_adapter_2/RIGHT_WRIST_LOCAL_COMPARE.md:7`–`:23`은
  기준 손목 X의±0.00125rad만 비교하고 기존 C02±0.3rad∩모델/source gate·LA/목표·
  PD/solver/24팔 PI/66 연결과 다른 관절 초기 목표를 유지한다.
  초기 접촉 확인 후 후기 기간을 직접 측정하고1초 양오차 개선 후보만 OFF 비교한다.
  개선 없으면 손목 X의 추가 세분화를 보류하는 조건은 범위 확장/새 controller 도입과 구분된다.
- reference JSON은 이전 negative_pose_late_v1 Wrist−0.005 입력과 byte exact다.
  두 후보는 R_Wrist_x 하나만±0.00125rad로 변경하며 다른 named 각/설정/key 집합이 exact다.
  reference native full q도 이전 native report와 exact다.
  완료 initial_inputs.json의 전체 q를 독립 대조하여 두 후보가±0.001249999rad만 변화하고,
  전체105-slot 중 나머지104각이 exact이며 nominal 오차2e−7rad 이내임을 확인했다.
- 초기 source SHA63개가 현재 파일과 일치하고 세 입력은 모든 초기 계약/accepted 조건을 통과했다.
  native body/goal·PD·C02/model·route/LA·vel0·0step/state 불변 및 기존 LH 조건을 유지한다.
  source 음수 pair는 모두0이며 unsigned RH:palm/G:body 간격은 기준2.313745mm,
  음수 후보2.328165mm, 양수 후보2.299420mm다. source 거리 변화로 실제 지지/안정성이나
  PhysX cooked clearance·관통 깊이를 인증하지 않는다.
- 기존 audit_arm_initial_inputs/compare_arm_initial_trials/generic plotter/PI runner/controller는
  직전 frozen source_final 사본과 현재 바이트가 exact다.
  새 group/on symlink로 이전 group/wrist_minus0050 원자료를 읽는 계획은 기존 comparator와 정합한다.
  초기 검수 시점에는 링크 생성 전이었고 실제 연결/원본 SHA resolve/기간별 재현은 아래에서 확인했다.

## 9개 ON 원자료·실제 참조 링크·판정

**문제없음**. 현재 동적/판정 범위의 남은 Critical/Warning/Suggestion 없음.
최종 현재 문서·미디어는 아래에서 확인했다.

- 새 reference_links 세 group/on symlink와 manifest가 이전 negative_pose_late_v1의
  각 group/wrist_minus0050 directory를 정확히 가리킨다. 외부 raw5×3의 SHA key는 원본 resolve 경로다.
  세 기간 reference raw5는 원본과 exact이고 원본을 쓰는 작업은 수행하지 않았다.
- comparison9개 global/row 계약, 명시 입력 SHA138개와 각 native runtime source SHA가 현재와 일치한다.
  선언 command output9개와 실제 rows path/count가 exact다. initial full q/vel0가 각 accepted audit와
  일치하며 후보는105개 중 wrist X 한 축만 변화한다.
  native 초기 기타 전체 states·proximal8개 body·PD/caps/limits·goal/solver/LA/PI 구조가 기준과 exact다.
  초기 공통 상태·다른 관절 목표 유지와 runtime 실제 몸/관절 상태를 구분한다.
- 저장 pre-step q에서 각6/30/60번 ON update의 e·적분·raw e+2I·cap/hardbox·
  applied delta 기준 blocked rollback 후 재계산·포화를 독립 계산해 exact 확인했다.
  4 physics ticks마다 update하고 나머지 sample은 target/record를 유지한다.
  native q에서 실제 arm drift/scalar-limit 위반도 재계산해 모든 row와 exact 일치했다.
  약0.030298–0.030299° 실제 scalar-limit 위반을 target bounds 통과와 구분한다.
- 긴 기간 raw5는 같은 초기각 short prefix와 exact다. 위치/정규화 quaternion 상대각을
  좌표에서 독립 계산해 trace와 일치했다. 모든 tick의 고정 LA/원본 장력 법칙도 검증했다.
  직전 저장 route points/velocities로 L/Ldot을 계산하고 L>LA일 때
  clip(6000(L−LA)+120Ldot,0,300), 그 외0을 적용하면 다음 trace 실제 장력과1e−8N 이내다.
  현재 post-step 길이와 직전 tick 적용 장력의 시점을 구분한다.
- 양수 후보의0.5초35.351546mm/4.948202°는 기준35.481509/4.991410보다 작지만,
  1초에는 음수117.748239/28.362203, 양수119.007568/29.302065로
  기준73.660431/13.502121보다 두 최대 오차가 모두 크다.
  off_selection=[]/OFF 미실행·두 후보 미채택·현재 진단 reference 유지와
  손목 X 추가 세분화 보류는 계획과 정합한다. 단기 개선·국소 최적·안정/연주 성공을 일반화하지 않는다.
- contact 행/unique physics sample/firstlast 및 포화를 raw에서 독립 집계해 row와 exact 확인했다.
  1초 기준/음수/양수 thumb3는221/143/141행,78/53/55sample,
  86–163/86–143/85–139step이며 thumb2는7/8/4행,6/7/2sample이다.
  LH/어깨/몸통 관측0, 모든1초 ON 포화212 physics samples다.
  접촉 수/끝점을 힘·인과·연속 지지 인증으로 해석하지 않는다.
- decision의 다음 팔꿈치 X 작은 음수 초기각 조합은 향후 fresh source 방향이다.
  이전 팔꿈치 시험은 다른 wrist 초기각이므로 clearance/1초 성능을 새 조합에 대신 적용하지 않는다.
  기존 C02/model box·현재 wrist/LA/goal/root·다른 목표·PD/solver/PI를 유지하며
  이번 결과에 새 초기각 실행·제어/gain·p/q feedback·학습을 추가하지 않는다.

## 최종 미디어·문서 검수 및 동결

**문제없음**. 전체 요청 범위의 남은 Critical/Warning/Suggestion 없음. 이 검수 기록은 최종본으로 동결한다.

- 결과 README의 지원 CLI를 새 `/tmp/right_wrist_local_review_reproduction_20261006`에
  독립 실행해 exit0을 확인했다. canonical PNG를 직접 시각 확인했고 실제 세 기간의3×2 패널·
  세 초기각 ON 곡선/범례·기간별 x축·위치mm/회전degree 단위가 저장 trace와 정합한다.
  PNG1902×1884는 재생성본과 RGBA 픽셀 및 파일 바이트가 exact다.
  manifest comparison1개·embedded 입력138개·producer1개·output1개 SHA가 현재 파일과 모두 일치한다.
- 결과 README의9개 최대 오차 표·초기각/source unsigned gap3개·runtime 최대 장력·contact/포화와
  누적 VISUAL_REPORT29절·소단계 계획 결과절·PLAN37·adapter README를 대조해 정합함을 확인했다.
  24팔 PI/주요66 연결과 몸통9/손가락42/C02하체 초기 목표 유지는 기존 계약과 맞고 실제 상태 고정과 구분된다.
  source proxy/cooked clearance·target bounds/actual q·고정 길이/변하는 힘·contact 관측/지지 인증을 구분한다.
- 양수 후보의0.5초 개선과 두 후보1초 악화/OFF 미실행/현재 진단 reference 유지·손목 X 세분화 보류,
  다음 새 팔꿈치 조합의 fresh source 방향을 구분한 설명이 판정과 일치한다.
  이전 다른 손목 자세의 elbow source/후기 결과로 새 조합을 인증하지 않는다.
  새 제어/gain/goal·기타 p/q feedback·학습이나 안정·연주 성공을 추가하지 않는다.
- 현재 CHANGED_FILES 링크와 실제 줄, 새 CLI 출력 경로 안내를 확인했다.
  검수 상태 링크는 부모가 최종 갱신할 예정이고 보존 manifest/verification/inventory3개는 생성 예정이다.
  이후 보존본 확인은 읽기 결과만 전달하며 이 동결 기록에 추가하지 않는다.
  새 native 실행·원자료/기존 동결 기록 변경 없이 이 review.md만 작성했다.
