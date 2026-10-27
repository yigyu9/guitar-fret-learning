# 자원 실측 후 양손 개별 장기 학습

2026-10-19 00:47:39 KST에 **장기 학습을 시작했다**. 이 문서는 실행 설정과 선택 근거이며, 2시간 학습 완료나 음악 목표 성공을 뜻하지 않는다. 최신 생존 상태는 `long_supervisor_v1/status.json`, 초기 전체 에피소드 확인은 `early_status_v1.json`/`early_status_v1.md`를 본다. 종료 후에는 두 trainer의 `report.json`과 `musical_quality_report.json`을 확인해야 한다.

## 선택한 구성

- 왼손 16환경 + 오른손 16환경을 동시에 실행한다. 서로 독립된 specialist 정책이며 양손 결합 정책은 아니다.
- 손별 최대 7,200초, 최대 256 PPO 업데이트다. 시간은 업데이트 경계에서 확인하는 soft 제한이므로 시작·현재 업데이트·정리가 더 걸릴 수 있다. 명목 종료는 **2026-10-19 02:47:39 KST 전후**다.
- CPU native PhysX worker 총32개, 정책/가치망은 RTX4070Ti의 `cuda:0`, 기존 medium 규모를 사용한다. 상태563·행동39를 유지한다.
- H120 × 16환경 = 손별 업데이트당1,920전이다. 최대 예산은 손별491,520전이, 합계983,040전이이며 2시간에 이 상한을 채운다는 예측은 아니다.
- H120은 2초의 수집 단위다. 수집기는 업데이트 사이에도 환경 상태를 이어가며 7초 episode가 끝날 때만 해당 환경을 초기화한다. 첫2초도 정책이 목표를 보고 준비한다. 2초마다 시작 자세로 되돌리지 않는다.
- 메모리 여유6GiB 보호선, worker 응답300초 제한, 자원 기록5초·터미널 heartbeat10초, 체크포인트5업데이트 간격을 유지한다.
- 현재 곡은 `05_BN2-131-B_solo`의 첫 단일 압현 이벤트, stage1(±0.5초)다. 전곡·다양한 곡·양손 통합 학습으로 확대하지 않는다.
- Root고정·하체유한·기타자유/중력ON/스트랩OFF, 기존 유지제어·안전 종료·보상은 바꾸지 않았다.

## 실측 선택 근거

장비는 i9-13900(32논리CPU), RAM약31.1GiB, RTX4070Ti12GB다. 물리 시뮬레이션이 CPU 기반이므로 GPU 사용률100%보다 처리량과 메모리 여유를 기준으로 선택했다. 비교 원자료는 `pilot_comparison_v1.json`이다.

| 비교 | 수집 처리량 | 실행 전체 처리량 | 비고 |
|---|---:|---:|---|
| 왼손 N8 단독 |29.60전이/s|24.73전이/s|960전이 / trainer wall38.82초|
| 왼손 N16 단독 |35.53전이/s|30.65전이/s|1,920전이 / trainer wall62.65초|
| 양손 N8씩, 총16 |합계36.82전이/s|29.20전이/s|1,920전이 / supervisor65.76초|
| **양손 N16씩, 총32** |**합계46.72전이/s**|**36.83전이/s**|3,840전이 / supervisor104.27초|

수집 처리량은 데이터 수집 시간만, 전체 처리량은 시작·업데이트·정리까지 포함한다. 단독은 trainer wall, 동시 비교는 supervisor wall로 계측 범위가 다르다. 두 동시 구성끼리 비교하면 총32개가 약26.1% 빠르다. 단독 수집만 비교하면 N16이 N8보다 약20.0% 빠르다. 측정하지 않은 모든 환경 수 중 최적이라는 주장은 하지 않는다.

선정 pilot의 host 최소 MemAvailable은14.4567GiB, trainer 최소 표본은13.9350GiB였다. 표본 시점이 다르므로 값을 혼용하지 않는다. Host CPU busy는 첫 표본을 제외한 평균80.61%, GPU 메모리 최대7,035MiB였다. 이는 다른 host 작업도 포함하는 짧은 관측값이다. 환경 추가는 IPC·메모리·CPU 경합을 늘리므로 비교한 범위에서 가장 빠르고 메모리 여유가 확인된32개를 선택했다.

모든 pilot는 첫2초 준비 구간만 수집했으며 **완료 episode는0개**다. 음악 품질·반복 reset·장기 처리량의 근거로 사용하지 않는다. 장기 초기 구간에서 7초 전체 episode와 reset을 별도로 확인한다.

## 모델 재개와 보존

처리량 비교의 공통 출발은 로그 개선 단계의 LH update3 / RH update1이었다(`initial_models_v1.json`). 장기는 선택한 dual16 pilot의 최종 LH update4 / RH update2에서 **모델·Adam·RNG·계수 전체를 strict resume**한다. pilot의 수락된 업데이트도 이어가며 원본 모델은 덮어쓰지 않는다.

PPOConfig는 그대로다(선언 actor_lr1e-5, value_lr3e-4, minibatch240, epochs2, targetKL0.02). 실제 재개 actor LR은 KL 보호 이력을 이어받은 LH1.5625e-7 / RH6.25e-7이며 선언값으로 초기화하지 않는다. 이 작은 실제 LR은 향후 학습 진전 해석에 함께 봐야 한다. 우선 요청한 장기 학습을 동일 방법으로 수행하며 LR·보상·난이도를 실행 중 몰래 바꾸지 않는다.

- `source_pins_v1.json`: 현행 생산 소스169파일 SHA. 이번 작업에서 생산 코드는 변경하지 않았다.
- `long_execution_pins_v1.json`: 실제 사용한 모델·설정·plan·실행기6파일 SHA.
- `long_launch_v1.json`: 실제 detached supervisor PID·시작·명목 종료 시각.
- `long_plan_v1.json`, `long_left_settings_v1.json`, `long_right_settings_v1.json`: 실제 설정.
- `run_pair_v1.py`: 두 trainer를 시작하고 host 자원을 기록하는 이번 실험 전용 실행기.
- `pilot_*`: 자원 비교 원자료. 실패가 발생하면 별도 증거로 보존하며 덮어쓰지 않는다.

## 로그·모델·확인 방법

| 경로 | 내용 |
|---|---|
|`long_supervisor_v1/status.json`|시간·양손 trainer PID/returncode. `null`은 종료 전이라는 뜻이다.|
|`long_supervisor_v1/host_resources.jsonl`|실제 host CPU·MemAvailable·GPU5초 표본|
|`long_supervisor_v1/result.json`|supervisor 종료 결과. 각 trainer returncode도 확인한다.|
|`long_left_v1.log`, `long_right_v1.log`|실시간 진행·보호/오류·업데이트 출력|
|`long_left_v1/`, `long_right_v1/`|손별 모델·학습 지표·episode·원전이·입력/소스 봉인|
|손별 `learning_status.json`|현재 음악/안전 누계와 durable/committed 회계|
|손별 `update_*.json`, `learning_metrics.jsonl`|실제 PPO 업데이트·KL·LR·reward/cost·품질|
|손별 `episodes.jsonl`|7초 완료 episode·안전 실패·역할별 성공 및 실패 이유|
|손별 `checkpoint_*.pt` / `final.pt`|정기/최종 모델. 최종파일은 종료 후 생성된다. 실제 이름은 디렉토리에서 확인한다.|
|손별 `report.json`, `training_summary.json`, `musical_quality_report.json`|정상/처리된 중단 후 최종 결과. `completed`는 실행/audit 상태이며 음악 성공과 구분한다.|

이 실행은 채팅/터미널과 분리된 프로세스에서 계속된다. 다른 실험을 겹쳐 실행하기 전에 현재 status와 실제 PID를 확인한다. 안전 중단이 필요하면 이 실행의 supervisor에만 SIGINT를 보내고 두 trainer의 정리를 기다린다. 기록된 PID를 재사용할 때는 프로세스 신원을 먼저 확인한다. 프로세스 전체 종료 명령을 사용하지 않는다.

재개는 손별 최신 유효 checkpoint와 같은 settings로 `guitar_learning.train_musical_quality --settings <설정> --resume <검증된 checkpoint> --out <새 결과 디렉토리>`를 실행한다. 과거 출력 디렉토리는 재사용하지 않는다. 실제 중단 지점의 report/accounting으로 유효한 모델을 확인하고, 실패·미반영 전이를 재개 성공으로 간주하지 않는다.

이번 검증은 장기 실행 시작 및 초기 경과 확인이다. 장기 종료 후 성공률 추이, release/extra-strike·KL/LR·물리 실패·실측 처리량을 분석해야 학습 효과를 판단할 수 있다. 사람 유사성·실제 압력·음향·새곡 일반화는 평가하지 않는다.
