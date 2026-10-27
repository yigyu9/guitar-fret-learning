# PALM_RATE의 native DOF force 관측

2026-10-07. 이 문서는 기존에 완료된 sensor-only 계측의 저장 자료를 보여준다. 계측 단계에는 두 fresh attempt가 있었다. 첫 attempt는 `std::bad_alloc`으로 0 physics step에서 실패해 로그와 자료를 보존했고, 수정된 `attempt_v2`는 120 step을 완료했다. 이 그림 생성 과정에는 native 실행이나 설정 변경이 없다.

## 그림

![두 어깨 native total DOF force와 완료-step 좌표 gap](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dof_force_observation_v1/artifacts/dof_force_observation.png)

왼쪽 panel은 `sensors.json`에서 요약된 `native_total_DOF_force`를 signed Nm로 표시한다. 오른쪽은 각 완료 physics step n의 실제 관절 scalar 좌표와 직전 전달 목표(`controls[n−1]`) 차이의 절대값을 degree로 나타낸다. Force sensor는 105개 native DOF에서 type code 1(회전), 단위 Nm로 기록됐다. Step0 force는 측정하지 않아 null이며, 첫 점은 완료 step1 / 1⁄240 s다. 초기 샘플을 0으로 만들지 않았다.

## 선택 관절 요약

| Native DOF | Signed force 최소 (Nm) | Signed force 최대 (Nm) | 절댓값 최대 (Nm), step | 완료-step scalar gap 최대 / 최종 (°) |
|---|---:|---:|---:|---:|
| L_Shoulder_x | −14.536089 | +0.112701 | 14.536089, 1 | 21.619762 / 21.619762 |
| R_Shoulder_z | −1.187056 | +5.564084 | 5.564084, 1 | 17.266792 / 17.266792 |

120개 센서 표본 모두 nonzero였지만 이는 관측일 뿐 판정 gate가 아니다. 총 DOF force 값은 actuator-only 토크, 접촉력, effort 포화 또는 PD 부족의 원인을 분리하지 않는다. 관절 좌표 차이는 native scalar 차이며 물리적 상대 회전각이 아니다.

기타 최대 위치/회전 오차 36.091149 mm / 4.761921°, LH source-center 최대 이탈 90.540508 mm는 이전 PALM_RATE 0.5초 실행과 그대로였다. 왼손 contact 행도 이전과 같아 유지 실패는 남는다. 이번 force-only 계측이 기타 유지나 물리 지지를 인증하지 않는다.

초기 기타 위치(Z +5 mm)와 기존 초기 회전, 고정 LA `1.1010801317960974 m`, 초기 관절각, PD/solver, 66개 주요 DOF·몸통9·손가락42·C02 하체 목표는 동일하다. 제어, 목표, 초기값, 물리는 변경하지 않았다. 다음으로 검토 중인 [어깨 stiffness 비교 제안](/home/ajou/yigyu/3/stability_adapter_2/SHOULDER_PD_COMPARISON_PROPOSAL.md:1)은 L/R shoulder 6 DOF의 stiffness 200→300 비교일 뿐이며 사용자 확인 전이고 아직 구현·실행하지 않았다.

## 재생성 및 provenance

```bash
MPLCONFIGDIR=/tmp/dof_force_observation_mpl python /home/ajou/yigyu/3/stability_adapter_2/plot_dof_force_observation.py \
  --input /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dof_force_observation_v1/summary.json \
  --out /tmp/dof_force_observation_reproduction.png
```

Plotter는 summary의 170개 입력 SHA와 `attempt_v2/force_report.json`의 167개 SHA, six sensor checks, 120개 완료 샘플과 type/unit metadata를 확인한다. 실행 명령과 종료 상태는 `plot_execution_v1.json`; input·plotter·image SHA는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dof_force_observation_v1/artifacts/plot_manifest.json)에 있다. 이전 실패·부분 자료와 v2 성공 로그는 보존했다.
