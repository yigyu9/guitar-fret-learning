# 왼손바닥 source 경계 방향의 초기각 비교

2026-10-07. 기준 왼팔 자세의 초기 source 조건을 확인하고, 통과한 여섯 초기각 설정으로 ON 18회와 선택한 동일 각도의 OFF 대조 6회를 실행했다. 기준 포함 8개 입력 중 2개는 LH:palm–guitar signed source query 음수 pair 때문에 거부해 native 실행하지 않았다.

## 초기 입력 검사

표의 signed 값은 `LH:palm`이 포함된 가까운 source geometry pair의 최소 query다. 부호·크기로 PhysX clearance, 관통 깊이, 접촉 또는 지지력을 인증하지 않는다. 별도 `RH:palm/G:body` unsigned hull proxy와도 다른 값이다.

| 초기 조건 | 관절각 변화 | source 검사 | negative pair | 최소 LH:palm signed query (mm) |
|---|---:|:---:|---:|---:|
| 기준 | — | 통과 | 0 | 0.440263 |
| L_Elbow_x | +0.003125 rad | 통과 | 0 | 0.265971 |
| L_Elbow_x | +0.00625 rad | 통과 | 0 | 0.045009 |
| L_Elbow_y | −0.0015625 rad | 통과 | 0 | 0.013130 |
| L_Elbow_y | −0.003125 rad | 거부 | 2 | −0.387545 |
| L_Wrist_x | −0.00625 rad | 통과 | 0 | 0.333081 |
| L_Wrist_x | −0.0125 rad | 통과 | 0 | 0.167218 |
| L_Wrist_y | −0.0375 rad | 거부 | 2 | −0.100042 |

거부한 `L_Elbow_y −0.003125 rad`와 `L_Wrist_y −0.0375 rad`는 source 검사 단계에서 제외했다. 통과 입력과 수치는 [초기 입력 audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/initial_inputs.json:1)에 기록돼 있다.

## 저장된 native run 오차

아래는 각 저장 trace의 최대 기타 위치·회전 오차다. ON은 여섯 통과 초기조건 각각 0.1/0.5/1초, OFF는 `L_Elbow_y −0.0015625`와 `L_Wrist_x −0.0125 rad`만 같은 기간으로 대조했다.

| 구간 | 초기 조건 | 모드 | 최대 위치 오차 (mm) | 최대 회전 오차 (°) |
|---:|---|:---:|---:|---:|
| 0.1 s | 기준 | ON | 6.872551 | 1.519351 |
| 0.1 s | L_Elbow_x +0.003125 | ON | 6.872246 | 1.519329 |
| 0.1 s | L_Elbow_x +0.00625 | ON | 6.871966 | 1.519248 |
| 0.1 s | L_Elbow_y −0.0015625 | ON | 6.872239 | 1.519244 |
| 0.1 s | L_Wrist_x −0.00625 | ON | 6.871911 | 1.519243 |
| 0.1 s | L_Wrist_x −0.0125 | ON | 6.874401 | 1.519676 |
| 0.5 s | 기준 | ON | 35.481509 | 4.991410 |
| 0.5 s | L_Elbow_x +0.003125 | ON | 35.486269 | 4.980201 |
| 0.5 s | L_Elbow_x +0.00625 | ON | 35.479085 | 4.990976 |
| 0.5 s | L_Elbow_y −0.0015625 | ON | 35.479442 | 4.991030 |
| 0.5 s | L_Wrist_x −0.00625 | ON | 35.480294 | 4.991143 |
| 0.5 s | L_Wrist_x −0.0125 | ON | 35.481594 | 4.991597 |
| 1.0 s | 기준 | ON | 73.660431 | 13.502121 |
| 1.0 s | L_Elbow_x +0.003125 | ON | 116.694184 | 28.125562 |
| 1.0 s | L_Elbow_x +0.00625 | ON | 73.552292 | 13.475650 |
| 1.0 s | L_Elbow_y −0.0015625 | ON | 73.371659 | 13.452251 |
| 1.0 s | L_Wrist_x −0.00625 | ON | 73.663483 | 13.503909 |
| 1.0 s | L_Wrist_x −0.0125 | ON | 73.268255 | 13.439339 |
| 0.1 s | L_Elbow_y −0.0015625 | OFF | 6.872239 | 1.519244 |
| 0.1 s | L_Wrist_x −0.0125 | OFF | 6.874401 | 1.519676 |
| 0.5 s | L_Elbow_y −0.0015625 | OFF | 54.804833 | 7.939969 |
| 0.5 s | L_Wrist_x −0.0125 | OFF | 54.807644 | 7.940843 |
| 1.0 s | L_Elbow_y −0.0015625 | OFF | 144.193935 | 36.363384 |
| 1.0 s | L_Wrist_x −0.0125 | OFF | 144.267967 | 36.395296 |

![왼손바닥 경계 방향의 통과 각도 및 기준, ON/OFF 저장 trace 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/artifacts/left_palm_boundary_v1.png)

1초 ON에서 세 후보의 오차는 기준보다 조금 낮았다. 상위 두 후보를 같은 입력의 OFF와 대조하면 `L_Wrist_x −0.0125 rad` ON은 73.268255 mm/13.439339°, OFF는 144.267967 mm/36.395296°이고, `L_Elbow_y −0.0015625 rad` ON은 73.371659 mm/13.452251°, OFF는 144.193935 mm/36.363384°였다. 부모 결정에 따라 `L_Wrist_x −0.0125 rad`는 새 진단용 초기각 기준으로만 유지한다. 기준도 drift가 크며 안정 연주 성공이나 채택된 연주 자세로 보지 않는다.

모든 1초 ON run에서 arm 24개 PI 관절 중 하나 이상이 212 physics samples 동안 포화됐고, 해당 OFF run의 포화 sample은 0이었다. 1초 ON 최대 적용 strap tension은 15.017191–15.036838 N, OFF는 15.342925–15.358659 N이었다. 최대 적용값은 strap law의 일정한 장력 설정을 뜻하지 않는다. 종료 속도도 작지 않다: ON 여섯 조건은 선속도 0.293048–0.459840 m/s, 각속도 1.190872–2.666053 rad/s; 두 OFF는 각각 0.517255–0.517410 m/s, 3.245196–3.247943 rad/s였다. native arm target-bounds 검사는 모든 run에서 통과했지만, 1초 ON/OFF의 실제 arm scalar-limit 위반은 0.030286–0.030300°였다. 목표 제한 통과는 실제 상태의 제한 통과나 물리적 안정성 인증이 아니다. 1초 LH/어깨 contact 행은 모두 0이며, contact 행·sample은 접촉력·원인·연속 지지·관통 깊이를 증명하지 않는다.

이번 연결은 주요 66 관절을 유지하고 arm 24개만 PI target correction 대상으로 두었다. 손가락 42, 몸통 9, C02 하체의 PD 목표는 유지했으나 실제 humanoid 상태가 고정된 것은 아니다. 기타 목표·root·PD·solver·controller를 변경하지 않았으며 기타 오차 feedback도 없다.

## 다음 진단 및 재생

다음 비교는 결정 기록대로 이 전체 초기 pose에서 절대 rest length를 fresh-audit한다. 원래 cable-law 초기 장력 0/1/2 N에 대응하는 길이를 검사하되 각 run에서 rest length는 고정되고 law tension은 변한다. 이전 preload 비교는 다른 왼손목 pose에서 나온 자료여서 그대로 이어받지 않는다. 새 controller·gate·model·learning은 추가하지 않는다.

재생은 저장 trace만 읽고 native simulation은 추가하지 않는다. 전역·행별 comparison checks와 embedded input SHA를 검사하며, 기존 artifact를 덮어쓰지 않도록 새 빈 출력 경로를 사용한다.

```bash
PYTHONPATH=/home/ajou/yigyu/3 MPLCONFIGDIR=/tmp/left_palm_boundary_mpl_repro MPLBACKEND=Agg \
  /home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_saved_arm_trials \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1 \
  --out-dir /tmp/left_palm_boundary_user_reproduction
```

이 그림의 input·plotter·output SHA는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/artifacts/plot_manifest.json:1)에 기록했다.
