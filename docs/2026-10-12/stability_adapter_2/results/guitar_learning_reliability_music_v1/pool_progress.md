# 병렬 수집 대기·종료·진행 기록 개선

수정 범위는 `guitar_learning/parallel.py`와 `guitar_learning/tests/test_parallel.py`다. 기존 파일은 root가 `guitar_learning/archive/20261018_before_reliability_music`에 보존했다. Native 실행·자산·물리 제어 변경은 수행하지 않았다.

- 모든 pending 연결과 process sentinel을 함께 기다린다. 응답은 준비된 순서대로 받고 호출자가 요청한 worker 순서로 재구성한다. 느린 worker 앞에서 기다리느라 다른 worker의 비정상 종료를 놓치지 않는다.
- 대기 중 최대 0.5초 간격으로 `wait_callback`에 operation, pending worker, 경과 시간, 전체 worker PID·생존·exitcode를 전달한다. 메모리 감시 오류도 기존과 같이 pool/collector를 무효화하고 미완성 buffer를 반환하지 않는다.
- 비정상 종료·연결 단절·전송 실패에 worker ID/PID/exitcode를 포함한다. Timeout에는 operation과 pending 목록·process 상태를 보존한다.
- 종료는 전체 worker에 close를 보낸 뒤 공유 2초 유예를 적용한다. 살아남은 worker에 terminate, 다시 공유 2초 뒤 kill한다. 기존 worker당 순차 2초 지연을 제거했다. 정상 final audit는 기존 순서를 유지하며 강제 종료는 `pool.close_diagnostics`의 종료 전후 상태·terminate/kill 여부에 남는다. 생성자 실패도 exception의 `pool_close_diagnostics`로 접근할 수 있다.
- `Collector.collect(horizon, progress_callback=...)`는 완료 tick·전이 수·경과 시간·완료 episode 수를 전달한다. Bootstrap과 부분 reset 계산은 유지했다.
- Native factory는 `task_sampling.build_environment`로 연결한다. numpy/torch/random 시드는 기존 `base_seed + worker_id`; sampler에는 base seed와 worker_id를 각각 제공한다. Music 옵션이 없는 legacy 고정 목표도 같은 factory를 거친다. Reset의 `episode_task`는 별도 감사 JSON, step의 `episode_task`/`pick_guide`는 제공될 때 compact 로그에 포함한다.

검증: `PYTHONDONTWRITEBYTECODE=1 /home/ajou/miniconda3/envs/rl38/bin/python -m unittest guitar_learning.tests.test_parallel -v` — 최종 **10개 통과, 15.076초**. 강제 `os._exit(13)` 즉시 검출, 느린 worker와 응답 순서, wait callback 중단, tick 진행 callback/중단, 강제 timeout cleanup, 부분 reset, terminal/truncated bootstrap, N2 PPO update, worker startup/step 실패와 감사, factory 선택을 확인했다.

CPU fake-worker 검증이며 native 장면의 실제 메모리 부족 재현이나 장기 음악 수행 개선을 입증하지 않는다. Native 검증과 최종 봉인은 root가 담당한다.
