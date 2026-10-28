# 왼손 학습 실패 진단 v1

## 최신 진행 상태: 손목 제어 교정과 낮은 힘 상한의 압현 재현

**현재는 고정 기타에서 압현 가능성과 손가락 제어의 기여를 분리하는 중이다. 기본 J33 학습의 전체 실패 원인을 확정하거나 자유 기타·전곡 개선을 완료한 상태는 아니다.** 저장공간 정리는 중지했으며 이 진단과 원래 기준 학습 결과 전체를 정리 대상에서 제외했다.

- 진단 손목의 위치 미분 좌표와 누적 요청을 교정한 v3를 CPU·실제 GPU·독립 검수했다. 검지 reference의 손목 오차는 중앙값0.205mm/0.041도로 줄었지만, 같은 원래 손가락 명령의 달성은0/4였다. 기본 J33 raw policy는 이 진단용 Jacobian 보정 경로를 직접 사용하지 않는다. [손목 v3 결과](05_verified_fixes/wrist_position_candidate_v3/analysis/results_v1/RESULTS.md) · [원 source 자세 정합 감사](05_verified_fixes/source_finger_pose_consistency/RESULTS.md)
- 동일 원음에서 손가락4축의 유한 목표각을 비교했다. 원20Nm에서 검지21/135·중지4/180 후보가 통과했으나 선정 자세의 새4시도는 검지3/4·중지4/4였다. 검지의 큰 첫마디 합력이 남았고, 특정 충돌 한 쌍 제거는 힘을 다른 마디로 옮겨 기본 채택하지 않았다. [원 grid](05_verified_fixes/finger_only_oracle_acquisition_v1/analysis/results_v1/RESULTS.md) · [한 쌍 분리 결과](05_verified_fixes/index_proximal_pair_isolation_v1/analysis/results_v1/RESULTS.md)
- 손가락16축의 native effort 상한만20→0.25Nm로 낮춘 별도 진단에서, 기존 선정각115의 검지는0/4·오압현100%로 후퇴하고 손목 오차도 커졌다. 중지114는4/4를 유지했다. 전체105속성·90충돌쌍·원 판정/음시간/범위를 보존·검증했다. 0.25Nm는 진단용 공학값이며 인체 적정값이나 실제 압력 상한이 아니다. [같은 선정각 비교](05_verified_fixes/finger_effort_limit_v1/analysis/results_v1/RESULTS.md)
- 같은315목표각을 낮은 상한에서 다시 비교하면 검지38/135·중지5/180이 통과했다. 원 순위로 검지112·중지114가 선정됐지만 전체 평균 오압현률도 증가해 전반적인 개선이나 기본 채택으로 보지 않는다. [전체 비교·검수](05_verified_fixes/finger_effort_limit_v1/oracle_grid_v1/analysis/results_v1/RESULTS.md)
- **새 검지112는 새4환경에서4/4·압현 유지100%·오압현0·물리/손목 실패0**이었다. 실제 종료0/30.489초와 입력 불변·장면 종료·별칭 복원을 확인했다. 하중·자세와 독립 검수 상태는 [실제 분석](05_verified_fixes/finger_effort_limit_v1/oracle_grid_v1/reproduction_v2/analysis/results_v1/RESULTS.md) 및 status.json에 기록한다. 중지114는 이미 검수된 동일 조건4/4를 재사용한다. 같은 seed의4환경이며4seed 재현이나 학습 성능이 아니다. [검지 재현 실행](05_verified_fixes/finger_effort_limit_v1/oracle_grid_v1/reproduction_v2/runs/index/evaluation.json)

기존115/114의 두 힘 상한을 실제 GPU에서 촬영한 손·전신8영상은 원 기록·화면 방향·전신 구도·인코더·독립 검수 PASS다. env0 첫 시도 영상이며 새112 성과 영상과 구분한다. [비교 영상·검증](05_verified_fixes/finger_effort_limit_v1/native_videos_v1/analysis/results_v1/README.md)

다음은 [학습 전 대조 계획](05_verified_fixes/low_effort_finger_prelearning_v1/PLAN.md)의10개 새 장면·40시도다. 검지·중지의 무명령/무작위 명령, 약지·소지의 기준/무명령/무작위 명령을 대조한다. 팔 이동만으로 성공하는 경우를 손가락 학습으로 세지 않는다. 검수된 기준 압현은 반복하지 않고 재사용한다. 이후 짧은 학습·해제/다음음·자유 기타·원곡67음 평가를 이어간다. 현재 보상·성공 기준을 낮추거나 큰 새 학습을 시작하지 않았다.

진행표는 [status.json](status.json)과 [전체 계획](../../plans/guitar_learning_failure_diagnosis_20261027.md)을 따른다. 아래는 **각 실행 당시의 기록**이며, 과거의 실행 중/미구현 표현을 현재 상태로 해석하지 않는다. 갱신 전 문서 원문은 [보존본](baseline/document_snapshots/20261027_before_latest_control_summary/README.md)에 있다.

## 이전 단계의 기록


상태: 엄지 후면 기하 교정·CPU101검사·고정GPU회귀를 완료했다. 비용 예측 head 초기값 비교 B는150~250회128/128달성했지만 마지막300회65/128로 후퇴했다. 목표 누적 억제 재생 실험은128/128달성을 유지하며 중지 음 구간 합력 중앙값89.61→30.23N으로 낮췄다. 기존 오차까지 푼 조건은0/128이었다. 진단 결과이며 기본 제어 채택·자유 기타·전곡 개선은 아직 미확인이다.

- 계획: `../../plans/guitar_learning_failure_diagnosis_20261027.md`
- 기준 실행: `../guitar_learning_large_until0900_v1`
- `baseline/source_preservation.json`: 558원문 보존, 655입력 SHA 확인
- `baseline/cpu_before.log`: 관련60개 CPU 검사 통과
- `baseline/`: 기존 모델의 읽기전용 상세 추적
- `01_control/`: 이름별21관절/양방향/누적·위치 제어 비교
- `02_contact_reward/`: 도달 가능성과 현행 압현 판정 확인
- `03_short_learning/`: 앞 단계 통과 뒤 제한 과제 학습
- `04_ablation/`: 근거가 있는 보상·학습 설정의 독립 비교

기존 학습·checkpoint·로그는 보존한다. 진단용 고정 기타·스크립트 제어 결과를 학습한 자유 기타 정책 성과로 보고하지 않는다.

## 현재 확인된 사실

1. **기본 관절 제어의 전달 오류는 발견되지 않았다.** 같은 유한 목표각 궤적에 두 제어 모드가 따라가며, 고정 기타에서는 모든 관절·방향 사례에서 B 자세 도달 기준을 통과했다. 작은 지속 출력은 누적 방식에서 큰 목표각 편향을 만들었다. 이는 정의된 동작이며 codec 계산 오류는 아니다. [고정/자유 비교](01_control/FREE_FIXED_COMPARISON.md)
2. **최종 정책은 한계각을 향해 계속 명령했다.** 기존 최종 모델 상세 추적에서 손가락 목표의 한계 체류와 바깥 방향 출력이 겹쳤다. B 보상 gate는 열려 있어도 실제 B 복귀는 이루어지지 않았다. [모델 상세 추적](baseline/README.md)
3. **정적 접촉과 실제 음악 시점 수행은 다르다.** 원곡에서 미리 정한24목표를 검사했고, 실제 패드 위치와 손목 오차를 함께 보정한 유한 제어에서 각 손가락의 정적 연속 후보를 확보했다. 실제 악보 시계에서는6/24달성, 중지는0/6이었다. 최초접촉·유지·달성·오압현·부족 및 PBRS 정산 검산은 통과했다. 보상·판정 문턱은 바꾸지 않았다. 일부 경로의 높은 접촉력은 미해결이며 진단 제어 성과를 정책 학습 성과로 확대하지 않는다. [접촉·보상 검사](02_contact_reward/README.md)
4. **엄지 안내 품질과 실제 접촉은 다르다.** 제한 범위 후면 접근 두 검사에서 기하 품질은1이었지만 실제 엄지 순접촉힘과 후보는0이었다. 전체 가동범위 도달 불가능이나 cooked mesh 오류를 입증한 것은 아니다. [엄지 검사](01_control/thumb/RESULTS.md)

단계3은 팔을 유한 제어로 배치하고 선택 손가락4축만 정책이 제어하는 진단 조건이다. 처음 사용한 두 중지 목표는 reference에서도0/4달성이었다. source 접촉 순간의 실제 손목과 목표각 기반 손목이약5.7cm 달랐다. 실제 손목 pose를 유지하는 별도 조건은 두 제어 방식 모두 reference3/4달성·출력0/무작위0/4·실패0을 확인했다. 원래 보상/종료 조건으로 fresh300회 seed7/17 두 모드 비교를 완료했다. 기본 공동 학습 실행과 과거 자료는 유지한다. [v1 실패](03_short_learning/PRECHECK_V1.md) · [v2 사전검사](03_short_learning/PRECHECK_V2.md) · [실험 조건](03_short_learning/EXPERIMENT_SPEC.md)

incremental/seed7의 실제 고정128평가는 초기0→50회85→100회20→150~300회0달성이었다. 전체 학습·평가의 물리/손목 종료는0이고 탐색 std도 거의 같았지만, 최종 정책은 준비 중 크게 반대로 움직이며 목표 한계 체류를 만들었다. 최고 저장본도 사전 통과 기준에 미달한다. reference128대조는108달성·wrong14.13%이며 학습 정책 성과로 계산하지 않는다. [완료된 첫 비교 분석](03_short_learning/pilot_incremental_seed7_v2_retry2/analysis/INTERPRETATION.md)

position/seed7은300회 학습5,632시도와 초기·50간격 모든 고정 평가에서 달성0이었다. 최종 실제 선택 관절 움직임은 약1.5~2.95° 범위였고 한계 체류는 없었다. 같은 reference 목표각 명령도 실제 물리 반응은 분기했으며 reference76/128달성·wrong32%였다. 제어 모드의 일반적인 우열로 확대하지 않고, 긴 시간의 탐색/접촉 민감성과 학습 신호를 더 분리한다. [위치 제어 비교 분석](03_short_learning/pilot_position_seed7_v2/analysis/INTERPRETATION.md)

동시에 진행되던 문서 정리에서 현재 진단/기준 자료430항목을 제외하고 필요한 자료를 runs/failure_diagnosis_live_preservation_20261027에 추가 보존했다. 이후 호스트 재부팅으로 pilot이49회 부근에서 중단됐다. 입력674개·활성Python517개와 자세 자료의 SHA를 재검증한 뒤 동일 조건의 새 retry2를 완료했다. 중단된 원자료와 불완전한 마지막 로그 행은 수정하지 않았다.

단계4의 시간척도·탐색 기하 감사는 학습 변경과 구분한다. [할인 계수 분석](04_ablation/TIME_SCALE.md) · [팔/손가락 탐색 분석](04_ablation/exploration_conditioning/README.md) · [지정한 접촉 시간표의 보상 순서](04_ablation/reward_objective_audit/README.md) · [PPO 경로 점검](04_ablation/PPO_PATH_AUDIT.md) · [수집 시각 분포](04_ablation/temporal_sampling/README.md) · [실제 기울기 진단](04_ablation/gradient_probe/RESULTS.md) · [가치 예측 검산](04_ablation/gradient_probe/VALUE_CALIBRATION.md)

보상 산술 감사8조건에서 정상 clean 점수1.5가 짧은 반복 접촉.478/누락−.1/오압현−.250보다 높았다. 다섯 핵심 압현 항에서는 음 종료 뒤 해제 유무의 점수가 같으며, 전곡 균형 점수와 무가중 달성 음 수는 서로 다른 수행 순위를 만들 수 있다. 실제 정책·전환 과제에서 별도 확인할 사항이며 이 결과만으로 보상 계수를 바꾸지 않았다. 독립 재계산과 별도 검수를 통과했다.


## 후속 실제 검사와 다음 비교

- 실제 악보 시계의128시도에서 짧은 접촉만17개, 연속50ms 이상 해제95개, 달성53개를 관측했다. 범주는 겹친다. 전체 원장·9보상·240Hz 시계 검산과 독립 검수를 통과했다. loaded back-facing 부정 사례는 전체111,616표본에서도0개여서 미확인으로 유지한다. [접촉·해제 결과](02_contact_reward/live_release_probe/analysis_01/RESULTS.md)
- cp50/100/300에서 가중치 변경 없이 각각7개 연속H32를 실제 수집해9보상·가치 잔차·비용의 기울기를 나눴다. 비용 관측은 모두0이지만 비용 critic을 통한 정책 신호는0이 아니었다. cp100의 음 구간 비용 가치 bias는 약+.401이었다. 반대로 cp300의 reward MC MSE는 약.000272로 작았다. 큰 가치 잔차 기울기를 예측 오류로 해석하지 않으며, 비용 초기화가 퇴행 원인이라고 확정하지 않는다. [기울기](04_ablation/gradient_probe/RESULTS.md) · [실제 관측 return 대조](04_ablation/gradient_probe/VALUE_CALIBRATION.md)
- 증분 최고50회·최종300회 및 위치 최종300회의 손/전신6영상을 저장했다. 사전 지정env0 첫 시도는 모두 미달성이다. 별도128평가 성과와 구분한다. [영상과 검증](03_short_learning/native_videos_seed7/README.md)
- 원래 seed17 두 제어 비교는 완료했다. 실제 엄지 안내면 오류 수정·재검증 뒤 같은 수정 기하의 fresh 기준선과 시간척도만 변경하는 실험을 비교한다. 필요하면 원래 시간척도에서 비용 critic 마지막층만0 초기화하는 별도 실험을 한다. 각각 fresh300회와 동일 고정 평가를 사용한다. 두 변경을 한꺼번에 넣거나 기본값으로 채택하지 않았다. [다음 독립 비교 계획](04_ablation/INTERVENTION_PLAN.md)

단계2의 잘못된 방향 사례·모든 손가락의 실제 음악 수행, 단계3의2~4음/자유 기타 복구 및 최종 원곡 검증은 남아 있다. 현재 진단 결과를 학습 개선 완료로 보고하지 않는다.


## Seed17 증분 재현 결과

같은 예산의 두 번째 증분 학습은 결정론 평가 달성/128이 `0→0→77→127→0→89→128`(초기·50간격)이었다. 최종 clean100%·wrong0%·물리/손목 종료0이므로, 이 제한 과제가 항상 학습 불가능하다고 볼 수 없다. 다만150회와300회만 단일 기준을 통과했고 비연속이어서 사전의 연속2평가 기준은 미달이다. seed7 최종0과의 차이 및 저장본 간 큰 변동을 함께 본다. 확률적 훈련5,632시도의2,170달성과 탐색을 끈 고정 평가를 구분한다. 초기 reference108/128은 seed7과 정확히 같았다. [재현 분석](03_short_learning/pilot_incremental_seed17_v2/analysis/INTERPRETATION.md)

최종 실제 중지4축의 전체 에피소드60Hz 움직임 범위 중앙값은 약50.3°/24.9°/38.3°/29.7°였다. 실제 움직임은 있지만 특정 음 구간의 관절 분담이나 자연스러움의 인증은 아니다. 목표각 한계 체류도 남아 있다. 위치seed17도 모든 정책 평가 달성0으로 완료했다. GPU 작업은 계속 한 번에 하나만 실행한다.


## 수정 전 엄지 안내면의 source 기하 불일치

수정 전 loader는 OBJ의 모든 꼭짓점으로 hull을 만들어, 면이 참조하지 않는 꼭짓점까지 안내에 포함했다. face를 기준으로 재계산한 연주용 neck1 후면과 현재 안내면은 현곡67목표의 센터에서3.371~5.463mm 다르다. 이전 엄지 검사점은 neck1의 유한 삼각형에서5.146mm 뒤였다. 67개 안내센터와±40mm 범위는 모두 neck1 안에 있으므로, 현곡은 headstock 전환부를 포함한 가상 공통 경사면을 쓸 필요가 없다. 독립 source/수치/그림 검수를 통과했다. [상세 감사](04_ablation/thumb_geometry_audit/README.md)

![원본 면과 엄지 안내면](figures/thumb_source_faces.png)

이는 원본 face 기하와 안내의 불일치이며, PhysX cooked 충돌면의 직접 측정은 아니다. 실제 힘은 기타 충돌이 활성화된 thumb3에서 측정하고 있어, 충돌 없는 marker의 힘을 읽어서0이 된 경우는 아니었다. 이 근거로 활성 수정 전에 동일한 물리·범위·유한 제어의 별도 native A/B를 수행했다.

## 실제 A/B로 확인한 안내면 오류와 후속 수정

같은 자산·PD·범위·고정 기타에서 기존 안내는 접촉0/3600endpoint, face-only playing-neck1 안내는 접촉→유지→해제→재접촉을 모두 통과했다. 새 면에서 안정 유지 약2.4N, 재접근 transient peak약11.2N이었다. [actual matched 결과](04_ablation/thumb_geometry_audit/native_comparison/analysis_v1/RESULTS.md)를 보존하고, [생산 수정 계획](05_verified_fixes/thumb_rear_surface_v3/PLAN.md)에 따라 실제 면과 안내를 맞췄다. 이전517Python/README/AGENTS519파일은 새 archive에 보존했다. 수정 후 입력으로 별도 재봉인해 fresh 기준선을 완료했고 시간척도 A를 실행 중이다. 비용 초기화 B는 아직 실행하지 않았다.

성공한 seed17 최종 env0은 중지 audible 합력 p95약69.83N·엄지59.43N이며 관절 목표 추종 오차도 남았다. 엄지 목표035 고정과 유한 손목 teacher가 포함된 조건이다. [하중 감사](04_ablation/policy_contact_load_audit/RESULTS.md) · [성공한 첫 시도 손/전신 영상](03_short_learning/native_videos_seed17/README.md). 이 자료는 실제 현 압력/자연스러운 전곡 연주 인증이 아니다.


## 교정된 새 기준선과 현재 비교

같은 large128/H32/300/seed7 예산의 새 기준선은 저장시점50/100/150/200/250/300회에서2/21/37/90/74/127개를 달성했다. 최종 압현 유지99.2644%·오압현0.6940%·물리/손목 실패0이다. 최종만 기준을 통과해 연속2평가 수용 기준은 미달이다. [분석](04_ablation/time_credit_ablation/corrected_source_v3/baseline_original_gamma_seed7/analysis/INTERPRETATION.md) · [성과 그래프](04_ablation/time_credit_ablation/corrected_source_v3/baseline_original_gamma_seed7/analysis/performance.png) · [최종 손/전신 영상](04_ablation/time_credit_ablation/corrected_source_v3/native_video_baseline_final300/README.md)

네 조건(초기zero/reference·50회정책·최종정책) 전체128 첫시도의240Hz 힘·목표각·point Jacobian 관찰을 완료했다. [하중 관찰](05_verified_fixes/contact_load_probe/README.md)의 별도 분석에서 힘과 명령을 함께 확인한다. 몸체 합력을 현 압력으로 해석하지 않는다. 시간 할인만 바꾼 A가 실행 중이며, 다른 손가락·음 전환·자유 기타·전곡 검증은 이후 단계로 남아 있다.


전체128환경 하중 관찰의 독립 검산을 완료했다. 최종 모델의 음 구간 중지 접촉 합력 중앙값은89.61N(목표각 대조6.02N), 엄지84.11N이며 음 종료 뒤 중지도95.35N이다. 선택4관절 target−actual 오차 norm 중앙값은44.34도였다. 동일 성공 예산은 두 힘 수준 모두에 지급됐다. 현재 제어는 접촉으로 실제각이 막혀도 목표를 계속 누적할 수 있으므로, 추가 안쪽 명령 억제와 기존 목표오차의 유한 완화를 분리하는 진단을 준비한다. 힘의 단독 원인이나 실제 현 압력으로 확정하지 않는다. [240Hz 전체128 결과·검수](05_verified_fixes/contact_load_probe/analysis/results_v1/RESULTS.md) · [비교 그림](05_verified_fixes/contact_load_probe/analysis/results_v1/summary.png)


시간 할인 A의300회와10평가도 종료코드0으로 완료했다. 달성은50/100/150/200/250/300회에서0/80/126/0/0/0이며 후반 세 평가의 오압현은100%였다. 두 조건 모두 연속2평가 기준에 미달해 A를 기본 채택하지 않는다. 실제 초기 가중치73개·초기4대조 성과는 같았고717개 입력과 수치를 독립 검수했다. [동일 기하 비교표·그림](04_ablation/time_credit_ablation/corrected_source_v3/comparison_gamma_seed7/RESULTS.md)

후속 B는 원래gamma .99와 실패 비용을 사용하고 비용 예측 마지막층의 fresh 초기값만0으로 둔다. 실제 초기 저장본에서 그2텐서만 변경되고 나머지71개는 같음을 확인했다. 동시에 [목표각 누적 진단 계획](05_verified_fixes/contact_target_windup/PLAN.md)에 따라 같은 명령 tape·처음2초 무개입·최종4rad/s 제한의 세 조건을 CPU에서 구현 중이다. 일반 제어는 아직 변경하지 않았다.

## 비용 초기화 비교와 접촉 목표 누적 실험 완료

- [기준·A·B 비교](04_ablation/time_credit_ablation/corrected_source_v3/comparison_cost_head_seed7/RESULTS.md)는 독립검수를 통과했다. B의 비용 신호는 전체300회0이고 기존 연속2평가 기준을 통과했으나 최종 후퇴는 남았다. 원래 계획의seed17 재현 학습을 시작했다. 실패 비용과 보상 계수는 유지한다.
- [동일 명령의 세 제어 조건](05_verified_fixes/contact_target_windup/analysis/results_v1/RESULTS.md)은 실제GPU 종료코드0·원본 전체재현·첫2초동일성을 확인했다. 추가 안쪽 목표 누적 억제는 하중을 줄이며 압현을 유지했고, 기존 목표 오차 완화는 압현을 잃었다. 팔 안내의 후속 반응도 달라졌으므로 손가락 단독 효과라고 해석하지 않는다. 실제 결과 독립검수도 통과했다.
- [B 최고250회 손·전신 영상](04_ablation/time_credit_ablation/corrected_source_v3/native_video_B_best250/README.md)은 사전 지정env0 첫시도다. 촬영 시도도달성했지만60Hz8표본의 중지 합력 중앙값53.17N으로 높은 하중이 남아 있다. 자유 기타·전곡·자연스러운 손 모양의 해결을 뜻하지 않는다.

최초 접촉 후속 확인에서 전128환경의 첫 부하는1.721~1.758초였고, 기존 개입시점2초에 이미 중지합력 중앙값31.98N이었다. [근거](05_verified_fixes/contact_target_windup/analysis/PRELOAD_FOLLOWUP.md)는 독립검수를 통과했다. 같은 누적억제를 최초 유효접촉부터 적용하는 단일 시점 비교를 새 진단으로 준비하며, 생산 제어는 유지한다.
