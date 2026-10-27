# 병렬 환경 수·장기 학습 시작 설정 최종 검수

## 요약 판정

**문제없음.** 완료된 제한 실험의 집계와 시작 설정의 선정 근거가 실제 기록 및 현행 안내와 일치한다. 장기 학습 수렴이나 음악 연주 성공을 인증하는 판정은 아니다.

- Critical: 없음.
- Warning: 미해결 사항 없음. 아래 검증 범위의 제한은 결과 문서에 명시되어 있다.
- Suggestion: 없음.

검수 중 `guitar_learning/TRAINING.md:92`의 과거 “병렬 시뮬레이션 수집은 미구현” 문구를 발견해 담당자에게 전달했다. 현재는 train.py의 단일 환경 수집과 parallel.py/train_parallel.py의 병렬 구현을 구분하도록 수정되어 있으며 이를 재확인했다. 검수자는 소스·원자료·기존 문서를 수정하지 않았다.

## 독립 대조한 내용

10개 report와 각각의 압축 transition 로그를 읽어 전이 수·종료 수·실패 수·음악 매칭·유지 시간 합계·기타 편차 최댓값·완료 에피소드 평균 비용을 다시 집계했다. 총 **31,616전이, 완료 295에피소드, 실패 0**으로 run_summary.json과 일치한다. 각 report의 completed는 true이며 입력 변경·import pin 누락·원 소스 parity 오류·worker 감사 누락·guard 위반·worker 실패·물리 flag 오류 목록은 모두 비어 있다. worker 감사 수도 환경 수와 일치한다.

세 pilot은 각각 8,192전이와 완료 80에피소드다. 전체 compact 기록의 50/100ms 매칭 최댓값은 모두 0이다. 압현 후보 유지 시간 합계는 baseline 0초, explore 0.0291666667초, faster 0.05초다. 이는 에피소드 간 합이며 단일 연속 유지 성공을 뜻하지 않는다. 마지막 물리 substep에서 저장한 60Hz 기타 이동 최댓값은 각각 **2.22077 / 46.41372 / 46.95239mm**로 문서와 일치한다. 나머지 240Hz 표본 전체의 최대 편차로 확대하지 않았다.

CPU 환경 수의 N8/N16 반복 평균과 90% 선정 규칙, optimizer만 비교한 CPU 8.2013초/GPU 0.2075초, CUDA collection 종료 동기화 개정, 세 후보의 공통 N16/H128/batch2048/seed7/medium 조건을 확인했다. GPU 약 40배 수치를 물리·전체 학습 가속으로 사용하지 않는다. H128 유지에 따른 batch2048 선택은 첫 B 목표 시간창을 포함하려는 의도로 기록되어 있다.

pilot_checkpoint_analysis.json은 저장된 학습 상태에서 정책 출력과 log_std가 변경되었음을 확인하는 자료로 설명되어 있다. 별도 native 평가에서 음악 수행이 개선되었다는 주장으로 사용하지 않는다. distal 몸체 원점과 명목 프렛 목표 사이의 거리도 실제 접촉 간격으로 설명하지 않는다.

장기 JSON은 N16/H128/CUDA/medium, 초기 std=exp(-3), actor lr=3e-5, value lr=3e-4, 추가 업데이트 상한 256, 체크포인트 간격 10, soft wall budget 28,800초다. 최대 전이는 16×128×256=524,288이다. baseline pilot의 전체 wall time을 비례 확장한 약 8.09시간과, 초기 준비를 포함하고 업데이트 경계에서 검사하는 soft budget의 초과/조기 종료 가능성을 문서가 구분한다. long_config_validation.json의 설정 검사·선택 checkpoint strict load·실제 parameter 수 1,931,600 기록을 확인했다. **장기 실행은 수행하지 않았다.**

현행 README/TRAINING/PARALLEL_TRAINING과 archive index의 실행 진입점·이전 버전 보존·기존 검증 결과 구분을 대조했다. CPU 104개 통과는 cpu_tests_v2.txt의 기존 로그를 확인했으며 재실행하지 않았다.

## 감사 범위와 한계

input_audit.json의 passed=true, 오류 목록 없음, 실제 로드 XML/선언 mesh 106파일, 입력 경로 1,580개, 준비 reset 398회, reset 정적 물성 동일, 보관 48파일 및 보존 대조 151파일 일치 기록을 확인했다. 이 전수 SHA·정적 물성 감사는 담당자의 감사 산출물을 검토한 것이며, 이번 독립 리뷰에서 같은 대량 검사를 반복하지 않았다. 전체 raw 저장은 398 control tick/1,592 물리 표본이고 나머지는 compact 기록이다.

기존 사전 검수는 review_preflight_v2.md와 review_preflight_v3.md에 보존되어 있다. 이번에는 새 native 실행·렌더·물리 실험·학습·무거운 검사를 추가하지 않았다. 최종 봉인용 final_verification/source_final/artifact_inventory는 담당자가 후속 작성하는 별도 산출물이며, 이 리뷰는 아직 만들어지지 않은 산출물의 완료를 전제하지 않는다.

## 검수 시점 SHA256

| 파일 | SHA256 |
| --- | --- |
| run_summary.json | `93c5e5d841caae3afe98d5591007f8181394603d56d6d9771d45061fbe051588` |
| pilot_checkpoint_analysis.json | `5507e463333b6457eae4faea00be8cd9ec56783e5adfc7272fb3c9776912fcd9` |
| long_training_decision.json | `0ce0b553fc1ef70f301fc999e002f2bdc72bf06e5a561869e626292dec696664` |
| long_config_validation.json | `a93a2fe05706c69b5fe698f83d2d74b5b4a1d2dc587a57ac20bdd0ec636f9fce` |
| input_audit.json | `27a685a9a947d5cfa74ae5f8ba63e07ced2d68311d8851b9c501511b5d3c3382` |
| guitar_learning/train_parallel.py | `510c2f4dc6d43590837f04bf5cf950f94983da41d19e19f2d1d0167aca870254` |
| guitar_learning/configs/long_B_16env_v1.json | `39576b97276c0d4891eeb635e65d92919b28c4bcec9d8726ab7417a168721d95` |
