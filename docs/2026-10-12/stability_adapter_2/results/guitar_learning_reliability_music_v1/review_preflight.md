# 실패 복구·메모리 감시·음악 탐색 개선 사전 검수

## 요약 판정

**문제없음 — 지적한 두 실패 경계 수정 확인 후, 제한된 native 연결 검증을 진행할 수 있다.** 이번 판정은 구현 사전 검수이며 장기 메모리 안전성·음악 학습 개선·실제 resume 성공을 인증하지 않는다.

- Critical: 미해결 사항 없음.
- Warning: 미해결 구현 결함 없음. 아래 운영·검증 한계는 유지해야 한다.
- Suggestion: 없음.

## 발견과 해결 확인

1. **terminal step 뒤 reset 실패 시 폐기 전이 수 누락.** 최초 구현은 성공한 terminal step을 로그에 저장한 후 reset하고, 마지막에 progress를 기록했다. reset에서 guard/timeout이 나면 `discarded_transitions`가 환경 수만큼 적게 보고됐다. 현행 `parallel.py`는 step/episode 집계 직후 progress를 먼저 전달하고 reset을 수행한다. guard와 timeout을 각각 주입하여 마지막 완료 tick과 전이 수가 유지되는 회귀 검사도 추가되어 있다. 이전 소스는 `pool_before_tick_accounting/`에 보존되었다.

2. **strict resume 실패 뒤 잘못된 복구 모델 생성.** 최초 구현은 trainer 생성 뒤 load 실패도 동일한 실패 저장 경로를 사용하여 무작위 초기 상태 또는 부분 로드 상태를 `failure_last_valid.pt`로 저장할 수 있었다. 현행 `train_parallel.py`는 `recovery_eligible=False`로 시작하고 fresh 초기화 또는 strict load 완료 뒤에만 true로 전환한다. `monitoring.py`는 부적격 상태에서 파일을 만들지 않고 `resume_not_validated`를 보고한다. 실제 PPO identity mismatch 시 원 checkpoint SHA 유지·복구 파일 미생성, 정상 load 후 복구 checkpoint 재로드 검사가 추가됐다. 이전 소스는 `runner_before_resume_eligibility/`에 보존되었다.

## 코드 검수 범위

보관본과 현행 train_parallel.py/parallel.py 변경분, monitoring.py/dense_environment.py/task_sampling.py 및 해당 검사를 읽었다. 기존 ppo.py와 training_environment.py는 보관본과 내용이 동일함을 확인했다.

- **Legacy 계약:** 음악 옵션이 없거나 legacy 고정 목표이면 기존 TrainingEnvironment와 정본 목표 생성 경로를 그대로 사용한다. 음악/성공 판정·비용·관측·PPO identity를 변경하지 않는다. dense_v2는 별도 reward 계약을 추가하므로 기존 legacy checkpoint의 strict load가 거부되는 것이 의도된 동작이다.
- **Dense 보상:** 원 환경이 반환한 네 실제 240Hz 표본과 동일 step의 음악 측정을 짝지어 추가 항을 적분한다. 반환 reward, reward_terms, 누적 reward와 종료 episode reward를 함께 보정한다. 성공 ledger·안정성 비용·제어 목표나 native 상태에는 쓰지 않는다. 오른손 guide의 signed normal·유한 현 위치·깊이·시간창이 기존 기하 타현 정의와 일치하며, 속도는 두 표본 각각의 기타 로컬 좌표 차분으로 계산한다. 이는 접촉·음향 측정이나 연주 성공을 대체하는 항이 아니다.
- **목표 pool:** 명시된 모든 B 이벤트를 검증하고 미지원/비단음/열린현을 조용히 제외하지 않는다. 각 worker는 seed+worker_id로 재현되는 비복원 순환 선택을 사용한다. 정책 계약에는 전체 후보 목록이 고정되고 개별 episode 목표는 reset 감사와 compact info에 별도 기록된다. reset마다 실제 measurement와 observation builder가 새 목표를 참조한다.
- **IPC·실패:** pending pipe와 전체 process sentinel을 함께 기다리고 반환 순서는 요청 순서로 복원한다. EOF/비정상 종료/전송 오류와 timeout은 pool을 무효화하고 부분 buffer를 반환하지 않는다. 짧은 poll 중 메모리 검사와 현재 worker 상태를 기록하며, close→terminate→kill은 전체 worker 공유 유예 시간을 사용한다. terminal/truncation bootstrap과 worker별 부분 reset 계산은 유지된다.
- **감시·복구:** 백그라운드 감시와 foreground callback은 동일 잠금으로 로그/status를 갱신한다. 낮은 MemAvailable과 probe 오류는 latch 후 foreground에서 중단한다. optimizer에 비동기 예외를 주입하지 않으며 기존 PPO의 예외 시 모델·optimizer·RNG 복원 뒤 저장한다. 실패 저장 실패가 원 예외를 대체하지 않으며 실제 종료 이유와 worker 종료 조치를 기록한다. 원본 입력 pin·부모/자식 import 감사·물리 flag 검사는 유지된다.

## 검증과 남은 범위

담당자가 보고한 관련 CPU 결과는 runner/monitor 13개, parallel 11개, dense/sampling 7개 통과다. 검사 소스에서 fake RAM·대기/종료/순서·reset 실패·strict load·reward 합산·목표 계약 검증 경로를 확인했다. 이후 루트 담당자의 cpu_tests.log에서 최종 전체 CPU **126개, 27.320초, OK**를 확인했다. 검수자가 전체 CPU 검사나 native 실행을 추가하지는 않았다. 실제 최소 연결/중도중단/복구 검증은 후속 증거로 남겨야 한다.

RAM 감시는 주기적 표본 및 foreground 경계에서 작동한다. 그 사이의 급격한 RAM 고갈, OS SIGKILL, 파일 시스템 실패에서 저장을 보장하지 않는다. RSS/PSS/peak는 서로 다른 지표이며 환경 수8이나 RAM 여유4GiB만으로 장기 안전성이 증명되지 않는다. 복구 checkpoint는 PPO/optimizer/RNG 상태이며 native solver의 중단 시점 재현이 아니다. 변경된 dense reward 또는 sampled task 계약은 새 학습 조건으로 취급해야 하고, 기하 보상 증가만으로 음악 수행 개선을 주장해서는 안 된다.

새 물리·학습·영상 실행이나 자산 변경은 수행하지 않았다. 이 review_preflight.md 외 파일은 수정하지 않았다. 최종 입력 봉인·문서·source_final/inventory는 루트 담당 범위다.

## 검수 시점 SHA256

| 파일 | SHA256 |
| --- | --- |
| train_parallel.py | `b6eb831ef91bb1a5dac605e42d40bf27b070081233f5e0d5952a74a62a147c01` |
| monitoring.py | `b11186fb743e141e5f157b2d71b0db174bcf2285e8ca327242147f198b5fa21e` |
| parallel.py | `a267340e7b75c3e93a752de2a8c57aeaf4e16559d820ec686d232a6232514d14` |
| dense_environment.py | `10c81e2e3bbd7cf943e43d0dbbaa7511327cdd6b86dd65c45604f3f8575f0cac` |
| task_sampling.py | `183102c3c87f02d2fc2b79903d7085eb552cfa41e9666dbdefcfa07b0cdf4ff9` |
