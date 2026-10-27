# 원본과 현재 CPU 진단의 PD 구동 경로 그림

2026-10-07. 이 자료는 원본 `tab2body`와 현재 `stability_adapter_2`의 코드·감사 JSON을 정적으로 비교한다. 시뮬레이터를 초기화하거나 physics step을 실행하지 않았다. 입력 감사는 105개 nominal DOF와 6개 계약, 101개 SHA를 확인했다.

## 코드 경로도 및 105축 nominal 값

![원본 explicit force와 현재 position-target 경로 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1/artifacts/pd_actuation_paths.png)

이 그림은 이미지/렌더링된 physics 결과가 아니라 저장 코드와 감사 자료의 경로도다. Fret와 Strike task-policy 이름은 각각 30개(팔 9 + 손가락 21)이며 서로 겹치지 않고, 두 30개 이름 집합은 현재 `main66` 이름에 포함된다. `main66`에 추가 6개 이름이 있고 `Torso9` 이름은 별도의 PD-hold 인터페이스다. 이 이름 관계를 새 학습 action 차원 결정으로 해석하지 않는다.

| audited name group | DOF 수 | nominal kp | nominal kd | explicit cap 값 (Nm) |
|---|---:|---:|---:|---:|
| Fret policy | 30 | 20–200 | 5–50 | 4–150 |
| Strike policy | 30 | 20–200 | 5–50 | 20–150 |
| Main66 중 task 이름 외 | 6 | 200 | 50 | 150 |
| Torso9 PD-hold 이름 | 9 | 600 | 150 | 300 |
| 나머지 native DOF | 30 | 30–300 | 7.5–75 | 300 |

위 수치는 모두 `audit.json`의 105 `nominal_rows`에서 묶어 계산했다. 감사 체크는 원본 gain/cap 계산값이 저장 native stiffness 200의 숫자와 105축 모두 일치했다고 기록하지만, 숫자 일치가 actuator 동등성은 아니다.

## 구현상 경로와 해석 한계

그림의 `(target, q)`는 목표와 실제 DOF 좌표의 두 입력을 뜻한다. `q`는 PD target의
구성 요소가 아니라 실제 상태이며, 그림은 두 입력을 한 상자에 표시했다.

원본 `tab2body/env/base.py`는 POS drive mode에서 stiffness를 0, damping을 `kd`로 설정하고, step마다 explicit `τ = kp × (target − q)`를 계산해 ±cap으로 자른 뒤 `set_dof_actuation_force_tensor`로 보낸다. 공식 [Isaac Gym tensors 문서 384행](/home/ajou/yigyu/3/isaacgym/docs/programming/tensors.html:384)은 actuation force tensor가 `DOF_MODE_EFFORT`인 DOF에만 적용된다고 적는다. 이 정적 코드/문서 차이만으로 원본 force가 실제로 무시됐거나 bug/failure였다고 결론 내릴 수 없다. 원본 importer의 runtime 응답은 이번 감사에서 측정하지 않았다.

현재 [환경 코드](/home/ajou/yigyu/3/stability_adapter_2/environment.py:162)는 POS drive mode와 solver `stiffness=kp`, `damping=kd`, numeric effort property를 두고, [position-target API](/home/ajou/yigyu/3/stability_adapter_2/environment.py:221)를 사용한다. 이 경로에는 custom arm torque 제출이 없다. 현재 팔 경로와 원본 explicit torque 경로의 실제 actuator equivalence는 확인하지 않았다. Total DOF force 역시 actuator-only torque가 아니다.

원본 기타 고정·gravity off·하체 매 step state 재주입 조건은 현재 자유 기타 환경에 승계하지 않는다. Strike grip의 `pinch` action 범위는 손의 물리 hard limit 고정을 뜻하지 않는다. 실제 변경이나 runtime 진단을 위한 별도 제안은 사용자 확인 전이며 실행되지 않았다.

## 재생성 및 provenance

```bash
MPLCONFIGDIR=/tmp/pd_paths_plot_reproduction MPLBACKEND=Agg \
python /home/ajou/yigyu/3/stability_adapter_2/plot_pd_paths.py \
  --run /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1 \
  --out /tmp/pd_actuation_paths_reproduction.png
```

실제 그림 생성은 exit 0, native initialization 0, physics steps 0이다. command·환경·log는 [plot_execution_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1/plot_execution_v1.json) 및 [plot_run_v1.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1/plot_run_v1.log)에 있다. [Manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1/artifacts/pd_actuation_paths.manifest.json)는 입력 101 SHA, audit execution, producer, 코드 문서 hash와 PNG SHA를 분리해 보관한다. [독립 검수](runtime_review.md:7)를 완료했고 남은 finding은 없다.
