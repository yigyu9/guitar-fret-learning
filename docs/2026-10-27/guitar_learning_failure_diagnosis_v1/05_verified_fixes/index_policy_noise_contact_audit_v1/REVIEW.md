# 독립 준비 검수

요약 판정: **문제없음 / PASS**. Critical·Warning·Suggestion 지적 없음. 구현자가 아닌 별도 검수자가 원 908개 SHA를 모두 다시 계산했고, 실제 rl38 Python3.8에서 CUDA를 숨긴 CPU fixture를 재실행하여 기존 보고서와 정확히 일치함을 확인했다. 생산·봉인 소스·CPU 보고서는 변경하지 않았다.

- `experiment.py:197–222`: 원 V7 ready와 V4 엄격 load/evaluate를 유지한다. fit·warmup·PPO 갱신은 없고 원 평가의 모델/optimizer/checkpoint 불변 검사를 재사용한다.
- `experiment.py:97–128`: 원 bound act와 원 Normal.sample의 [128,4] 추출을 재사용한다. private7 첫 상태는 원 post-load seed7 경계와 비교하고, 이후 호출마다 private stream을 이어간다. deterministic은 난수를 추출하지 않는다. CPU 두 tick의 원 표본과 정확히 일치했고 private17은 달랐다. 실제 CUDA 수치 재현은 후속 실행에서 확인해야 한다.
- `experiment.py:130–164`: first mask를 원 step 전에 복제하며 원 step을 정확히 한 번 호출한다. 완료 전 128/127 행을 구분하고 원 raw ledger를 deepcopy한다. 공통 계약 v2 원인 순서와 10몸체 순서를 대조한다. source onset/end에서 원 audible duration을 저장하며 clean 요구시간을 분모로 대신하지 않는다.
- `experiment.py:165–171`: factory/상속된 step/instance act와 Python·NumPy RNG를 복구하고 Torch CPU/CUDA fork scope를 종료한다. CPU에서는 factory/act/step 예외에도 주 예외와 전후 RNG가 보존됐다. `global_RNG_scope_restored`는 hook 복구 상태를 재사용하므로 독립 CUDA 상태 비교값으로 해석하지 않는다. 정상 완료는 fork context 복귀 이후 기록된다. 원 stochastic 수행의 최종 global RNG와 같다는 주장은 없다.
- `experiment.py:183–199`: 평균/private7 두 기준 평가가 모두 성공하고 입력/출력 SHA가 유지되어야17/27을 허용한다. 별도 stdlib toy fixture로 두 기준 통과·비힘 trace 불일치 거절·입력 변경 거절을 추가 검증했다.
- `experiment.py:223–242`: 실행 실패를 숨기지 않고 partial raw ledger·수집된 actor 행·실패 보고서를 보존한다. source 변경은 완료로 처리하지 않는다.

이 PASS는 **준비 코드의 검수**다. 실제 GPU/native/체크포인트 load/실모델 생성·forward는 하지 않았다. 원128 첫 시도·384 음 분모와 실패를 유지하는 계약이며, 기준 재현 gate는 음악 수용 gate와 다르다. 기존 음악 수용 실패를 그대로 재현해도 기준 재현 검사는 통과할 수 있다. 원인 누적 시간은 겹치므로 합산 감점·정확한 substep 발생 시각·실제 줄 압력 또는 음향 증명으로 해석하면 안 된다.
