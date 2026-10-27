# negative_pose_late_v1 별도 변경 검수

2026-10-06. 별도 change-reviewer. 수정 소유는 이 새 review.md뿐이다.
공유 코드·문서·원자료·기존 동결 검수 기록을 수정하거나 되돌리지 않았다.
검수자는 새 native 초기화·source search·physics trial을 실행하지 않았다.

## 계획·입력 복사·초기 audit

**문제없음**. 현재 요청 범위의 남은 Critical/Warning/Suggestion 없음.
동적 결과 및 미디어는 아래 후속 검수에서 확인했다.

- `/home/ajou/yigyu/3/stability_adapter_2/NEGATIVE_POSE_LATE_DIAGNOSTIC.md:6`–`:20`은
  기존 accepted 음수 초기각의 후기 동작을 직접 측정하는 기간 선택을 명시한다.
  0.1초 어깨 접촉 확인 후 0.5/1초를 측정하며 0.5초 개선을 연장 조건으로 쓰지 않는다.
  초기 source gate·각 범위·PD/gain·고정 길이·PI 제어와 성공 기준을 바꾸지 않는다.
  1초 양오차 개선 후보 최대2개만 세 기간 OFF 비교하는 조건이 구체적이다.
- input_recipe.json의 네 copied_from/input_path 파일 바이트와 SHA를 독립 대조해 모두 exact 확인했다.
  reference는 기존 fine c02 기준이며 각 후보의 설정 차이는 R_Wrist_x −0.0025/−0.005rad 또는
  R_Elbow_y −0.00125rad 하나뿐이다. 기타 +5mm 초기 목표·LA 및 다른 설정은 reference와 exact다.
- 완료된 initial_inputs.json의 전체 native q를 독립 대조했다.
  reference 대비 actual 변화는 Wrist_x −0.002499998/−0.004999995rad,
  Elbow_y −0.001250029rad이며 해당 축 외 q가 exact이고 nominal 오차는 2e−7rad 이내다.
  네 초기 계약 모두 통과하고 source/input SHA64개가 현재 파일과 일치한다.
  C02±0.3rad∩모델·비팔 q/proximal body·기타 전체 state/goal·native PD·root·route/절대 길이·
  LH 조건·vel0·0step/state 불변을 초기 audit에서 확인했다.
- 네 입력은 source 음수 pair0이며 accepted다. unsigned RH:palm/G:body 간격은
  reference2.256704mm, Wrist−0.0025 2.285141mm, Wrist−0.005 2.313745mm,
  ElbowY−0.00125 2.178539mm다. source proxy를 cooked clearance·힘·안정성 인증으로 해석하지 않는다.
- audit/compare/generic plotter 및 기존 PI runner/controller는 이전 음수 결과의 frozen source_final 사본과
  현재 바이트가 일치한다. 이번 변경은 기존 입력 복사와 새 진단 계획이며 runtime 코드 변경이 아니다.

## 12개 ON·선택된 3개 OFF 저장 실행 검수

**문제없음**. 현재 동적 원자료 범위의 남은 Critical/Warning/Suggestion 없음.
최종 비교/판정 문서와 미디어는 아래에서 확인했다.

- 12개 ON의 comparison_on.json global/row 계약과 명시 입력 SHA157개가 현재 파일과 일치한다.
  완료된 ON12/OFF3의 선언 command output15개와 실제 report15개 path/count가 exact다.
  모든 native report 계약·initial full q/vel0·accepted 입력 매칭을 확인했다.
- 각 ON의 6/30/60 control update를 저장된 pre-step actual q에서 독립 계산했다.
  e, 제안 적분, raw e+2I, ±0.15 cap/최종 hardbox, 실제 적용량을 이용한 blocked rollback 후
  재계산 및 saturation record가 exact다. 4 physics ticks마다 update하며 나머지 sample은 target/record를 유지한다.
  OFF3은 모든 최종 팔 목표=초기24각이고 적분/δ/포화0이다. 새 제어기·gain·보정 cap을 도입하지 않는다.
- 세 기간 reference raw5는 이전 fine c02 ON과 exact다. 모든 긴 실행 raw5는 같은 mode/name의
  short prefix와 exact이며 Wrist−0.005 OFF/ON의 initial native state 전체도 exact다.
  위치 오차를 좌표에서, 회전 오차를 정규화 quaternion 상대각에서 독립 계산해 trace와 일치했다.
- 1초 ON은 reference76.099207mm/14.183879°, ElbowY−0.00125 112.841326/26.625913,
  Wrist−0.0025 116.186913/27.908480, Wrist−0.005 73.660431/13.502121이다.
  Wrist−0.005의 0.5초35.481509mm/4.991410°는 기준34.975339/4.871416보다 크지만
  1초에서는 두 오차가 작다. off_selection.json의 해당 후보 하나 선택은 이번 후기 진단 계획과 정합한다.
  이 차이를 안정·연주 성공이나 더 긴 기간 성능으로 일반화하지 않는다.
- Wrist−0.005 OFF는 0.1초6.872551mm/1.519351°, 0.5초54.801345/7.940387,
  1초144.260293/36.309554다. 0.1초 ON/OFF 기타 오차는 같고 긴 기간은 기존 PI가 오차를 줄이지만
  1초 ON에도73.660mm/13.502° 드리프트가 남는다.
- contact raw의 행/unique physics sample/firstlast를 독립 집계했다.
  1초 Wrist−0.005 ON thumb3는221행/78sample/86–163step, thumb2는7행/6sample/86–91;
  OFF thumb3는113행/37sample/109–145step이다. 기준 ON thumb3는187행/69sample/84–160이다.
  모든 실행 LH/어깨 관측0이며 이 수치는 힘·원인·연속 지지 인증이 아니다.
  ON 포화는0.1/0.5/1초 각각8/92/212 held physics samples다. OFF는0이다.

## 최종 comparison15개·diagnostic reference 판정

**문제없음**. 최종 비교/판정 범위의 남은 Critical/Warning/Suggestion 없음. 미디어는 아래에서 확인했다.

- comparison.json의15개 global/row 계약과 명시 입력 SHA176개를 현재 파일에서 확인했다.
  이전 comparison_on.json의12개 ON rows가 최종 비교에 exact 보존된다.
  actual arm drift/모델 scalar-limit 위반을 native saved q에서 독립 계산하여 모든15개 row와 exact 일치했다.
  선택된 Wrist−0.005의 actual scalar-limit 위반은0.030298°로 target bounds 통과와 실제 상태를 구분한다.
- decision.json의1초 기준 대비 감소2.438775909mm/0.681758472°를 독립 계산해 exact 확인했다.
  Wrist−0.005는 다음 진단용 reference로만 선택한다. 기타 최대73.660mm/13.502° 오차,
  종료 속도 비영·LH접촉0·PI 포화212가 남아 안정·연주 성공이나 장시간 유지로 채택하지 않는다.
  이전 짧은 기간 순위가 후기 동작을 예측하지 못한 관측을 결과 범위 안에서 설명한다.
- 다음 고정 초기 strap 길이와 이 초기각의 결합 비교 방향은 향후 진단이다.
  기존 coarse c01의 strap 결과를 새 wrist pose의 결과로 대신하지 않으며,
  새 task-feedback/controller·gain·각 범위·goal 변경을 이번 결과가 승인한 것으로 해석하지 않는다.

## 최종 미디어·문서 검수 및 동결

**문제없음**. 전체 요청 범위의 남은 Critical/Warning/Suggestion 없음. 이 검수 기록은 최종본으로 동결한다.

- 변경하지 않은 generic plotter의 지원 CLI를 새
  `/tmp/negative_pose_late_review_reproduction_20261006`에 독립 실행하여 exit0을 확인했다.
  canonical PNG를 직접 시각 확인했다. 실제 세 기간별 3×2 패널, 네 초기각 ON과 선택 후보 OFF,
  각 기간 x축·mm/degree 단위·OFF 점선 구분과 그래프의 후기 변화가 저장 trace와 정합한다.
  재생성 PNG1902×1884는 canonical과 RGBA 픽셀 및 파일 바이트가 모두 exact다.
  manifest의 comparison1개·embedded 입력176개·producer1개·output1개 SHA가 모두 현재 파일과 일치한다.
- 결과 README의15개 표 수치와 누적 VISUAL_REPORT25절, 소단계 계획 결과절/PLAN33/adapter README를 대조했다.
  0.5초 순위와1초 순위 차이, diagnostic reference만 선택, 큰 잔여 오차/속도·포화/LH0,
  접촉 관측의 힘·인과·연속성 한계와 기타 p/q feedback 부재를 구분한 설명이 원자료와 정합한다.
  README의 `24팔 PI와 주요66관절 제어 연결`은 기존 구조와 일치한다.
  fingers42/몸통9/C02하체는 목표 유지이며 물리적 state 고정이나66개 전체 PI 보정으로 해석하지 않는다.
- 새 native 실행·원자료 수정·기존 동결 기록 수정 없이 이 review.md만 작성했다.
