# right_wrist_negative_extension_v1 별도 변경 검수

2026-10-06. 별도 change-reviewer. 수정 소유는 이 새 review.md뿐이다.
공유 코드·문서·원자료·기존 동결 기록을 수정하거나 되돌리지 않았다.
검수자는 새 native 초기화·source search·physics trial을 실행하지 않았다.

## 계획·단일 축 입력·초기 audit

**문제없음**. 현재 요청 범위의 남은 Critical/Warning/Suggestion 없음.
동적 실행·실제 reference symlink·최종 판정·미디어는 아래 후속 검수에서 확인했다.

- `/home/ajou/yigyu/3/stability_adapter_2/RIGHT_WRIST_NEGATIVE_EXTENSION.md:7`–`:27`은
  현재 진단 기준에서 손목 X 하나만 추가−0.0025/−0.005rad로 바꾸는 범위를 명시한다.
  기존 C02±0.3rad∩모델/source gate·0N LA·기타 p/q/목표·PD/solver·24팔 PI/66 연결과
  다른 관절 초기 목표를 유지한다. 초기/0.5초 순위로 후기 성능을 추정하지 않고,
  1초 양오차 개선 후보 최대2개 OFF·새 성공 기준 미도입 조건이 구체적이다.
- reference JSON은 이전 negative_pose_late_v1 Wrist−0.005 JSON과 byte exact다.
  두 후보는 R_Wrist_x 한 축만 변경하고 다른 named 각/설정/key 집합이 exact다.
  입력각−0.42717687010765076/−0.42967687010765077rad와 추가 폭은 계획과 일치한다.
- 완료 initial_inputs.json 전체 native q를 독립 대조했다. reference는 이전 Wrist−0.005
  native report의 full q와 exact다. 후보는 R_Wrist_x만−0.002499998/−0.004999995rad 변화하고
  nominal 오차2e−7rad 이내, 전체105-slot 중 나머지104개 native q가 exact다.
  초기 source SHA63개가 현재 파일과 일치하며 모든 초기 계약/accepted 조건을 통과했다.
  초기 body/goal·PD·C02/model·route/절대 길이·vel0·0step/state 불변을 기존 audit에서 확인했다.
- source 음수 pair는 모두0, unsigned RH:palm/G:body 간격은 기준2.313745mm,
  추가−0.0025 2.342578mm, 추가−0.005 2.371586mm다.
  거리 변화 자체를 실제 지지 개선이나 PhysX cooked clearance/관통 깊이로 해석하지 않는다.
  기존 LH 위쪽 반구/국소 넥 조건을 유지한다.
- audit_arm_initial_inputs/compare_arm_initial_trials/generic plotter/PI runner/controller는
  이전 frozen source_final 사본과 현재 바이트가 exact다.
  비교기의 group/on reference를 이전 group/wrist_minus0050로 연결하는 새 read-only symlink 계획은
  기존 raw5 검사 수학과 정합한다. Path.resolve로 SHA 경로를 원본 파일로 남기며 원본을 수정하지 않는다.
  초기 검수 시점에는 링크가 생성 전이었고 실제 연결/원자료 재현은 아래 동적 후속 검수에서 확인했다.

## 9개 ON 원자료·실제 참조 링크·판정

**문제없음**. 현재 동적/판정 범위의 남은 Critical/Warning/Suggestion 없음.
최종 현재 문서·미디어는 아래에서 확인했다.

- 실제 reference_links의 세 group/on symlink와 reference_link_manifest가 이전
  negative_pose_late_v1의 각 group/wrist_minus0050 directory를 정확히 가리킨다.
  외부 raw5×3의 비교 입력 SHA key는 symlink wrapper 경로가 아닌 원본 파일 resolve 경로다.
  reference의 세 기간 raw5는 원본과 exact이고 원본을 쓰는 작업은 수행하지 않았다.
- comparison.json9개 global/row 계약 및 명시 입력 SHA138개와 각 native runtime source SHA가
  현재 파일과 일치한다. 선언 command output9개와 실제 rows path/count가 exact다.
  initial full q/vel0는 각 accepted audit와 일치하고 후보는105개 중 R_Wrist_x 한 축만 변화한다.
  native 초기 기타 body 전체 state·proximal8개 body·PD/caps/limits·goal/solver/LA/PI 구조는 기준과 exact다.
- 저장 pre-step q에서 각6/30/60번 ON update의 e·적분·raw e+2I·cap/hardbox·
  applied delta 기준 blocked rollback 후 재계산·포화를 독립 계산해 exact 확인했다.
  4 physics ticks마다 update하고 나머지 sample은 target/record를 유지한다.
  실제 arm drift 및 scalar-limit 위반도 native q에서 재계산해 row와 exact 일치했다.
  약0.030298–0.030300°의 실제 scalar-limit 위반을 target bounds 통과와 구분한다.
- 모든 긴 기간 raw5는 같은 초기각 short prefix와 exact다. 위치/정규화 quaternion 상대각을
  좌표에서 독립 계산해 trace와 일치했다. 고정 LA와 원본 strap law도 확인했다.
  이전 trace의 route points/velocities로 L/Ldot을 계산하고 L>LA일 때
  clip(6000(L−LA)+120Ldot,0,300), 그 외0을 적용하면 다음 trace 실제 장력과1e−8N 이내다.
  현재 post-step 길이를 직전 tick 적용 장력과 혼동하지 않는다.
- 1초 기준73.660431mm/13.502121° 대비 추가−0.0025는114.478578/27.196448,
  추가−0.005는124.274325/31.128511로 두 최대 오차가 모두 크다.
  off_selection=[]/OFF 미실행·추가각 미채택·현재 진단 reference 유지는 계획과 정합한다.
  단조 개선·국소 최적·안정/연주 성공을 주장하지 않는다.
- contact 행/unique physics sample/firstlast 및 포화를 raw에서 독립 집계해 row와 exact 확인했다.
  1초 기준/추가−0.0025/추가−0.005 thumb3는221/136/121행,78/54/41sample,
  86–163/86–139/87–138step이다. thumb2는7/8/12행,6/6/8sample이다.
  LH/어깨/몸통 관측0이며 모든1초 ON 포화212 physics samples다.
  접촉 행·끝점은 힘·인과·연속 지지 인증이 아니다.
- decision의 다음 Wrist±0.00125rad fresh source 방향은 향후 검사다.
  기존 C02/model box와 LA/goal/root·다른 초기각·PD/solver/PI를 유지하며
  이번 결과에서 새 초기각 실행·제어/gain·기타 p/q feedback·학습을 추가하지 않는다.

## 최종 미디어·문서 검수 및 동결

**문제없음**. 전체 요청 범위의 남은 Critical/Warning/Suggestion 없음. 이 검수 기록은 최종본으로 동결한다.

- 결과 README의 지원 CLI를 새 `/tmp/right_wrist_negative_extension_review_reproduction_20261006`에
  독립 실행해 exit0을 확인했다. canonical PNG를 직접 시각 확인했고 실제 세 기간의3×2 패널·
  세 초기각 ON 곡선/범례·기간별 x축·위치mm/회전degree 단위가 저장 trace와 정합한다.
  PNG1902×1884는 재생성본과 RGBA 픽셀 및 파일 바이트가 exact다.
  manifest comparison1개·embedded 입력138개·producer1개·output1개 SHA가 현재 파일과 모두 일치한다.
- 결과 README의9개 오차 표·초기각/source unsigned gap3개·runtime 최대 장력·접촉 행/sample/시점·
  포화와 누적 VISUAL_REPORT28절·소단계 계획 결과절·PLAN36·adapter README를 대조해 정합함을 확인했다.
  팔24 PI/주요66 연결과 몸통9/손가락42/C02하체 초기 목표 유지는 기존 계약과 맞는다.
  source proxy/cooked clearance·target bounds/actual q·고정 길이/변하는 힘·contact 관측/지지 인증을 구분한다.
  전체105-slot 중 변경축 하나와 나머지104각 설명도 일치한다.
- 추가각 미채택/OFF 미실행/현재 진단 reference 유지와 다음±0.00125rad fresh source 방향을 구분한다.
  안정·연주 성공, 단조 효과/국소 최적이나 새 기타 p/q feedback을 이번 결과로 주장하지 않는다.
  현재 CHANGED_FILES의 실제 링크·줄과 비어 있는 새 CLI 출력 경로 안내를 확인했다.
  검수 상태 링크는 부모가 최종 갱신할 예정이고 보존 manifest/verification/inventory3개는 생성 예정이다.
  이후 보존본 확인은 읽기 결과만 전달하며 이 동결 기록에 추가하지 않는다.
  새 native 실행·원자료/기존 동결 기록 변경 없이 이 review.md만 작성했다.
