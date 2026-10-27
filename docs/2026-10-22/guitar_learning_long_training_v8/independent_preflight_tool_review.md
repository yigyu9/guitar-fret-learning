# v8 장기 실행 보조 도구 사전 독립 검수

**요약 판정: 문제없음 — 보완한 현행 도구 구성에 대한 사전 판정이다. 실제 장기 학습 결과 검수 완료를 뜻하지 않는다.**

- **Critical:** 현재 운영에 남은 지적 없음.
- **Warning:** 현재 보완된 도구에 대한 추가 지적 없음.
- **Suggestion:** 없음.

현재438개 학습 소스는 수정하지 않았다. 새 phase의 감시·후처리·검산·분석·평가·재생 도구와 테스트를 읽기 검수하고 허용된 CPU fixture만 실행했다. 실제 `/proc` 조회, 프로세스 신호, native/GPU/GL, 장기 학습의 main은 실행하지 않았다. 작성한 파일은 이 검수 MD/JSON뿐이다.

## 검수 결과와 보완 확인

- 원래 `monitor_training.py:25`의 status EIO, `:41`의 NVIDIA timeout, `:49`의 로그 쓰기 오류가 감시를 종료시키는 경로와 `:47`의 PID 미검증을 지적했다. 원문은 보존하고 `monitor_training_v2.py`로 교체하는 구성을 검수했다. v2는 GDB 전체 인수·시작 시각·직계 자식을 통해 최초 native를 찾고, 캐시한 native PID/시작 시각/전체 인수/출력 경로를 신호 직전에 재확인한다. 상태·소스·외장 저장 오류는 검증된 대상에 SIGINT를 한 번 시도하며 NVIDIA 조회 실패는 경고로 분리한다.
- v2는 외장 progress 기록을 우선하고 로컬 ENOSPC는 외장에 기록하며 감시를 계속한다. 외장 기록 실패도 guard에 연결한다. `/proc` 읽기 EIO를 native 종료로 오인하지 않으며 launcher marker가 없어도 native 부재와 닫힌 report를 대조한다. `monitor_replacement.json`은 root가 원래 감시기만 종료하고 교체한 운영 기록이다. 검수자가 실제 PID를 조회하거나 교체를 수행한 것은 아니다.
- `run_training.py:34`의 외장 로그 fsync 오류로 launcher 종료 marker가 누락될 수 있다는 경로는 원문에 남는다. 현재 후처리는 launcher의 정확한 인수/시작 시각·24시간 한도·동일 launch marker·완료 report를 검사하고 이 경우 실패를 기록하며 새 GPU 단계를 시작하지 않는다. 원래 launcher가 수정됐다고 주장하지 않는다.
- `after_training.py`는 launcher 종료 직전의 부분 JSON을 다시 읽고, launcher가 사라졌을 때도 마지막으로 완성 marker를 재확인한 뒤 실패를 판단한다. 외장 실패 기록이 다시 실패하면 로컬 emergency 파일을 남긴다. 순서는 전체 검산→별도 strict resume1→재개 검산→학습 로그 분석→고정5모델 평가→대표 모델 전신/손 재생이다. 하위 프로세스 종료를 기다린 뒤 다음 단계를 시작하며, 결과와 큰 로그/영상은 외장 새 경로에 저장한다.
- 초기 `verify_training.py`가 요구한 `source_training/`가 없음을 지적했다. root가 동결438사본을 생성했고 검수자가 모든 사본 SHA를 manifest와 직접 대조해 통과했다.
- 초기 advantage 검사가 이상적인 평균0/표준편차1에 지나치게 엄격함을 실제 float32 `policy_advantages` fixture로 재현했다. `100+linspace(0,.01)`에서도 정규화 평균 약−.00169가 발생한다. 보완본은 원신호 크기·float32 eps에 따른 반올림 한도를 적용하고 std 범위·잘못된 mode/count/mix 검사를 유지하며 사용한 한도를 결과에 기록한다. 이는 요약 통계 검증이며 개별 GAE 재계산이나 보편적인 GPU reduction 오차 증명이 아니다.
- middle 분기의20열 전체를 index의20열로 바꿔도 통과하던 검사도 재현했다. 보완본은 각 손가락의 canonical q_offset/q_velocity/target_error·자기 posture·valid/idle20열과 인덱스를 정확히 대조한다. 전체 cross-finger 오배선 회귀가 거부된다.
- 최종 검산 도구는 v8/544/8토큰·finger actor·separate/.98·3331 상태를 검사한다. fresh 예산과 별도1회 재개를 구분하고 parent→initial 전체 nonmetadata 상태를 비교한다. 원자료 CRC/EOF·순서·에피소드/지표·reward 합·journal·실제 close 검사는 유지한다. prefix는 최종 EOF/close로 확대하지 않는다.
- `analysis.py`의 추가 std 비율·accepted KL·critic 지표는 학습 수집 통계다. 비율을 gradient 기여도로 표현하지 않고, update 평균과 풀링 통계·고정 정책 평가·실제 자연스러움을 구분한다.
- 평가 도구는 봉인 v8/source438과 현재 입력 SHA를 확인하며 초기/500/1000/1500/2000 각각1024 첫 곡을 비교한다. 저장된3331/progress를 복원하고 학습/승급하지 않는다. 초기 포함0..7의 실제 t0·reset 전 자세 캡처, 마지막 reset 생략, CUDA synchronize/finally close 및 cached 필수 pin 검사를 유지한다. 재생 도구는 v8 fresh chain만 받아 새 물리 없이 원래 몸체 자세를60fps로 표시한다.

## 직접 검증

최종 도구의 독립 CPU 검사는 **42개 모두 통과**했다: 평가11, 분석20, 감시11. 각각 별도 프로세스로 실행했으며 감시 검사는 가짜 proc tree·mock NVIDIA/kill만 사용했다. 분석 검사는 float32 경계·완전 cross-finger 치환·복원/CRC·순수 CPU 그림 생성을 포함한다. 최종 Python11파일의 AST를 읽어 확인했다.

원래 도구의 source snapshot 누락·float32 거짓 실패·배선 검사 누락과 감시 장애를 발견한 뒤 보완본을 다시 검수했다. after_training 최종 marker 재읽기 패치는 정적/AST 검수이며 실제 자동 후처리를 실행한 검증은 아니다. 파일별 검수 SHA는 동반 JSON에 고정한다.

## 적용 한계

이 시점에는 장기 학습이 진행 중이다. 실제2000회 완료, 전체65,536,000전이 무결성, 2000→2001 재개, 고정5모델 평가, 영상 품질·자연스러움·연주 성과는 아직 판정하지 않았다. 도구가 준비됐다는 판정과 실제 결과의 검수를 구분해야 한다. 기술적 오류 시 원자료를 남기고 실패를 기록하는 구성이며 저장 장치의 영구적 건강이나 모든 시스템 오류에서의 자동 복구를 보장하지 않는다.

이 검수 기록2파일 작성 뒤 쓰기를 종료한다. 이후 도구 변경이나 실제 장기 결과에는 별도 검수가 필요하다.
