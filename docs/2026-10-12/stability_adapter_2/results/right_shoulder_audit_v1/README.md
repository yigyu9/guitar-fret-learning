# 오른어깨 source-query audit와 저장 contact 정렬

작성일: 2026-10-06. `audit_v2.json`의 source-shape query 100개와 `contact_alignment.json`의 관측 contact 두 행을 정리했다. 추가 native 실행은 하지 않았다. 초기 reference와 candidate_01 비교에는 기존 `right_support_v1/short/` 저장 결과만 사용했다.

## 저장 상태의 오른어깨 거리

| run | physics step / time (s) | R_Shoulder–G:body unsigned source hull (mm) |
|:---|---:|---:|
| reference | 0 / 0.000000 | 35.395 |
| reference | 2 / 0.008333 | 30.636 |
| reference | 3 / 0.012500 | 31.520 |
| reference | 4 / 0.016667 | 31.805 |
| reference | 24 / 0.100000 | 38.019 |
| candidate_01 | 0 / 0.000000 | 0.787 |
| candidate_01 | 2 / 0.008333 | 0.000 (source query ≈ 5.56e−8 mm) |
| candidate_01 | 3 / 0.012500 | 0.590 |
| candidate_01 | 4 / 0.016667 | 0.689 |
| candidate_01 | 24 / 0.100000 | 12.525 |

초기 RH:palm–G:body unsigned source hull 거리는 reference/candidate에서 100.306/3.230 mm였다. 왼손 조건은 바뀌지 않았다. 따라서 candidate는 source-shape proxy 기준으로 오른손바닥과 어깨가 모두 기타에 가까운 상태에서 시작하지만, 이는 접촉이나 지지를 입증하지 않는다. 각 run의 audit 50행은 저장 상태 5개와 body pair query 10개를 다루며, 전체 100행이다. `audit_v2.json`의 네 검사는 모두 true다. 보존된 `audit.json`은 이전 80행 스냅샷이며 원본 script는 `source_v1/`에 남아 있다.

## Native contact 행과 source-gap 정렬

| native contact step | time (s) | raw native `initialOverlap` (mm) | source signed gap at prior saved step (mm) | source signed gap at same-numbered saved step (mm) |
|---:|---:|---:|---:|---:|
| 3 | 0.012500 | −4.092317 | −4.092297 (step 2; difference 2.04e−8 m) | +0.150602 (step 3) |
| 4 | 0.016667 | +0.150595 | +0.150602 (step 3; difference 6.71e−9 m) | +0.222301 (step 4) |

관측된 contact 행은 이 두 개뿐이다. 값은 같은 번호의 저장 상태가 아니라 직전 저장 source 상태와 가까이 일치한다. `initialOverlap`은 native contact의 raw field이고 source signed gap은 별도 source-query 측정값이다. 이 비교만으로 모든 solver 단계나 cooked shape의 일치, 또는 일반적인 관통 깊이를 확정할 수 없다.

## 그림 26. 다섯 저장 시점 및 두 contact row의 source/native 측정

![오른어깨 source unsigned distance와 두 contact row의 signed measurements](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_shoulder_audit_v1/images/right_shoulder_audit_samples.png)

위 곡선은 discrete saved state 다섯 개만 연결하며 연속 관측 데이터가 아니다. 아래 그래프는 두 contact step의 raw native field와 이전/같은 번호 source-query 값을 각각 구분해 보여준다.

## 그림 27. 두 시작 자세의 오른어깨·오른손 source geometry

![reference와 candidate 시작 pose의 오른어깨 및 RH palm witness와 source shapes](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_shoulder_audit_v1/images/right_shoulder_audit_initial_geometry.png)

파랑은 기타 body/neck source shape, 주황은 오른어깨, 초록은 오른손바닥, 회색은 가까운 오른팔 source shape다. 두 패널은 같은 범위와 시점을 사용한다. 저장된 초기 pose의 source collision geometry를 CPU에서 재구성한 그림으로, Isaac/PhysX native renderer 출력이나 clearance 인증이 아니다.

## 범위와 재현

`audit_v2.json`의 query 100개는 기록된 source geometry에 대한 정적 측정이다. step 3/4의 관측 수치만으로 hard gate나 새 controller를 추가하지 않았다. 다음 방향은 손 근접도와 어깨/상완을 함께 관측하는 초기각 진단이다. palm-position feedback 적용은 별도 승인 대기 중이다.

재생성 명령은 기존 저장 pose와 query JSON만 읽으며 새 native physics를 실행하지 않는다. output 경로에 그림과 기본 `plot_manifest.json`을 생성하고 기존 출력 파일은 덮어쓰지 않는다.

```bash
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
MUJOCO_GL=disable MPLCONFIGDIR=/tmp/right_shoulder_audit_mpl MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_right_shoulder_audit \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_shoulder_audit_v1 \
  --out-dir /tmp/right_shoulder_audit_reproduction
```

[Plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_shoulder_audit_v1/plot_manifest.json)는 audit/contact/run JSON 입력, plotting·replay helper, 현재 config, human/guitar XML, XML에서 참조하는 mesh 37개 및 출력 PNG의 SHA-256을 기록한다. plotter는 실험 입력 파일을 수정하지 않는다.
