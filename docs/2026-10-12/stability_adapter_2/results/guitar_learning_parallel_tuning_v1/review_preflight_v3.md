# CUDA 계측 수정·후보 실행 사전 검수 v3

요약 판정: **최소 수정은 정합하며 현재 제한 pilot을 막는 Critical은 없음. 감사 실패 처리에는 Warning이 있다.** 아직 실행하지 않았거나 진행 중인 후보를 최종 성과로 평가하지 않는다.

읽기 전용으로 보관 runner와 현재 runner의 실제 diff/SHA, `runner_timing_revision.json`, 환경 수 결과의 완료 여부/처리량, `pilot_decision.json`, `pilot_batch_v1.py`를 확인했다. 새 물리·성능 시험·무거운 검사와 실행 중 파일 수정은 하지 않았다.

## 최소 수정 확인

- 보관 `train_parallel.py` SHA는 `4c2fd19855125bfcf89919d74de4c5eaef5cb10be5fc0ae1c395ac7cdbb17727`, 현재 SHA는 `510c2f4dc6d43590837f04bf5cf950f94983da41d19e19f2d1d0167aca870254`이며 revision 기록과 일치한다.
- 실제 diff는 `collect()` 뒤 CUDA synchronize를 수행한 다음 collection 경과 시간을 확정하도록 기존 한 줄을 나눈 것뿐이다. 물리/제어/관측/보상/정책/PPO 수학은 바뀌지 않았다. CPU 경로의 동작도 그대로다. 기존 CPU benchmark가 이전 버전을 소비했다는 기록을 유지한다.
- optimizer profile 최초 절대경로 import 실패를 성공 결과로 대체하지 않고, `PYTHONPATH` 명시 재시도와 구분했다. GPU warm optimizer 시간은 전송/환경을 제외한 동일 rollout의 optimizer 비교이며 native 전체 처리량의 같은 비율 향상을 뜻하지 않는다.

## 후보 선정·예산

- 완료된 상위 두 환경 수의 원시험+반복 평균은 N8 약17.8478, N16 약21.9706 transitions/s다. 최고 평균의90%는 약19.7735이므로 구현한 규칙은 N16을 선택한다. 이는 시험한 후보 내의 처리량 기준이며 모든 환경 수나 학습 효율의 전역 최적값이 아니다.
- warm optimizer 중앙값 CPU8.2013초/CUDA0.2075초는 정의한20% 기준을 만족한다. 실제 batched CUDA 수집·업데이트/메모리와 음악/안전 결과는 이후 pilot에서 확인해야 한다.
- 세 후보는 같은 N/망/seed7/목표/보상/물리/기본 행동 범위를 쓰고 `(initial_std, actor_lr)`만 `(exp(-3),3e-5)`, `(.12,3e-5)`, `(.12,1e-4)`로 바꾼다. 모두 fresh run이며 순차 실행한다.
- runner가 bench의 horizon128을 상속함을 확인해 처음 계획의 ‘약1024’와 차이를 root에 전달했다. root는 첫 B목표 시점1.12초가 horizon64의1.0667초보다 뒤임을 근거로 horizon128을 의도적으로 유지하고 계획에 예산을 명시하기로 확정했다. 실제 **N16×H128=2048/업데이트, 후보별4회=8192전이, 세 후보 총24576전이**다. PPO가 목표 전에 rollout을 나누면 원리적으로 학습 불가능하다는 뜻은 아니며 이번 수집 구간 선택이다.

## Warning

**감사 실패 일부가 batch 중단 조건에서 빠짐** — `pilot_batch_v1.py:32–36`.

nonzero exit에서 guard/변경 입력/worker failure/physical flag 오류는 중단하지만 `missing_import_pins`, `original_source_parity_errors`, `missing_worker_audits`는 검사하지 않는다. 따라서 이런 감사 오류로 실패한 run 뒤에도 다음 후보가 시작될 수 있다. 개별 report와 exit code는 보존돼 실패가 성공으로 둔갑하지는 않는다. 진행 중 소스를 고치라는 요청은 아니며, 해당 오류 발생 시 운영자가 중단하고 실패 후보를 선정에서 제외해야 한다. 이후 새 버전에서는 감사 실패 전체를 batch 중단 조건으로 묶는 편이 명확하다.

최종 후보 선택은 세 pilot의 실제 완료·감사·KL/반환값/비용·음악/안전 결과를 보고 별도로 검수해야 한다. 현재 기록은 사전 구현/선정 규칙 검토이며 장기 수렴이나 연주 성공을 승인하지 않는다.
