# 왼손 학습 실패 진단 v1

상태: 단계0~1 완료. 단계2 실제 보상 정산과 정적 부정 사례 감사는 통과했지만 일부 physical negative는 미확인이다. 단계3 중지/incremental 및 position/seed7의300회와 고정 평가를 완료했다. incremental은 후반 퇴행했고 position도 학습 기준을 통과하지 못했다. 기존 저장본의 고정 기울기 진단을 진행 중이다. 자유 기타 전곡의 성능 개선은 아직 확인하지 않았다.

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

단계3은 팔을 유한 제어로 배치하고 선택 손가락4축만 정책이 제어하는 진단 조건이다. 처음 사용한 두 중지 목표는 reference에서도0/4달성이었다. source 접촉 순간의 실제 손목과 목표각 기반 손목이약5.7cm 달랐다. 실제 손목 pose를 유지하는 별도 조건은 두 제어 방식 모두 reference3/4달성·출력0/무작위0/4·실패0을 확인했다. 원래 보상/종료 조건으로 fresh300회 비교를 진행한다. 기본 공동 학습 실행과 과거 자료는 유지한다. [v1 실패](03_short_learning/PRECHECK_V1.md) · [v2 사전검사](03_short_learning/PRECHECK_V2.md) · [실험 조건](03_short_learning/EXPERIMENT_SPEC.md)

incremental/seed7의 실제 고정128평가는 초기0→50회85→100회20→150~300회0달성이었다. 전체 학습·평가의 물리/손목 종료는0이고 탐색 std도 거의 같았지만, 최종 정책은 준비 중 크게 반대로 움직이며 목표 한계 체류를 만들었다. 최고 저장본도 사전 통과 기준에 미달한다. reference128대조는108달성·wrong14.13%이며 학습 정책 성과로 계산하지 않는다. [완료된 첫 비교 분석](03_short_learning/pilot_incremental_seed7_v2_retry2/analysis/INTERPRETATION.md)

position/seed7은300회 학습5,632시도와 초기·50간격 모든 고정 평가에서 달성0이었다. 최종 실제 선택 관절 움직임은 약1.5~2.95° 범위였고 한계 체류는 없었다. 같은 reference 목표각 명령도 실제 물리 반응은 분기했으며 reference76/128달성·wrong32%였다. 제어 모드의 일반적인 우열로 확대하지 않고, 긴 시간의 탐색/접촉 민감성과 학습 신호를 더 분리한다. [위치 제어 비교 분석](03_short_learning/pilot_position_seed7_v2/analysis/INTERPRETATION.md)

동시에 진행되던 문서 정리에서 현재 진단/기준 자료430항목을 제외하고 필요한 자료를 runs/failure_diagnosis_live_preservation_20261027에 추가 보존했다. 이후 호스트 재부팅으로 pilot이49회 부근에서 중단됐다. 입력674개·활성Python517개와 자세 자료의 SHA를 재검증한 뒤 동일 조건의 새 retry2에서 진행한다. 중단된 원자료와 불완전한 마지막 로그 행은 수정하지 않았다.

단계4의 시간척도·탐색 기하 감사는 학습 변경과 구분한다. [할인 계수 분석](04_ablation/TIME_SCALE.md) · [팔/손가락 탐색 분석](04_ablation/exploration_conditioning/README.md) · [지정한 접촉 시간표의 보상 순서](04_ablation/reward_objective_audit/README.md) · [PPO 경로 점검](04_ablation/PPO_PATH_AUDIT.md) · [수집 시각 분포](04_ablation/temporal_sampling/README.md) · [기울기 진단 준비](04_ablation/gradient_probe/README.md)

보상 산술 감사8조건에서 정상 clean 점수1.5가 짧은 반복 접촉.478/누락−.1/오압현−.250보다 높았다. 다섯 핵심 압현 항에서는 음 종료 뒤 해제 유무의 점수가 같으며, 전곡 균형 점수와 무가중 달성 음 수는 서로 다른 수행 순위를 만들 수 있다. 실제 정책·전환 과제에서 별도 확인할 사항이며 이 결과만으로 보상 계수를 바꾸지 않았다. 독립 재계산과 별도 검수를 통과했다.
