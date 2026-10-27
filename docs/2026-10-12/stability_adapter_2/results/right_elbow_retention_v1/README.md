# 오른팔 팔꿈치 초기각 비교

2026-10-06 결과. fine c02 기준 자세에서 오른쪽 팔꿈치 x/y/z축 중 한 각도만 바꾼 초기 query와, 통과한 후보의 저장 native run을 비교한다. 기타 +5 mm 목표, absolute strap rest length 1.1010801317960974 m, 기타 회전, Wrist, 좌측·proximal·손가락·Torso, C02 하체, root, PI/gain/cap은 유지했다.

초기 5조건 중 `R_Elbow_x +0.0025 rad`는 음수 source pair 1개로 제외해 native 실행하지 않았다. 기준과 x−0.0025/y+0.005/z+0.005 rad는 초기 조건 검사를 통과했다. 이 source query 관측은 PhysX clearance, 관통 깊이 또는 지지력을 보증하지 않는다.

## 최대 기타 오차

| 기간 | 조건 | 위치오차 (mm) | 회전오차 (°) |
|---|---|---:|---:|
| 0.1초 | reference | 6.872016 | 1.519281 |
| 0.1초 | x −0.0025 rad | 6.875722 | 1.519841 |
| 0.1초 | y +0.005 rad | 6.874411 | 1.519658 |
| 0.1초 | z +0.005 rad | 6.870843 | 1.519168 |
| 0.5초 ON | reference | 34.975339 | 4.871416 |
| 0.5초 ON | x −0.0025 rad | 35.265762 | 4.942168 |
| 0.5초 ON | y +0.005 rad | 33.889111 | 4.696079 |
| 0.5초 ON | z +0.005 rad | 35.669838 | 5.012532 |
| 1.0초 ON | reference | 76.099207 | 14.183879 |
| 1.0초 ON | y +0.005 rad | 118.323471 | 29.067896 |

y +0.005 rad만 0.5초에서 두 오차가 모두 기준보다 낮았다. 1초에는 두 값 모두 기준보다 커졌다. x/z 후보는 1초에서 검사하지 않았으며 OFF 조건도 새로 실행하지 않았다. 새 팔꿈치 후보는 채택하지 않고 기존 fine c02 진단 자세를 계속 기준으로 둔다. 이 비교만으로 안정 연주, task feedback 또는 학습 성능을 인증하지 않는다.

## 접촉과 보정 한계

LH/어깨 contact 행은 모두 0이다. 1초 reference ON의 RH thumb3 행은 step 84–160, y +0.005 ON은 step 82–143에 관측됐다. 첫·마지막 시점만으로 연속 접촉을 뜻하지 않으며 접촉 행은 지지력, 원인, 관통 깊이가 아니다. 두 1초 ON run에서 기존 PI 보정은 각각 212개 physics sample에서 포화됐다.

그림은 위쪽에서 0.5초 네 ON trace를, 아래쪽에서 1초 reference/y+0.005 ON trace를 별도 시간축으로 보여준다. manifest는 비교 JSON에 선언된 source/input 146개 SHA를 plot 전에 재검증하고 plotter와 PNG 해시를 기록한다.

![오른팔 elbow 초기각 0.5초 네 조건 및 1초 비교 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_retention_v1/artifacts/right_elbow_retention_v1.png)

재생성:

```bash
PYTHONPATH=/home/ajou/yigyu/3 MPLCONFIGDIR=/tmp/right_elbow_retention_v1_mpl MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_arm_initial_trials \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_retention_v1 \
  --out-dir /tmp/right_elbow_retention_v1_reproduction
```

