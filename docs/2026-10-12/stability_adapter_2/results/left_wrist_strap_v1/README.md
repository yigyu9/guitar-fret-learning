# 왼손목 기준 자세에서 초기 strap 길이 비교

2026-10-07. 새 기준 자세 `L_Wrist_x = −0.9063641667366027 rad`를 유지하고, cable law의 초기 0/1/2 N에 대응하는 고정 절대 rest length를 비교한 저장 ON run 9개다. 세 입력은 full humanoid q, body state, guitar state/goal, PD와 route가 동일하고 strap rest length만 다르다. 61개 source SHA가 현재 파일과 일치한다.

`reference_links/*/wrist_minus0050`은 이전 도구의 경로 형식을 유지하기 위한 alias다. 이름이 가리키는 실제 source run은 이전 `left_palm_boundary_v1`의 `l_wrist_x_minus0125` 설정으로, 예전 wrist angle −0.005 rad 결과가 아니다. alias 목적과 원본은 [reference link manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_wrist_strap_v1/reference_link_manifest.json:1)에 기록돼 있다.

## 세 가지 초기 설정

관절각은 세 입력에서 동일하고 초기 cable-law 장력에 대응하는 rest length만 다르다. 각 trial 도중 rest length는 고정이며 strap law tension은 시간에 따라 변한다. 값은 일정한 runtime force가 아니다.

| 입력 | 초기 법칙 장력 대응값 | 절대 strap rest length (m) | `L_Wrist_x` (rad) | 입력 JSON |
|---|---:|---:|---:|---|
| `load_00n` | 0 N | 1.1010801317960974 | −0.9063641667366027 | [load_00n.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/left_wrist_strap_v1/load_00n.json:1) |
| `load_01n` | 1 N | 1.1009134651294308 | −0.9063641667366027 | [load_01n.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/left_wrist_strap_v1/load_01n.json:1) |
| `load_02n` | 2 N | 1.1007467984627641 | −0.9063641667366027 | [load_02n.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/left_wrist_strap_v1/load_02n.json:1) |

## 저장 trace의 최대 기타 오차

아래 9개 run은 모두 ON이다. 각 값은 해당 구간의 최대 위치·회전 오차다.

| 구간 | 초기 법칙 장력 대응값 | 최대 위치 오차 (mm) | 최대 회전 오차 (°) |
|---:|---:|---:|---:|
| 0.1 s | 0 N | 6.874401 | 1.519676 |
| 0.1 s | 1 N | 6.838543 | 1.518452 |
| 0.1 s | 2 N | 6.821213 | 1.523082 |
| 0.5 s | 0 N | 35.481594 | 4.991597 |
| 0.5 s | 1 N | 35.482229 | 4.979386 |
| 0.5 s | 2 N | 35.577810 | 4.999207 |
| 1.0 s | 0 N | 73.268255 | 13.439339 |
| 1.0 s | 1 N | 118.622890 | 28.826878 |
| 1.0 s | 2 N | 120.835674 | 30.129771 |

![새 왼손목 기준 자세에서 세 초기 strap 길이의 저장 기타 오차 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_wrist_strap_v1/artifacts/left_wrist_strap_v1.png)

1 N과 2 N 설정은 1초 위치·회전 오차가 0 N 기준보다 모두 커 채택하지 않았다. 0 N은 새 왼손목 자세의 진단 기준으로만 유지하며, 기준도 큰 drift가 남아 안정 연주 성공은 아니다. 추가 OFF 비교는 하지 않았다.

1초 세 run 모두 arm 24개 PI joint 중 하나 이상이 212 held physics samples에서 포화됐다. 1초 최대 적용 tension은 15.035908–16.020121 N 범위로 달랐고, 종료 선속도는 0.293048–0.464767 m/s, 각속도는 1.191623–2.870732 rad/s였다. 이 값은 고정 force 조건을 뜻하지 않는다. 1초 LH/어깨 contact 행은 모두 0이며 contact 관측은 힘·원인·연속 지지·관통 깊이를 입증하지 않는다. Native target bounds 검사는 통과했지만 1초의 실제 arm scalar-limit 위반은 0.030297–0.030300°였다. 목표 제한 통과는 실제 상태의 제한 통과나 안정성 인증이 아니다. PI 보정은 arm 24개에만 적용했고 주요 66 연결을 유지했다. 손가락 42, 몸통 9, C02 하체는 PD 목표가 유지됐지만 실제 몸 상태가 고정된 것은 아니다.

## 다음 진단과 재생

부모 결정에 따라 같은 초기 관절각·LA `1.1010801317960974 m`·제어 설정으로 3초 진단을 수행할 예정이며, 기존 1초 prefix를 확인하고 후기 기타 위치·회전·속도·contact·포화 자료를 기록한다. 기간을 늘리는 관찰 진단이며 WAIT 조건이나 안정성 기준이 아니다. 새 controller/gain/gate/model/learning이나 기타 p/q feedback을 추가하지 않는다.

재생은 현재 comparison과 저장 trace만 읽으며 native trial을 만들지 않는다. 전역·행별 checks 및 139 embedded input SHA를 검사한다. 기존 산출물을 보존하기 위해 새 빈 output 디렉터리를 지정한다.

```bash
PYTHONPATH=/home/ajou/yigyu/3 MPLCONFIGDIR=/tmp/left_wrist_strap_mpl_repro MPLBACKEND=Agg \
  /home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_saved_arm_trials \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_wrist_strap_v1 \
  --out-dir /tmp/left_wrist_strap_user_reproduction
```

그림의 comparison·plotter·output hash는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_wrist_strap_v1/artifacts/plot_manifest.json:1)에 기록했다.
