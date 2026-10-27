# right_elbow_retention_v1 별도 변경 검수

2026-10-06. 별도 change-reviewer. 수정 소유는 이 review.md뿐이다.
공유 작업자의 코드·문서·원자료·기존 보관본을 수정하거나 되돌리지 않았다.
검수자는 새 native 초기화·source search·physics trial을 실행하지 않았다.

## 계획·입력5개 및 공용 audit 판정

**문제없음**. 현재 검수 범위에서 남은 Critical/Warning/Suggestion 없음.
동적 원자료·미디어·최종 문서는 아래 검수에서 확인했다.

- `/home/ajou/yigyu/3/stability_adapter_2/RIGHT_ELBOW_RETENTION_COMPARE.md:6`–`:17`의
  reference/Elbow_x±0.0025/Elbow_y+.005/Elbow_z+.005의5개와 accepted 최대3개/fallback,
  0.5초 양오차 개선만1초 연장·같은 초기 OFF 진단은 기존 초기각·PI 범위와 정합한다.
  source query를 실제 cooked clearance/지지 성공으로 사용하지 않으며 새 controller/gain/gate를 도입하지 않는다.
- `/home/ajou/yigyu/3/stability_adapter_2/audit_arm_initial_inputs.py:26`–`:40`은 별도 C02 native q와
  기준 q/PD/고정 proximal body/전체 기타 state·goal/route·length를 확보한다.
  `:51`–`:61`이24팔 밖의 초기 q·C02±0.3rad∩model·고정 body·vel0·목표/PD·
  고정LA/route·main66/arm24·0step/state불변 및 기존 source/LH gate를 확인한다.
  후보 input 경로와 generator/helper/C02를 포함한 source SHA를 기록하고 기존 audit를 덮어쓰지 않는다.
- 공용 audit 자체의 허용 집합은24팔이며 이번 계획의 Elbow3 집합보다 넓다.
  재사용 의도와 구분해 이번5개 record의 전체 native 초기 q를 독립 대조했다.
  reference는 이전 fine candidate_02 native 초기 q와 exact이며 각 후보는 지정 R_Elbow 한 축만 변한다.
  actual delta는±0.002499998/+0.004999995rad로 nominal과2e−7rad 이내이고 나머지 q는 exact다.
- 모든 초기 계약과 input/source SHA 현재 readback이 일치한다.
  reference/x_minus0025/x_plus0025/y_plus0050/z_plus0050의 unsigned RH:palm/G:body 거리는
  2.256704/2.691345/1.821231/2.565990/3.330104mm다.
  x_plus0025만 전신 source 음수 pair1로 거부되고 나머지4개 통과하여 계획의 x_minus fallback과 정합한다.
  양의 unsigned 가까움만으로 native 접촉력·연속 지지·안정성을 주장하지 않는다.
- wrist 단위의 최종18개 source 사본 SHA 및 manifest에 포함된 현재 Python source SHA를 읽기 전용으로 확인해
  모두 일치했다. 이전 wrist review.md는 이미 snapshot됐으므로 수정하지 않았다.

검수자가 쓴 프로젝트 파일은 이 새 검수 기록뿐이다.

## 비교 helper·0.5초8개 및 전체10개 원자료

**문제없음**. 현재 코드·원자료·판정 범위의 남은 Critical/Warning/Suggestion 없음.

- `/home/ajou/yigyu/3/stability_adapter_2/compare_arm_initial_trials.py:36`–`:68`은
  accepted named 입력과 전체 native target/audit 초기각·저장 initial q/vel0를 exact로 대조한다.
  arm24 밖 q, mode·고정length·PD/model/diagnosticbounds/goal/route/controller/physics/controlHz,
  final δ/관절 bounds·4step schedule·sample count·current execution source를 확인한다.
  `:85`–`:95`는 accepted unique selection/fixed required short set/declared path·count와 이전 raw5를 검증한다.
  실제 audit/selection/native raw6/commands/source/외부raw5/helper만 해시하며 파생 media/docs/comparison은 입력이 아니다.
- 0.1/0.5초8개와 추가1초2개의 모든 ON PI update를 stored pre-step actual q에서 독립 재계산했다.
  actual error·integral·raw clip·hardbox·blocked rollback 후 재계산·saturation이 기록과 exact다.
  ON6/30/60 update, final target δ±0.15rad/C02∩model box 및 non-update sample의 target/integral 기록 hold를 확인했다.
  native 초기 q는 각각 accepted audit의 full vector와 exact이며 initial velocity는0이다.
- 0.5초 기준34.975339mm/4.871416°, X−35.265762/4.942168,
  Y+33.889111/4.696079, Z+35.669838/5.012532를 raw에서 재계산해 일치했다.
  모든0.5초 ON의 포화는92 physics samples다. Y+만 두 최대오차가 작아 long_selection의 단일 후보가 된 기록과 정합한다.
- 실제 pure CLI를 read-only symlink fixture /tmp/right_elbow_missing_half_reviewer_20261006에서 실행했다.
  hold_05s/x_minus0025 한 실행을 뺀7 rows는 개별 계약을 통과하지만 declared_run_coverage_exact=false/exit1로 거부됐다.
  새 native 실행은 없었고 임시 fixture/output만 /tmp에 저장했다.
- 전체10개 declared path/count는 실제 rows와 exact이고 최초 comparison_05s8 rows는 전체 결과에서 exact 보존된다.
  각 기간 reference ON raw5(states/trace/contacts/leg_torques/controls)는 이전 fine candidate_02와 exact다.
  긴1초의 raw5 short prefix도 exact다.146개 명시 input SHA가 현재 파일과 일치한다.
  root의 실제 후처리 CLI repeat 전체 JSON도 current comparison과 exact인 것을 직접 읽었다.
- 1초 reference76.099207mm/14.183879°, Y+118.323471mm/29.067896°를 raw에서 독립 계산했다.
  차이+42.224265mm/+14.884016°가 decision과 일치하며 양쪽의 포화는212 physics samples다.
  실제 모델 scalar-limit 편차와 큰 기타 drift는 target bounds 검사 통과와 구분해야 한다.
- 모든 contact row/unique sample/firstlast를 raw에서 독립 대조했다.
  1초 Y+ thumb3는147행/55sample/82–143step(.341667–.595833초), thumb2는5행/4sample/83–86step;
  기준 thumb3는187행/69sample/84–160step(.350–.666667초), thumb2는6행/4sample/85–88step이다.
  LH/어깨 관측0이고 첫·마지막 접촉을 힘/원인/연속 지지로 일반화하지 않는다.
- 소단계 계획 `:36`–`:49`, PLAN31 및 adapter README의 후보 미채택·fine c02 유지·X−/Z+1초 미측정,
  유망1초 후보가 없으므로 OFF 미실행/새 OFFON 이득 주장 없음이 실제 실행과 정합한다.
  다음 작은 음수 Elbow_y의 fresh source 검사는 방향 제안이며 새 controller/gain/gate/goal 변경을 도입하지 않는다.

최종 미디어·결과 문서는 후속 검수 범위다. 프로젝트 수정 소유는 이 review.md뿐이다.

## 최종 미디어·문서 판정

**문제없음. 남은 Critical/Warning/Suggestion 없음.**

- `/home/ajou/yigyu/3/stability_adapter_2/plot_arm_initial_trials.py:22`–`:39`의0.5초 네 ON 조건 및
  1초 reference/Y+ 두 ON 조건, saved time·m→mm·degree 변환, 독립0.5/1초 축·범례가 원자료와 일치한다.
  `:61`–`:67`은10 rows/global 계약과146개 explicit 입력 SHA를 plot 전에 확인한다.
  기존 output을 거부하며 새 native physics나 source geometry renderer를 사용하지 않는다.
- 결과 README `:35`–`:38`의 지원 CLI를 fresh /tmp/right_elbow_retention_review_reproduction_20261006에서
  실행해 exit0 및1902×1336 전체 pixel exact를 독립 확인했다. canonical PNG도 직접 읽어 축·곡선·범례를 확인했다.
  manifest의 comparison 포함147개 direct 입력,146개 embedded source/raw 입력,
  producer1개 및PNG1개 SHA는 전부 현재 파일과 일치하고 downstream media/docs/comparison 입력은 없다.
- 결과 README `:11`–`:20`의 모든10개 최대오차 행은 raw/comparison의6자리 반올림과 일치한다.
  소단계 계획·PLAN31·adapter README·VISUAL23의5static/10native, 초기 source 거부,
  Y의 단기 개선/1초 악화·fine c02 유지·X/Z1초 미측정·OFF 미실행 설명이 정합한다.
  접촉 시점과 포화를 실제 지지력·연속 접촉·인과로 단정하지 않으며 안정/연주 성공을 주장하지 않는다.
  기존 joint PI 및 초기각 승인 범위의 분석이며 새 기타 p/q feedback/gain/model/gate를 도입하지 않는다.

프로젝트 수정은 이 review.md뿐이며 다른 작업자의 변경·공용 모델·기존 결과를 수정하거나 되돌리지 않았다.
검수자의 CLI 실행은 저장 자료의 pure 비교 및 plot 재생성뿐이고 native rollout은 없었다.
