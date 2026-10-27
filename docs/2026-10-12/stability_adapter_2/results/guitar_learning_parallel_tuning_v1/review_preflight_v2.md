# 병렬 수집·성능 계측 사전 검수 v2

요약 판정: **수정 권장 사항은 있으나 현재 CPU 환경 수 벤치마크와 저장 rollout의 optimizer 비교를 막는 Critical은 없음.** 아래 내용은 실행 구조의 사전 검수이며 진행 중인 N16이나 미완료 결과의 성공 판정이 아니다.

검수 범위: `guitar_learning/train_parallel.py`, `parallel.py`, `headless_session.py`, 해당 CPU 검사, 이 결과 디렉토리의 `bench_batch_v1.py`, `profile_updates_v1.py`. 읽기 전용으로 검토했으며 새 물리·성능 시험·무거운 검사를 실행하지 않았다. 실행 중 소스와 원자료는 수정하지 않았다.

## Critical

없음. 앞서 발견한 `PreparedHeadlessSession`/`HeadlessPreparedSession` 이름 불일치는 수정됐으며 실제 factory 선택을 검사하는 CPU 회귀검사도 추가됐다.

## Warning

1. **CUDA 수집 시간의 마지막 비동기 작업** — `guitar_learning/train_parallel.py:143–145`.
   `collect()` 직후 collection 시간을 확정한 다음 CPU 저장/동기화를 수행한다. CUDA에서는 마지막 가치 계산·tensor stack이 아직 실행 중일 수 있어 이 짧은 tail이 collection_s에 포함되지 않을 수 있다. 현재 CPU 환경 수 벤치마크에는 영향이 없다. 추후 CUDA 수집 시간을 직접 비교하려면 새 버전에서 collect 전후를 동기화하고 시간을 재거나, 현재 측정의 한계를 명시해야 한다. 별도 `profile_updates_v1.py:21–24`는 optimizer 측정 전후 동기화하므로 이 문제와 구분된다.

2. **RAM 최소값은 표본 최소** — `guitar_learning/train_parallel.py:113–128`, `bench_batch_v1.py:24–25`.
   MemAvailable은 실행 시작과 각 control tick 완료 시 측정된다. 최초 scene 생성/재준비 중의 순간 최저값까지 관측한 것은 아니다. N16 판단과 최종 문서에는 ‘관측한 표본의 최소 여유 RAM’이라고 명시해야 한다. worker RSS는 각 프로세스의 lifetime peak 합이므로 동시점 실제 RSS 합과도 구분한다.

3. **batch 오류 시 나머지 후보를 자동 진행하지 않음** — `bench_batch_v1.py:21–27`.
   한 subprocess가 실패하면 즉시 종료해 나머지 후보와 최종 batch 요약 파일 작성을 건너뛴다. 개별 console/report는 남으므로 실패가 성공으로 바뀌지는 않는다. 계획의 ‘실패 보존 후 다음 독립 설정’은 이 드라이버가 자동 구현한 동작이 아니다. 실제 오류가 발생하면 보존된 로그를 근거로 다음 독립 실행을 결정하고, 이미 실행한 batch 파일을 소급 수정하지 않아야 한다.

## 확인한 정합성

- 원본 Guard를 상속하고 create_sim의 graphics device와 명시한 PhysX thread 수만 변경한다. 실행 camera mapping을 비워 원래 생성 loop가0회 돌며 dummy handle을 사용하지 않는다. constructor의 임시 class binding은 finally로 복구된다. thread 수 변경의 수치 동등성은 별도 native 비교 사항이다.
- spawn 독립 환경에 중앙 batched policy를 사용하며 `[T,N]` 기록, terminal bootstrap0, truncation의 마지막 실제 관측 bootstrap, partial reset과 비종료 환경 보존이 정합하다. 오류가 난 일부 batch만 학습에 사용하는 경로는 없다.
- worker finally audit를 회수해 부모/자식 actual import 합집합을 핀과 대조한다. 미존재 audit·worker failure·forbidden calls·Root/기타/중력/카메라 flag 오류는 최종 completed를 거부한다. 모델/원본 소스 parity와 입력 전후 SHA 검사도 유지한다.
- parent/spawn에 OMP/OPENBLAS/MKL/NUMEXPR=1을 설정하고 Torch1 및 worker runtime 정보를 기록한다. 이를 OS 전체 thread 수1이라는 주장으로 확대하지 않는다.
- CPU collection_s에는 실제 수집·중앙 정책·IPC·compact 기록과 수집 도중의 재준비가 포함된다. 최초 reset은 별도다. startup_s는 프로세스/모듈 시작, scene 생성과 준비는 reset_s에 포함된다. reset_s는 collection_s와 일부 중첩되므로 두 값을 단순 합산해 총 시간을 만들면 안 된다. max_wall_seconds는 update 사이의 soft budget이다.
- 환경 수 시험은 같은 horizon128에서 N별 총 전이 수가 달라진다. collection throughput 비교에는 적합하지만 같은 batch의 optimizer 속도 비교나 학습 효율 비교가 아니다. 상위 두 후보 반복과 이후 고정 총 batch 비교는 별도 근거로 남겨야 한다.
- optimizer profile은 같은 initial checkpoint와 같은 recorded rollout을 매 반복 다시 로드한다. CPU/CUDA 측정 시 데이터 전송·모델 생성/로드는 시간 밖이며 optimizer update만 측정한다. 첫 반복을 제외한 나머지 두 반복 중앙값이고 전후 CUDA synchronize가 있다. 실제 결과에서는 KL retry 횟수/유효 완료 여부도 함께 확인해야 하며, optimizer만 빠르다고 native end-to-end가 같은 비율로 빨라진다고 설명하면 안 된다.
- 매 에피소드 첫 전이만 raw240Hz 네 표본을 남기고 나머지는 compact60Hz 자료다. 비용/실패는 환경 내부의240Hz 검사에서 오지만 compact stability 숫자는 마지막 substep이다. 이 파일만으로 모든 물리 표본의 최대 변위나 삼중 지지 비율을 재검증했다고 주장할 수 없다.

완료된 수치, 후보 선정, headless parity, 실제 worker 종료·반환값, 최종 장기 설정의 근거는 후속 최종 검수 대상이다.
