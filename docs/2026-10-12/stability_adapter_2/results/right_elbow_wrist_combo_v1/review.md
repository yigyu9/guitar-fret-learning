# right_elbow_wrist_combo_v1 별도 변경 검수

2026-10-07(KST) 검수. 실행 자료의2026-10-06 날짜는 보존한다. 별도 change-reviewer.
수정 소유는 이 새 review.md뿐이다. 공유 코드·문서·원자료·기존 동결 기록을 수정하거나 되돌리지 않았다.
새 native 초기화·source search·physics trial은 실행하지 않았다.

**요약 판정: 문제없음.** 남은 Critical/Warning/Suggestion 없음. 이 검수 기록은 최종본으로 동결한다.

## 계획·입력·초기 감사

- `/home/ajou/yigyu/3/stability_adapter_2/RIGHT_ELBOW_WRIST_COMBO.md:8`–`:24`은
  동일 wrist/LA에서 elbow X만 변경하는 범위와 source gate·기존 PI/물리 조건 보존을 명시한다.
  후기 기간 직접 측정,1초 양오차 개선 후보만 OFF,진단과 안정·연주 성공 구분이 구체적이다.
- reference JSON은 이전 negative_pose_late_v1 Wrist−0.005 입력과 byte exact다.
  두 후보는 R_Elbow_x만−0.0025/−0.005rad 변경하고 다른 named 각/설정이 exact다.
  초기 native q는 전체105-slot 중 한 축만−0.002499998/−0.004999995rad 달라 나머지104각은 exact다.
  기준 wrist X−0.42467687010765076rad와 기존 LA를 유지한다.
- 세 audit record는 모든 초기 계약/accepted 조건을 통과했고 source SHA63개가 현재 파일과 일치한다.
  source 음수 pair0·기존 LH 조건을 유지하며 RH unsigned hull 간격은
  기준2.313745mm/후보2.747716·3.180791mm다. 이 거리를 cooked clearance/지지 인증으로 쓰지 않는다.
  기존 audit/comparator/generic plotter/PI runner/controller는 직전 frozen 사본과 현재 바이트가 exact다.

## 9개 ON 원자료·참조 연결·PI와 장력

- comparison의9개 global/row 계약,명시 입력 SHA138개와 각 runtime source SHA가 현재와 일치한다.
  선언 command output9개와 실제 rows path/count가 exact다.
  reference_links3개/manifest는 이전 각 group/wrist_minus0050를 정확히 가리키고 외부 raw5×3 SHA key는
  원본 resolve 경로다. 세 기간 기준 raw5는 원본과 exact이며 긴 기간 raw5는 동일 후보 short prefix와 exact다.
- actual initial q/vel0는 각 audit와 일치하고 native 초기 기타 전체 body state·proximal8개 body·
  PD/caps/limits·goal/solver/LA/PI 구조는 기준과 exact다. 공통 초기 상태/목표 유지와 실제 runtime 상태를 구분한다.
- 저장 pre-step q에서 각6/30/60번 update의 e·적분·raw e+2I·cap/hardbox·applied delta 기준
  blocked rollback 후 재계산·포화를 독립 계산해 exact 확인했다.
  4 physics ticks마다 update하고 나머지 sample은 target/record를 유지한다.
  실제 arm drift/scalar-limit 위반도 native q에서 독립 계산해 row와 exact 일치했다.
  약0.030294–0.030298° actual scalar-limit 위반을 target bounds 통과와 구분한다.
- 위치/정규화 quaternion 상대각을 좌표에서 독립 계산해 trace와 일치했다.
  직전 저장 route points/velocities로 L/Ldot을 계산해 원본 법칙
  L>LA일 때 clip(6000(L−LA)+120Ldot,0,300),그 외0을 적용하면 모든 tick의 다음 trace 장력과1e−8N 이내다.
  현재 post-step 길이와 직전 적용 장력의 시점을 구분하며 고정 LA를 일정 힘으로 해석하지 않는다.
- contact 행/unique sample/firstlast·포화도 raw에서 독립 집계했다.
  1초 기준/−0.0025/−0.005 thumb3는221/134/125행,78/54/42sample,
  86–163/86–141/87–142step이다. LH/어깨 관측0,각1초 ON 포화212 physics samples이며
  counts/끝점은 힘·인과·연속 지지 인증이 아니다.

## 판정·최종 미디어·문서

- 1초 두 후보119.343878mm/28.970036°,119.009665/28.632557은
  기준73.660431/13.502121보다 모두 크다. off_selection=[]/OFF 미실행·두 후보 미채택·현재 진단 reference 유지는
  계획과 정합한다. 오른쪽 distal 세분화 보류와 다음 왼팔 조합 fresh source 방향을 현재 결과와 구분한다.
  새 왼팔 초기 조합/후기 성능은 아직 측정 전이며 이전 왼팔 전체가 미검증이라고 일반화하지 않는다.
  새 제어/gain/goal·p/q feedback·학습이나 안정·연주 성공을 추가하지 않는다.
- 지원 CLI를 새 `/tmp/right_elbow_wrist_combo_review_reproduction_20261007`에 독립 실행해 exit0을 확인했다.
  canonical PNG를 직접 시각 확인했고3×2 실제 기간 패널·세 조건 ON 곡선/범례·mm/degree 단위가 정합한다.
  PNG1902×1884는 재생성본과 RGBA 픽셀 및 파일 바이트가 exact다.
  manifest comparison1개·embedded 입력138개·producer1개·output1개 SHA가 현재 파일과 모두 일치한다.
- 결과 README의9개 오차 표·초기각/source gap·최대 장력15.034899/15.044201/15.044990N·contact/포화와
  VISUAL_REPORT30절·소단계 계획 결과절·PLAN38·adapter README를 대조해 정합함을 확인했다.
  PI는 팔24만 적용하고 주요66 연결 및 몸통9/손가락42/C02하체 목표를 유지한다는 설명이 맞다.
  source proxy/cooked clearance·target bounds/actual q·contact 관측/지지 인증을 구분한다.
  현재 인덱스 링크/실제 줄과 새 빈 CLI 출력 경로 안내를 확인했다.
  검수 상태·보존 manifest/verification/inventory3개는 부모가 후속 갱신/생성할 예정이며
  보존본 readback은 읽기 메시지로만 전달하고 이 동결 기록에 추가하지 않는다.
