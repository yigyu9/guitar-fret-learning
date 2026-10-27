# Native 저장 목표 readback 관측

2026-10-07. 기존 PALM_RATE 0.1초 실행에서 getter를 읽은 결과를 저장 자료로 그렸다. 새 실행은 이 계측 단계에서 fresh 1회·24 physics steps였고, plot 제작 과정에는 추가 native 실행이나 설정 변경이 없다. 첫 getter는 physics step 0 직전 실제 측정이며 synthetic 값이 아니다.

## 그림

![L_Shoulder_x 제출 목표와 native 저장 목표, 전체 축 readback 차이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/native_target_readback_v1/artifacts_validated/native_target_readback.png)

왼쪽은 `L_Shoulder_x`의 Python 제출 목표(`submitted_targets_rad`)와 getter가 읽은 native 저장 목표(`native_stored_targets_rad`)다. Before/after 48개 읽기 시점을 시간순으로 표시했으며, 한 physics time에 after와 다음 before read가 둘 다 있어 동일 x 시점이 반복된다. 제출/저장 목표는 관측된 값이 정확히 겹쳐 보인다. 오른쪽은 각 readback의 105축 전체에서 구한 `max(abs(native_stored_targets_rad − submitted_targets_rad))`다. 축 단위는 rad다.

48회 getter read 모두에서 저장 목표와 제출 목표의 차이는 관측상 0 rad였고, 원 보고서 최대 절대 차이도 0 rad였다. 이 값은 기록된 결과이지 성공 gate가 아니다. `get_actor_dof_position_targets`가 반환한 float32 105개 값을 복사했고, getter 전후 state·Python target·PD properties 보존 및 기존 7개 배열의 exact 일치 검사가 통과했다. t=0 읽기는 측정된 before-step 값이며, t=0 force sensor 샘플로 혼동하지 않는다.

기타 최대 위치/회전 오차는 6.874400844 mm / 1.519676367°, LH source-center 최대 이탈은 47.473935095 mm로 이전 PALM_RATE 0.1초 기록과 같았다. 이 좁은 0.1초 구간의 target-readback 일치는 actuator/PD 원인, 후기 추종, 기타 유지 또는 지지 성공을 증명하지 않는다. force/torque를 측정한 그림도 아니다. 어깨 stiffness 200→300 제안은 별도이며 사용자 확인 전이다.

## 조건과 시점

기존 초기 기타 위치(Z +5 mm)·회전, LA `1.1010801317960974 m`, PD/solver, root, PALM_RATE, 66개 주 DOF·Torso9·finger42·C02 하체 목표와 변화율 제한을 유지했다. Target getter만 read-only 관측으로 추가했다. 각 physics step n에서 before read는 `n/240 s`, after read는 `(n+1)/240 s`; `readbacks.json`의 physics-step 번호로 이 시간을 표시한다. 한 쌍의 getter 차이를 실제 목표 수정으로 해석하지 않는다.

## 재생성 및 provenance

```bash
MPLCONFIGDIR=/tmp/native_target_readback_mpl python /home/ajou/yigyu/3/stability_adapter_2/plot_native_target_readback.py \
  --run /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/native_target_readback_v1 \
  --out /tmp/native_target_readback_reproduction.png
```

Plotter는 report의 180개 입력 SHA, 48×105 getter 배열과 순서, native report의 13개 계약을 확인한다. 관측된 차이가 0인지 여부는 그림 통과 조건이 아니다. 실행 명령·환경·종료 코드는 [plot 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/native_target_readback_v1/plot_execution_v2.json)과 [plot log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/native_target_readback_v1/artifacts_validated/plot_run.log), report·plotter·image SHA는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/native_target_readback_v1/artifacts_validated/plot_manifest.json)에 기록했다. 앞선 표시 초안은 [source_plot_v1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/native_target_readback_v1/source_plot_v1/plot_native_target_readback.py) 및 [source_artifacts_v1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/native_target_readback_v1/source_artifacts_v1/native_target_readback.png)에 보존했다. Fresh attempt는 한 번의 24-step 실행이고, 이 실행에서 물리 step은 총 24회다.
