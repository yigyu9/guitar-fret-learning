# 시뮬레이터를 유지하는 학습 초기화

기존 학습은 초기 자세를 한 번 검증하기 위한 session 생성·종료 절차를 episode reset에도 사용했다. 따라서 약 1.47초의 단음 episode가 끝날 때마다 sim을 파괴하고 자산과 장면을 다시 만들었다. 물리 엔진이 요구하는 동작이 아니라 학습 연결 구현의 문제였다.

새 권장 진입점은 **`guitar_learning.train_persistent`**다. worker마다 sim/env/actor/asset과 제어기를 한 번 생성하고, episode 경계에서 상태와 이력을 초기화한다. 종료 때만 sim을 파괴한다. 기존 실행 중인 학습의 소비 Python·설정·입력과 원자료는 변경하지 않았다. 새 방식은 다음 실행부터 사용한다. 새 장기 학습은 시작하지 않았다.

## 구현과 유지한 조건

| 파일 | 변경 내용 |
| --- | --- |
| [persistent_session.py](/home/ajou/yigyu/3/guitar_learning/persistent_session.py) | 같은 native 장면에서 준비된 DOF q/qd·기타 pose/velocity·목표를 복원하고 인간 관절 effort와 제어 이력을 초기화 |
| [persistent_environment.py](/home/ajou/yigyu/3/guitar_learning/persistent_environment.py) | 원 환경의 reset 절차를 유지하면서 경계의 session 파괴만 생략. 오류·명시 close는 실제 정리 |
| [persistent_parallel.py](/home/ajou/yigyu/3/guitar_learning/persistent_parallel.py) | spawn worker에서 재사용 환경을 선택. Isaac Gym을 NumPy/Torch보다 먼저 import |
| [train_persistent.py](/home/ajou/yigyu/3/guitar_learning/train_persistent.py) | 기존 병렬 수집·PPO·저장·감시에 새 worker factory를 연결하는 별도 CLI |
| [persistent_audit.py](/home/ajou/yigyu/3/guitar_learning/persistent_audit.py) | 마지막 close 이후 생성/파괴·reset·금지 호출·상태 쓰기 계수와 readback을 최종 판정에 포함 |

관절 상태만 되돌리면 이전 episode의 제어·음악·안정성 이력이 남을 수 있다. 새 경로는 codec의 평활화/이전 목표, 제어기의 목표 기록·우손/해제 이력, 음악 시간과 측정 이력을 함께 초기화한다. 반면 FK·발/지지 기준·원본 관절 범위와 물성은 유지한다. 특히 제어기를 준비된 자세에서 새로 만들면 원래의 FK 기준이 달라지므로 기존 제어기를 보존한다.

- Root만 고정하고 하체는 기존 유한 제어를 유지한다. 105채널/비영범위 97축/원래 영범위 8축을 구분한다.
- 자유 기타·중력 ON·스트랩 OFF, 기존 모델·마찰·충돌 정책·의자·gain을 유지한다.
- 상태 쓰기는 episode 경계에만 허용한다. 기타 직접 보조 힘이나 제어 중 상태 덮어쓰기는 추가하지 않는다.
- 초기값 복원 뒤 **실제 물리 시간 2초**를 준비한다. 매 episode의 22초 검증이나 자산 재로딩을 수행하지 않는다. 2초는 벽시계 시간이 아니다.
- 상태468/이벤트64×24/우선토큰2×24/행동39와 기존 보상·음악 성공·안정성 종료·네트워크/PPO 계약은 유지한다. 정책이 하체 목표까지 직접 학습하는 변경은 아니다.

CLI는 해당 부모 프로세스에서 핵심 학습 실행 전체 동안 Pool binding을 바꾼다. 다른 프로세스의 기존 학습에는 영향을 주지 않는다. 같은 부모 프로세스 안에서 여러 학습을 동시에 thread로 실행하는 embedding API로 제공한 것은 아니다. 기존 `train_parallel` 직접 실행은 장면을 재생성하는 대조·재현 경로다.

## 실제 검증 결과

[최종 CPU 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_reset_v1/cpu_tests_v2.log)의 **146개 검사**를 통과했다. 같은 session의 재사용, 준비 480물리스텝, 제어 이력, 관측/보상 계약, 실패 시 close, worker 선택, 최종 lifecycle 근거 누락/재생성/추가 상태 쓰기의 실패 처리를 포함한다.

| 실행 | 환경 × horizon | 정책 전이 | 완료 episode | 초기 준비 포함 reset | 판정 |
| --- | ---: | ---: | ---: | ---: | --- |
| [기존 장면 재생성 대조](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_reset_v1/fresh_reference_v1/report.json) | 1 × 176 | 176 | 2 | 3 | 통과 |
| [같은 장면 반복](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_reset_v1/reuse_repeat_v1/report.json) | 1 × 704 | 704 | 8 | 9 | 통과 |
| [기존 checkpoint 재개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_reset_v1/reuse_resume_v1/report.json) | 2 × 128 | 256 | 2 | 4 | 통과 |
| [서로 다른 음악 목표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_reset_v1/reuse_pool_v1/report.json) | 2 × 192 | 384 | 4 | 6 | 통과 |

총 **1,520전이·완료 16episode·PPO 업데이트 4회**다. 재사용 3실행의 worker 총 5개는 각각 **create_sim=1, create_env=1, load_asset=2, destroy_sim=1**이었다. 반복 실행은 동일 sim/env/controller/FK를 9번 준비 과정 내내 유지했다. reset 경계에서 목표 이력 길이와 local clock은 0이며, 기타/인간 상태 쓰기는 마지막 경계 이후 증가하지 않았다. 모든 최종 guard·입력 변경·누락 import pin·원본 소스/모델 parity·worker/물리 플래그·정리 오류 목록은 비어 있다.

기존 실행의 완성된 `checkpoint_000014.pt`를 별도로 읽어 재개했다. 모델, 두 optimizer, cost weight, 계약, 업데이트 수, Python/NumPy/Torch/CUDA RNG가 새 실행의 initial checkpoint와 정확히 일치했다. 누적 업데이트 **15→16**과 최종 저장을 확인했다. 기존 장기 실행을 재시작하거나 그 파일을 수정하지 않았다.

음악 pool은 event `[0,1,2,3,4]`로 설정했고, 이번 짧은 실행의 정책 표본에는 **1·2·3·4**가 실제로 등장했다. 모든 후보를 실측한 것으로 설명하지 않는다. 서로 다른 종료 시점의 부분 reset을 확인했다.

## 복원 오차와 물리 결과

재사용 19개 경계의 상태 readback 검사는 각각 q/qd·기타 pose/velocity 허용치 1e-6 안에 들었다. 한 worker의 반복 9개 경계에서 최댓값은 DOF q/qd 오차 0, 기타 velocity scalar 오차 약 3.73e-9, 기타 위치 약 9.22e-8m, 회전 약 1.15e-7rad였다.

그러나 **2초 준비 후 자세가 새 장면과 완전히 같은 것은 아니다.** 새 장면의 준비 3회는 같은 q/qd·위치·목표였지만, 재사용 준비 9회를 첫 새 장면과 비교하면 다음 차이가 있었다. 회전은 정규화된 쿼터니언의 SO3 차이로 계산했다.

| 준비 후 차이 | 최댓값 |
| --- | ---: |
| 인간 DOF q | 0.00098330 rad |
| 인간 DOF qd | 0.02332013 rad/s |
| 인간 link 위치 | 0.6166 mm |
| 기타 body 위치 | 0.7189 mm |
| 기타 body 회전 | 0.00155289 rad |
| 105채널 제어 목표 | 0.00000258 rad |

이는 상태 복원 뒤 실제 물리 적분의 차이이며, 비공개 PhysX solver/contact cache까지 직렬화·복원했다고 주장하지 않는다. 반복 준비 9회의 양발 접촉과 세 부위 양성 지지는 모두 있었다. 이 단기 범위에서 실용 초기화를 확인한 것이며 장기 분포의 완전한 동등성 증명은 아니다.

| 정책 구간 60Hz endpoint | 기존 대조 | 재사용 반복 | checkpoint 재개 | 음악 pool |
| --- | ---: | ---: | ---: | ---: |
| 한 부위 이상 기타 지지 | 100% | 100% | 100% | 100% |
| 세 부위 동시 양성 지지 | 92.045% | 92.756% | 97.266% | 88.802% |
| 양발 양성 접촉 | 100% | 100% | 100% | 100% |
| 기타 이동 최댓값 | 1.815mm | 2.116mm | 1.444mm | 2.047mm |
| 물리 실패가 기록된 전이 | 0 | 0 | 0 | 0 |

세 부위의 접촉 분담 변화는 허용한다. 표의 접촉 비율과 편차는 compact 로그의 마지막 물리 표본, 즉 60Hz endpoint 집계다. 실패 지표는 환경이 각 전이의 네 240Hz 표본에서 합친 `failure_reasons`를 사용한다. 1,520전이는 준비 구간을 제외한 6,080물리스텝에 해당하며, 이 전 표본을 모두 raw로 저장한 것은 아니다.

모든 실행의 타현 매칭과 목표음 유지 누적 최댓값은 0이었다. 이번 결과는 초기화·수집·업데이트 연결 검증이며 연주 성능 개선이 아니다. 실제 현 압력·진동·음향은 검증하지 않았다.

## 시간과 메모리의 해석

N1 기존 방식은 reset 대기 합 76.958초/3회=25.653초, N1 재사용은 194.550초/9회=21.617초였다. 최초 생성과 실제 2초 준비를 포함한다. 다른 장기 학습과 자원을 공유한 짧은 실행이므로 일정한 가속 비율이나 공정한 성능 benchmark로 일반화하지 않는다. N2의 부모 reset 대기 합을 환경별 reset 수로 나눈 값은 분담 비용이며 개별 reset latency와 다르다.

5초 자원 표본의 worker 현재 RSS 합 최댓값은 기존 N1 약 664.16MiB, 재사용 N1 약 629.77MiB였다. 재사용 N2는 각각 약 1260.14MiB와 1261.70MiB였다. 별도 `resources.jsonl`에 현재 RSS/PSS와 peak를 보존했다. 이 짧은 검증으로 8시간 완주나 메모리 누수 부재를 주장하지 않는다.

## 다음 학습 실행

프로젝트 루트에서 아직 없는 출력 경로를 사용한다. 설정과 예산은 기존 권장 N8/H256/medium/dense_v2를 그대로 사용한다.

```bash
cd /home/ajou/yigyu/3
PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
PYTHONDONTWRITEBYTECODE=1 \
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.train_persistent \
  --settings /home/ajou/yigyu/3/guitar_learning/configs/long_B_8env_dense_v2.json \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_8env_dense_v2_persistent
```

같은 dense_v2 고정 목표 checkpoint에는 `--resume`을 붙인다. legacy 보상이나 다른 pool의 checkpoint를 강제로 연결하지 않는다. 재개는 정책/optimizer/RNG를 복원하고 새 물리 episode에서 시작한다. 실행 중이던 물리 solver나 sampler cycle의 중간 상태를 되살리는 기능은 아니다. 자세한 운영은 [PARALLEL_TRAINING.md](/home/ajou/yigyu/3/guitar_learning/PARALLEL_TRAINING.md)를 따른다.

`status.json`은 원 실행기의 진행 상태다. `core_report.json`은 원 실행기 결과의 정확한 바이트 보존본이다. **최종 판정은 `persistent_audit.json`을 합친 `report.json`**으로 확인한다. core가 성공해도 lifecycle 근거가 없거나 reset 중 재생성이 검출되면 최종 성공으로 처리하지 않는다.

## 보존과 남은 범위

- [이전 코드·검사·문서·설정 61파일](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_persistent_reset/archive_manifest.json)과 기존 실행의 소비 Python을 보존했다. 기존 Python 52파일은 변경하지 않았다.
- [실행 전 소스·설정·계획 78파일](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_reset_v1/source_run_v1/manifest.json), 중간 초안/실패 검사 수정의 보관본, CPU 로그, 네 native 실행과 콘솔을 보존했다. 실행에 소비된 Python은 이후 수정하지 않았다.
- [분석 원자료 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_reset_v1/analysis_inputs_before.json), [실제 수치와 checkpoint 대조](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_reset_v1/analysis.json), [분석 입력 무변경 확인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_reset_v1/analysis_verification.json)을 남겼다.
- [사전 독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_persistent_reset_v1/review_preflight.md)를 수행했다. 최종 독립 검수와 root의 source_final·artifact_inventory·final_verification은 결과 문서 확정 뒤 생성한다.

이번 계획의 구현·CPU 검사·반복 native·새 장면 대조·기존 checkpoint·부분 reset은 완료했다. 원 [실행 전 계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_persistent_reset_20261018.md)은 소비 전 보존본과 대응하도록 유지한다. 장기 재사용 안정성, 모든 음악 목표, 실제 연주 성능, 숨은 solver cache의 동등성은 별도 과제다.
