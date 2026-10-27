# GPU 물리 배치 학습 전환

2026-10-20. 사용자 요청에 따라 기본 손별 실행을 **GPU PhysX + GPU tensor pipeline + CUDA 배치 제어·측정·보상·PPO**로 전환했다. 정책만 CUDA로 실행했던 이전 벤치마크와 구분한다. 기존035/v14 초기 자세, Root 고정·105/97/8·자유 기타·중력ON·스트랩OFF·왼손 유연 제어를 유지했다.

사용자가 접촉 판정까지 GPU 방식으로 재설계하는 경로를 선택했다. 새 압현 후보는 실제 손가락 충돌 메시 표면 샘플과 유한 현·프렛 기하, 몸체 접촉 합력을 사용한다. GPU API가 접촉쌍·local witness를 제공하지 않으므로 기존 CPU clean 판정과 다른 `guitar_learning.gpu_loaded_geometry.v1` 계약이다. 샘플 사이 접촉을 놓칠 수 있고 몸체 합력은 접촉 상대·현 압력·음향을 인증하지 않는다. 지지 판정도 가까운 몸체의 합력 기반 새 계약이다.

## 현재 실행

[환경 설정과 기본 명령](/home/ajou/yigyu/3/guitar_learning/README.md), [실행·저장 흐름](/home/ajou/yigyu/3/docs/2026-10-26/learning_flow/README.md)을 따른다. 기본은CUDA·128환경·medium·H32·100업데이트다. GPU가 없으면 기본 실행은 오류로 종료하며 CPU 물리 재현은 `--physics cpu`로 명시한다. 환경 수1~1024를 허용하지만 모든 규모의 장기 안정성을 인증한 것은 아니다.

```bash
python -m guitar_learning.train \
  --hand left --device cuda:0 --physics gpu \
  --song 05_BN2-131-B_solo \
  --size large --num-envs 1024 --horizon 32 --updates 100 \
  --out /home/ajou/yigyu/3/runs/left_song_gpu_01
```

이 명령의100업데이트·음악 수렴은 시험하지 않았다. 원곡67음·1969tick/32.8167초를 유지하며32tick의 PPO 경계에서도 곡·물리·음별 원장을 이어간다. 실제 종료 환경만 초기화한다. CPU512/500 checkpoint는 GPU strict resume에서 거부한다.

## 실제 GPU 확인

장비는RTX4070Ti12GB, driver580.178.04, rl38/Python3.8.20, Torch2.4.1+cu121, Isaac Gym Preview4다. 아래 실행은 GPU를 순차 점유했다. 모든 최종 실행에서 실제 GPU PhysX/pipeline flags, CUDA 관절·root·몸체·접촉힘·Jacobian, 한 simulator 소유와 정상 종료, 입력 SHA·import pin을 확인했다.

| 시험 | 환경/모델 | PPO 반영 전이 | 이번 PPO | 실제 결과 |
| --- | --- | ---: | ---: | --- |
| [기준 자세 전곡](zero_action_song_v1/report.json) |2/정확한 행동0|없음:3938전이 측정|0|2/2 안전 전곡, 물리 실패0,67음별 원장·62개 수집 구간 확인|
| [large 배치](n1024_large_v4/report.json) |1024/large|65536|2|정상 저장, 실제 물리 실패979에피소드|
| [strict 재개](n1024_resume_v1/report.json) |1024/large|32768|1:누적3|추가 갱신·저장, 실제 물리 실패457에피소드|
| [기본 설정 규모](n128_default_v1/report.json) |128/medium|8192|2|정상 저장, 실제 물리 실패116에피소드|
| [오른손](right_n2_v1/report.json) |2/small|16|1|500상태·오른손 행동·PPO 저장 확인, 완료 에피소드0|

**1024는 단기 실행·저장·재개를 확인한 규모이며 안정적인 전곡 학습 환경 수로 인증하지 않았다.** 초기 무작위 정책의 기타 이탈·회전·관절 속도 실패가 많다. large 시험의979개 완료는 모두 물리 실패이며 전곡 성공으로 세지 않는다. 제어만 수행한 별도1024환경 진단에서도 초기32물리단계의 안전 기준을 모든 환경이 만족하지 못했다. 2환경 행동0의 안전 전곡은 초기 자세 유지의 근거이며, 학습 정책의 연주 성공·대규모 장기 안정성·수렴의 근거가 아니다.

large1024/H32/PPO2의 수집은18.547초, PPO는4.619초, 장면 생성·저장을 포함한 전체는30.116초였다. 수집 처리율은약3533전이/초, 수집+PPO는약2829전이/초다. GPU 가용 메모리의 표본 최소는3.32GiB, Torch allocated 최고3.12GiB/reserved5.23GiB다. 가용 메모리는 제어 tick/PPO 경계 표본이며 연속 NVML 최고 사용량 측정이 아니다. 측정·제어 계약과 수집 길이가 달라 이전 CPU 물리 벤치마크와 동일 품질의 속도 비교로 해석하지 않는다.

[재개 검증](resume_verification.json)은 재개 직전 final과 재개 직후 initial의 모델·두 optimizer·CPU/CUDA/NumPy/Python 난수·27값 curriculum buffer가 정확히 같음을 확인했다. 추가 PPO 후 모델 변경과 유한값도 확인했다. 새 프로세스의 물리 에피소드는 초기 자세에서 시작한다. [기존 CPU 모델 거부 검사](cpu_checkpoint_rejection.json)는 상태512·large 및 PPO 설정을 맞춰도 새 GPU 계약 때문에 strict load가 거부됨을 확인했다.

[선택 초기화 검사](selective_reset_v1/report.json)는 한 환경의 DOF·속도·기타 root·제어/접촉 캐시만 복원되고 다른 환경의 물리 상태·시계·제어 캐시는 보존됨을 실제 GPU에서 확인했다. 숨은 물리단계 없이 한 번만 초기화하고 다음4물리단계를 정상 진행했다.

[최종 콘솔 검사](native_console_checks.json)의 PhysX 접촉 누락/용량 경고와 CUDA 오류는0이다. 자산의 기존 시각 geom 로딩 오류6행은 남아 있으므로 콘솔 전체가 오류0이라고 주장하지 않는다. 충돌 자산·질량·COM·관성·DOF·shape 속성은 별도 실제 readback으로 검사했다.

## 구현과 실패 처리

`training/start.py → training/gpu_runner.py → training/gpu_pool.py → gpu/scene.py·control.py·environment.py`로 연결한다. 환경별 프로세스와 NumPy 상태 왕복을 없애고 CUDA 텐서를 공용 PPO에 전달한다. 로그·완료 요약·저장에는 host 전송을 사용한다. 하체는 기하 질량행렬·고정 반복 DLS IK·유한 stable PD, 상체는 중력·가슴/오른팔 지지를 사용한다. CPU solver와의 차이를 새 제어 계약에 기록했다.

Torch와 Gym의 외부 CUDA stream 사이에 명시적 완료 대기를 둔다. native 텐서는 실측한 env-local 좌표로 처리한다. 상태 setter는 에피소드 경계의 human DOF와 자유 기타 root에만 사용한다. reset 관측의 준비 몸체 snapshot은 첫 실제 물리단계 이후 native FK로 전환하며 실행 중 몸체 상태를 주입하지 않는다.

가슴 최근접 계산은 AABB512 후보를 인증하고 필요하면 전체 삼각형을 다시 계산한다. 비유한 값·인증 실패는 수집 중단이다. 유한하고 인증된 점의 지지 방향만 정의되지 않으면 해당 환경의 `support_control_invalid` 물리 실패다. 해당 행의 마지막 유효 힘을 현재4물리단계 tick 끝까지 유지하고, 양성 보상 억제·비용5·terminal 관측 계산 후 선택 초기화한다. 정상 방향이 돌아와도 그 tick의 실패를 취소하지 않는다. 이 추가 실패는 실제 large 시험에서1회 기록됐으며 보상·성공으로 상속하지 않았다.

## 보관·재현

- [전환 전 원문 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261020_before_gpu_batch_v1/manifest.json): 기존410 Python파일과README/AGENTS 원본. protected native·song/task.py·song/__init__.py·music_task.py는 그대로다.
- `n2_smoke_v1`, `n1024_large_v1/v2/v3`는 실패한 개발 실행이며 덮어쓰지 않았다. v1은CUDA 전달 시점 문제, v2는근접 후보 인증, v3는정의되지 않은 지지 방향으로 중단했다. 실패 자료는 PPO 반영/제외를 journal에서 구분한다.
- `diagnostics/`는 실제 전곡·재개 검사와 버전별 원문을 보관한다. compact/동일 원점·버퍼/aggregate 변경은 일부 PhysX 접촉 누락 경고 또는 물리 실패가 있어 **채택하지 않았다**. 활성 장면은 원래3m 배치다.
- [CPU 회귀 판정](cpu_regression/assessment.json):133모듈을 각각 새 프로세스로 검사하고 실패 모듈의 각 method도 단독 재실행했다. 최종 버전 고유785검사 중784통과·기존 teacher-proof preflight1개 SIGFPE·skip0다. 해당 검사와 연관 proof/train/parallel 소스는 전환 전 원문과 SHA가 같다. 전체 성공으로 보고하지 않는다. 최종 변경 GPU20검사는 별도 재실행해 모두 통과했고, 변경하지 않은 GPU scene/control10검사도 전체 검사에서 통과했다. 단일 프로세스·분할 실행의 실패 로그도 보존했다.
- `verification.json`, `source_manifest.json`, `review.json`은 최종 입력·검사·독립 검수 기록이다. 과거 CPU 결과·CAS·준비 입력을 수정하거나 GPU 성공으로 재분류하지 않았다.
