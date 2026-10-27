# Batch contract v1 — 초기 설정 입력·부분 재개 기능 진단

[변경 파일의 절대 경로·실제 줄 번호](CHANGED_FILES.md), [독립 검수 기록](review.md).

2026-10-06. 기존 `stability_adapter_2` 환경에 관절 절대각/절대 strap rest length를 전달하고, batch를 나누어 실행한 뒤 완료 trial을 건너뛰며 재개하는 입력·기록 계약을 확인했다. 세 trial은 각각 CPU PhysX에서 0.1초(24 physics steps) 실행했다. `stability_success`는 세 report 모두 `null`이며, 이 결과는 안정성 성공 판정이 아니다.

## 세 조건과 측정 결과

모든 조건에서 기타의 기준 target p/q는 같고, 초기 선속도·각속도는 모두 0이었다. humanoid root는 고정됐으며, report의 초기 상태·held target·root 검사는 세 run 모두 통과했다. 아래 p/q 오차는 각 trace의 최대 위치/회전 오차다.

| Trial | 설정 | 최대 위치 오차 (mm) | 최대 회전 오차 (deg) | 판독 |
|---|---|---:|---:|---|
| `H0_LA` | H0, 절대 rest length 1.0891851746440693 m | 65.315253 | 7.318146 | 기준 |
| `H0_RElbow_plus002_LA` | R_Elbow_x 절대각 −0.3378295232598935 rad (기준 −0.35782952325989353 rad에서 +0.02), 같은 길이 | 65.330385 | 7.315286 | 0.1초 endpoint에서 위치 오차는 기준보다 0.015133 mm 큼. 이 짧은 진단으로 개선을 판정하지 않음 |
| `H0_LA_plus001` | H0, 절대 rest length 1.0901851746440692 m | 65.315253 | 7.318146 | 일곱 trace sample의 기타 trajectory가 H0와 완전히 같음. 개선 후보로 선정하지 않음 |

초기 route 길이 세 run 모두 1.0891851746440693 m다. 각 report는 입력한 절대 rest length와 route 길이를 분리해 저장했다. strap route 길이는 0.1초 시점에 약 1.0355–1.0358 m였다. report의 `last_applied_tension_n`은 각 control sample에서 직전 physics substep에 적용한 값만 뜻한다. 기록값이 0 N인 것으로부터 전체 24 physics step에서 장력이 0이었다고 추론하지 않는다. 별도 비교 검증은 H0의 7개 측정 sample이 과거 `initial_environment_v3`와 완전히 일치하고, +0.001m 조건의 7개 기타 p/q/error/speed sample이 H0와 완전히 일치함을 확인했다.

초기 CPU source-shape query는 매 조건에서 R_Hip–G:body signed gap −1.331165 mm를 기록했다. 이는 query상 관통 후보이며 보정된 실제 관통 깊이나 PhysX clearance 인증이 아니다. 초기 palm signed normal z 성분은 0.869692208로 기록됐지만 cross-product 방향의 해부학적 부호는 아직 검증되지 않았다.

## 그림 10. 세 기능 진단의 기타 오차와 스트랩 길이

![세 batch trial의 기타 위치·회전 오차와 스트랩 route/rest 길이 시계열](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/batch_contract_v1/batch_contract_comparison.png)

그림은 checkpoint가 완료로 표시한 각 trial의 원본 `trace.json`에서 만들었다. 가로축은 시간(s), 세로축은 위치 오차(mm), 회전 오차(deg), strap 길이(m)다. 초록 H0 +0.001m trajectory는 파란 H0 baseline과 겹치며 범례에 이를 표시했다. 우측 패널의 점선은 설정된 절대 rest length, 실선은 trace의 strap route 길이다. CPU PhysX backend를 쓴 0.1초 기능 진단이고, 안정성 성공·무관통·GPU renderer 검증을 뜻하지 않는다.

## 실행·resume 계약과 검증

실제 partial 실행은 `--max-trials 1`로 한 trial을 완료한 뒤 같은 batch 입력을 resume해 나머지 두 trial을 마쳤다. checkpoint에는 세 report의 완료 경로/hash가 있다. `resume_validation.json`은 완료 3개·attempt 3개, resume 전 첫 report의 byte/mtime 불변, 현재 코드 hash 일치를 기록한다. 별도 보존 검사에서 기존 실험 파일 87개와 2026-08-19 원본 49개가 모두 변경되지 않았고, parent 종료 중 child subprocess의 batch lock 유지 및 child 종료 후 lock 해제를 확인했다. 테스트 로그에는 현재 13개 검사가 모두 통과한 것으로 기록됐다.

재현 시에는 기존 batch 결과를 덮어쓰지 말고 새 출력 디렉토리를 사용한다. 예시 입력은 저장된 manifest이며 두 번째 명령은 첫 번째와 같은 output 경로로 실행한다.

```bash
MUJOCO_GL=disable MPLCONFIGDIR=/tmp/stability_adapter_2_matplotlib \
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.run_batch \
  --manifest /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/batch_contract_v1/batch/manifest.json \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/batch_contract_v1/replay_batch \
  --max-trials 1

MUJOCO_GL=disable MPLCONFIGDIR=/tmp/stability_adapter_2_matplotlib \
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.run_batch \
  --manifest /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/batch_contract_v1/batch/manifest.json \
  --out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/batch_contract_v1/replay_batch \
  --resume
```

입력·checkpoint는 [manifest](batch/manifest.json)와 [checkpoint](batch/checkpoint.json)에 있다. 원시 trial은 [H0 report](batch/H0_LA/attempt_0001/report.json)·[trace](batch/H0_LA/attempt_0001/trace.json), [R_Elbow +0.02 report](batch/H0_RElbow_plus002_LA/attempt_0001/report.json)·[trace](batch/H0_RElbow_plus002_LA/attempt_0001/trace.json), [+0.001m report](batch/H0_LA_plus001/attempt_0001/report.json)·[trace](batch/H0_LA_plus001/attempt_0001/trace.json)에 있다. 재개 근거는 [partial log](partial_run.log), [resume log](resume_run.log), [resume 검증](resume_validation.json), [곡선 비교 검증](comparison_validation.json), [보존·lock 검증](preservation_and_lock_validation.json), [13개 test log](tests.log)다. 각 attempt의 `run.log`에는 CUDA device unavailable와 visual geom 오류가 남아 있다. 이는 CPU PhysX 실행과 구별되는 GPU/renderer 제한이며, 이 batch에서 GPU나 실제 장면 renderer를 검증한 것은 아니다.
