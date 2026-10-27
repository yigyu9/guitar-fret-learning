# StabilityAdapter 2 이미지·영상·설명 누적 결과

작성일: 2026-10-06 (Asia/Seoul). 디렉토리 날짜 `2026-10-12`는 사용자가 지정한 저장 위치다.
이 문서는 작업 결과를 단계별로 추가하는 기록이다. 메인 계획·구현은
[PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1)과 `stability_adapter_2/`에 둔다.

## 기록 방법

작업 단위가 끝날 때마다 이 문서 아래에 **실행일·단계·run ID·목적·조건·이미지/영상과 설명·
수치·판정·미검증 항목·다음 검토**를 추가한다. 이전 단계와 실패 결과를 보존한다.
이미지는 `images/<run_ID>_<내용>.png`, 영상은 `videos/<run_ID>_<내용>.mp4`처럼 run ID가 드러나는 이름으로 저장한다.
실제 장면 캡처에는 시점·카메라·부위·관통/접촉을, 측정 그래프에는 출처·단위·기록 주기와
해석 한계를 설명한다. 없는 장면 캡처를 측정 그래프로 대체했다고 보고하지 않는다.
이미지로 담기 어려운 움직임·접촉 변화는 영상으로 저장해도 된다. 영상은 문서에 절대 경로와 설명,
시뮬레이션 구간·카메라·재생 속도(정속/슬로모션)를 함께 적고 가능한 경우 대표 프레임도 첨부한다.

## 01. P1a CPU 환경 초기화·제어 연결

실행일: 2026-10-06. Run ID: `initial_environment_v3`.
이번 문서 추가는 기존 결과의 시각화이며 새로운 물리 실험을 실행하지 않았다.
현재 3개 이미지는 저장된 측정값의 그래프다. 사람·기타·양손 초기 배치의 실제 렌더는 아직 없다.

### 목적과 실행 조건

사람 root/Pelvis를 고정하고 공용 초기 위치·회전의 기타를 자유 상태로 두었을 때,
초기 상태·관절 목표 연결·원본 경로 스트랩이 실제 CPU 물리에 연결되는지 확인한다.
이 시험은 자세 안정화 제어기의 성능 시험이 아니다.

| 항목 | 이번 조건 |
|---|---|
| 기타 | 자유 root, 중력 ON, 공용 질량 4.648716kg, 초기 p/q가 불변 목표 |
| 양손 배치 | 공용 좌식 H0, 추가 지지 배치 최적화 없음 |
| 주요 제어 범위 | 양쪽 Thorax부터 손가락까지 66관절 |
| 몸통 | Torso·Spine·Chest 9관절 초기 PD 목표 유지; 작은 목표 보정 없음 |
| 다른 관절 | 하체·Head/Neck 초기 PD 목표 유지 |
| 관절 제어 | CPU native POS solver PD, 공용 kp/kd/effort cap; 공용 tensor hybrid PD와 다른 수치 조건 |
| 스트랩 | 원본 버튼·11개 guide·장력 수식, S0 rest length 1.089185175m 고정 |
| 주기·구간 | 물리 240Hz, 상태 기록 60Hz, t=0~0.1초의 7개 sample |
| 제외된 기능 | 기타/손 강제 부착, step 중 pose 덮어쓰기, 동적 길이 조절, 기타 오차 feedback, 학습 |

### 그림 1. 초기 목표 대비 기타 위치·회전 오차

![v3 측정 그래프: 기타 위치 및 회전 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/images/initial_environment_v3_guitar_error.png)

왼쪽은 기타 body-origin 위치의 목표 대비 거리(mm), 오른쪽은 정규화 quaternion의
목표 대비 회전각(°)이다. 위치 오차는 COM 이동량과 다르다. 점은 저장된 sample이고,
점 사이 선은 그 sample을 연결한 것으로 240Hz의 모든 중간 상태를 나타내지 않는다.

0.0333초→0.05초 사이에 위치 오차가 **5.943mm→60.272mm**, 회전 오차가
**0.490°→6.319°**로 증가했다. 마지막 0.1초에서는 **65.315mm·7.318°**다.
초기 목표 유지 성공으로 판단할 수 없다. 이 급격한 변화의 원인이 초기 관통·접촉 반발인지,
관절 제어와 지지 조건의 상호작용인지 현재 trace만으로 확정하지 않는다.
다음 검토에서는 초기 접촉 장면과 이 구간의 더 촘촘한 물리 상태를 확인한다.

### 그림 2. 몸통 기준 목표 유지 중 실제 관절 변화

![v3 측정 그래프: Torso Spine Chest 실제 관절 변화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/images/initial_environment_v3_torso_drift.png)

위에서부터 Torso·Spine·Chest의 x/y/z 관절각 변화이며, 각 값은 초기 관절각에서
얼마나 움직였는지를 도(°)로 표시한다. 세 패널의 세로축 범위가 서로 다르므로
선의 화면상 높이가 아니라 축 숫자로 비교한다. x/y/z는 모델의 관절 이름이며
몸통의 world Euler angle을 뜻하지 않는다.

PD 목표각은 초기값을 유지했지만 실제 관절은 움직였다. 마지막 sample에서
**Spine_y=-1.093°**로 9관절 중 절대 변화가 가장 컸다. 같은 시점의 Torso 최대 변화는
0.385°, Chest 최대 변화는 0.433°다. 이는 root 고정과 몸통 목표 유지가 몸통 전체를
물리적으로 잠그는 것과 다름을 보여준다. 사용자가 정한 최소 움직임의 수치 허용 범위는
아직 합의하지 않았으므로 몸통 유지 gate 통과로 표시하지 않는다.
작은 몸통 목표 보정은 초기 장면 검토 후 범위를 정한다.

### 그림 3. 스트랩 경로 길이·마지막 적용 장력

![v3 측정 그래프: 스트랩 경로 길이와 마지막 적용 장력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/images/initial_environment_v3_strap.png)

왼쪽 파란 선은 기타 버튼과 몸통 guide를 잇는 전체 경로 길이 L(m), 빨간 점선은
고정한 rest length다. 오른쪽은 각 기록 시점의 마지막 물리 tick에 적용했던 장력(N)이다.
버튼 사이 직선 거리나 상용 스트랩 길이 표기가 아니다.

0.1초의 경로 길이는 **1.035838m**로 rest length보다 **53.347mm 짧다**.
이 시점에는 tension-only 스트랩이 느슨하며 마지막 적용 장력도 0N이다.
단, 0.05초의 저장된 경로 길이는 **1.089816m**로 rest length를 약 **0.631mm 초과**한다.
따라서 전 구간이 항상 slack이었다고 설명하지 않는다.

현재 L은 물리 step **후** snapshot이고, 마지막 적용 장력은 마지막 step **전** 상태로
계산한 값이다. 이 시점 차이와 60Hz 기록 때문에 L이 rest length를 넘는 sample에서
저장된 마지막 장력이 0N일 수 있다. 저장된 7개 장력은 모두 0N이지만 중간 240Hz tick의
장력까지 항상 0N이었다고 단정하지 않는다. 장력·길이의 정밀 비교에는 동일 시점의
L/Ldot/T와 매 물리 tick 기록이 추가로 필요하다.

### 수치와 검증 판정

| 지표 | 첫 자유 step 전 | 0.1초 뒤 |
|---|---:|---:|
| 기타 목표 대비 위치 오차 | 0.000028mm | 65.315mm |
| 기타 목표 대비 회전 오차 | 0.0000145° | 7.318° |
| 기타 COM 선속도 | 0m/s | 1.594m/s |
| 기타 각속도 | 0rad/s | 3.657rad/s |
| 몸통 9관절 최대 절대 변화 | 0° | 1.093° |

초기화 검사 16개·단위/native 테스트 6개가 통과했고, 별도 change-reviewer가
CPU 초기화·제어 계약 범위에서 Critical/Warning/Suggestion 없음을 확인했다.
팔꿈치 목표 변경이 실제 q 응답을 바꾸는 것과 COM 기준 경로점 속도를 검증했다.
**자유 기타의 정지 안정성은 미달성**이다. 0.1초 구간만으로 10초 유지나 연주 호환을 판단하지 않는다.

이전 실패 이력도 보존한다. v1은 native 준비 단계에서 기타가 이동하여 초기화 검사에 실패했다.
v2는 별도 토크가 native POS 모드에서 무시되었으므로 작은 오차(9.438mm·0.485°)를
제어 성능 비교에 사용하지 않는다. v3는 native solver PD와 COM 기준 속도를 적용한 결과다.

### 출처·재생성·남은 검토

원본은 [report.json](results/initial_environment_v3/report.json),
[trace.json](results/initial_environment_v3/trace.json),
[run.log](results/initial_environment_v3/run.log),
[tests.log](results/initial_environment_v3/tests.log),
[물리 구현 검수](results/initial_environment_v3/review.md)에 보존한다.
그래프 생성 구현은 [plot_initialization.py](/home/ajou/yigyu/3/stability_adapter_2/plot_initialization.py:13)다.
PNG를 다시 만들 때는 기존 이미지를 보존하도록 새 출력 디렉토리를 지정한다.

```bash
MPLCONFIGDIR=/tmp/stability_adapter_2_matplotlib \
/home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_initialization \
  --run /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_environment_v3 \
  --images-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/images/새_출력_ID
```

현재 NVIDIA 드라이버 통신 실패로 GPU/렌더는 미검증이다. 초기 관통·접촉 품질·실제 토크와
포화·10초 정지 유지·작은 손/팔 움직임·연주 호환·학습 성능도 아직 확인하지 않았다.
다음 기록에는 실제 초기 배치 이미지와 손/전완·넥·몸통 접촉 설명을 추가한다.
그 검토 뒤 양손 지지 후보·초기 스트랩 길이·몸통 보정 범위를 정한다.

이번 문서와 이미지 검증: 생성 스크립트 문법 검사·문서 링크·PNG 디코딩·원본 수치 대조를
통과했다. 3개 이미지를 직접 열어 한글·축·범례·잘림 여부를 확인했다.
별도 change-reviewer도 이미지와 trace를 대조했고 Critical/Warning/Suggestion 없음으로 검수했다.
기존 v3 코드 source hash와 기존 실험 보호 대상 87개 파일은 변경되지 않았다.

## 핵심 목표 재확인 — 2026-10-06

사용자가 강조한 중심 작업은 **humanoid 초기 자세와 strap 초기 설정을 함께 바꿔 시작 직후
기타 변화를 줄이고, 이후 제어로 원래 기타 p/q에서 벗어난 오차를 보정·유지하는 것**이다.
v3는 H0·S0 진단 기준선이며 이 두 목표를 달성한 결과가 아니다. 이번 확인에서는
계획과 기록만 갱신했고 새 물리 실험·이미지·영상은 추가하지 않았다.

다음 결과는 H0/H1 자세와 초기 길이의 개별·조합 효과를 먼저 보여준다.
개별 효과 비교에는 H0에서 정한 같은 기준/선택 절대 rest length를 H0/H1에 적용하고,
H1 경로 길이·초기 장력은 결과로 측정한다. 자세마다 rest length를 자동 재설정하지 않는다.
원본 스트랩 경로·수식, root 고정, 첫 몸통 목표 유지와 동일 기타 p/q를 유지한다.
선정한 초기 조건에서 feedback OFF/ON을 비교하여 초기 배치 개선과 능동 보정 효과를
구별해 기록한다. 초기 속도·gain도 같게 두고 첫 구간과 전체 구간의 위치·회전 오차를 함께 평가한다.

## 최소 자세 제약 제안 — 2026-10-06

사용자가 잘못된 자세를 막기 위한 최소 제약을 요청했다.
[제안 문서](/home/ajou/yigyu/3/stability_adapter_2/POSTURE_CONSTRAINTS.md:9)에 관절 한계·
왼손 손바닥 방향·비정상 관통/교차 금지와 손목/팔꿈치·연주 공간 선호를 정리했다.
왼손 손바닥은 해부학적 법선의 world +Z 성분으로 평가하는 후보를 제안했으며,
사용자는 초기 후보의 **위쪽 반구 필수 + +Z에 가까운 방향의 부드러운 선호**를 선택했다.
선호 가중치와 실제 움직임 중 위반 기준은 초기 배치·움직임 검토 후 정한다.
이번 단계는 문서 제안과 소스 확인이다. 새 제약 적용·물리 실험·이미지·영상은 없으며,
제약을 만족하는 H1 자세나 개선된 기타 유지 성능이 검증된 것으로 표시하지 않는다.

## 02. 2026-08-19 손 관절 제한·분포 자료 검토

검토일: 2026-10-06. 목적은 기존 손 관절 자료를 초기 humanoid 자세와 최소 자세 제약에
활용할 수 있는지 확인하는 것이다. 새 물리 실험·분포 재계산은 하지 않았다.
원본 디렉토리는 보존하고 아래 이미지 3장은 결과 디렉토리에 바이트가 같은 사본으로 저장했다.

### 자료 범위와 결론

손가락 분포는 **왼손 초기 자세 후보와 부드러운 선호를 정하는 데 유용**하다.
다만 분포 범위를 곧바로 새로운 hard limit으로 적용하지 않는다. 연주 중 압현과
초기 준비·기타 지지·손가락 개폐에 필요한 자세가 서로 다를 수 있기 때문이다.

| 자료 | 확인한 내용 | 이번 활용 |
|---|---|---|
| 손가락 분포 이미지 2장 | 왼손 21개 DOF, XML range·p01~p99·p05~p95·median | 자연스러운 후보/선호와 과도한 굽힘·벌림 진단 참고 |
| 정리.txt | 관측 범위와 신규 hard limit 후보, 전문 연주자 1명이라는 기록 | 후보 출처로 보존; 실제 적용값으로 확정하지 않음 |
| fret_joint_limits JSON/CSV·렌더 | L_Thorax·어깨·팔꿈치·손목 각각 3개와 손가락 21개, 총 33개 | 모델 한계·렌더 목표/실제값 비교; 실제 연주 분포로 해석하지 않음 |
| 현재 model XML 대조 | 위 33개 하한/상한 모두 0.001° 허용 오차에서 일치 | 이름과 hard range의 현재 모델 호환 확인 |

분포 그림에 대응하는 수치 JSON 두 개는 해당 디렉토리에 없었다. 정리.txt에는 수치 일부가
있지만 `LH:pinky2` 신규 한계 칸의 비수치 `f` 등 미완성 항목도 있다. 이미지를 픽셀로 읽어
정확한 quantile 값을 만든 것으로 보고하지 않는다. 전체 마커 파일 수·frame 통계도 이번에 재계산하지 않았다.

### 그림 4. Fitted 손가락 모션 분포

![과거 fitted 모션의 왼손 손가락 분포 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/images/historical_20260819_finger_fitted.png)

원본은 `docs/2026-08-19/실제 관절 제한과 분포.png`다. 회색은 XML hard range,
옅은 파랑은 p01~p99, 진한 파랑은 p05~p95, 주황 점은 median이며 단위는 degree다.
그래프는 각 관절의 주변 분포이며 관절 간 결합이나 손바닥 방향·접촉을 나타내지 않는다.

현재 [fitted 분석 소스](/home/ajou/yigyu/3/tab2body/tools/analyze_fret_isaac_finger_distributions.py:16)는
기본 입력으로 `scale.json`을 사용하며 짧은 scale 모션의 분포라고 설명한다.
그림 제목·범례는 이 소스와 일치하지만 원본 그림의 정확한 과거 실행 인자는 기록에서 확인하지 못했다.
자주 쓰는 손가락 각도를 찾는 참고가 되며, 정리.txt에서 제안한 좁은 한계를 적용하기 전에는
초기 지지·손가락 개폐와 native DOF 좌표 변환을 검증해야 한다.

### 그림 5. 전체 raw 마커 자료에서 추정한 손가락 분포

![과거 전체 raw 자료 기반 왼손 손가락 분포 추정 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/images/historical_20260819_finger_estimated.png)

원본은 `docs/2026-08-19/전체 분포.png`다. 범례에 **estimated**가 붙어 있으며,
같은 모양의 범위도 직접 측정한 native DOF 분포로 간주하지 않는다.
현재 [추정 소스](/home/ajou/yigyu/3/tab2body/tools/estimate_full_guitar_isaac_finger_distributions.py:1)는
마커 특징을 scale 모션의 fitted 분포에 quantile mapping하는 방법을 설명한다.
정확한 IK 재현이 아니고, PIP/DIP는 같은 특징을 공유하며 엄지·벌림 각도는 신뢰가 낮다고 명시한다.
추정 결과를 XML 한계에 clip하므로 끝각도에 모인 범위 자체가 실제 관측 관절 한계라는 뜻도 아니다.

그림 4와 5의 범위가 다른 것은 입력 모션 범위와 추정 방법의 차이를 검토할 이유다.
더 넓거나 좁은 쪽을 자동으로 정답으로 채택하지 않는다. 분포가 충분한 신뢰를 갖는 부분부터
부드러운 선호로 참고하고, 엄지 지지에 필요한 동작은 별도의 물리 검증을 우선한다.

### 그림 6. 왼쪽 손목의 모델 관절 한계 렌더

![과거 왼쪽 손목의 개별 모델 한계 렌더 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/images/historical_20260819_left_wrist_limits.png)

원본은 `fret_joint_limits/overview/wrist_joint_limits.png`다. L_Wrist_x/y/z에 각각
하한·초기값·상한 목표를 보낸 두 카메라 방향의 과거 렌더이며, JSON은 다른 관절을 고정하고
기타를 장면 밖으로 이동했다고 기록한다. 실제 자유 기타 지지 장면이나 손목 연주 분포가 아니다.
손목 범위는 x=-180~90°, y=-45~45°, z=-90~90°로 모델 범위가 넓다는 것을 확인할 수 있다.
좋은 지지 자세는 이 범위 안에서도 손바닥 방향·접촉·연주 공간을 함께 만족해야 한다.
같은 디렉토리에 어깨·팔꿈치·Thorax의 개별 한계 렌더도 있다.

다만 JSON의 **L_Wrist_x 하한 목표 -180°가 rendered +90.010°**로 기록되어 있으며,
L_Elbow_x도 하한 목표 -180°에 rendered +99.186°, 상한 목표 +180°에 rendered -85.655°다.
따라서 이 두 관절의 극한 이미지를 정확히 재현된 끝각도 자세의 증거로 사용하지 않는다.
기록의 불일치 원인과 올바른 native 끝각도 동작은 별도로 확인해야 한다.

### 활용 순서와 미검증 범위

모델 hard range를 기본 한계로 유지하면서, 손가락 분포는 검증 후 초기 후보/soft 선호에 참고한다.
가능한 경우 관절 간 결합이 남아 있는 전체 손 frame을 사용하고, 각 관절의 median이나
범위 내 각도를 독립적으로 섞었다고 정상 자세로 판단하지 않는다.
왼손 손바닥 위쪽 반구 조건·비정상 관통·접촉·운지/타현 공간과 함께 검토한다.
어깨·팔꿈치·손목은 empirical 분포가 확인되지 않았으므로 현재 모델 한계와 넓은 자세 선호부터 적용을 검토한다.

오른손 분포, 연주자 간 다양성, 자유 기타 지지 자세의 분포, 정확한 native hinge 변환과
새 hard limit의 유지·연주 호환 효과는 미검증이다. 왼손 범위를 오른손에 그대로 복사하지 않는다.
기존 33관절 자료가 현재 66관절 제어 범위를 제한하지 않는다.

증거: [자료 검토 JSON](analysis/historical_20260819_review.json).
원본 49개 파일은 hash로 보존 여부를 확인한다. 이미지 사본의 source/copy 경로와 SHA-256,
현재 XML range 비교 및 수치 분포 파일의 확인 여부를 JSON에 기록했다.
이 검토에서는 model XML·runtime 제약·정책·공용 소스를 수정하지 않았다.
검증: 원본 49개 파일 hash 보존, PNG 사본 3개 일치·직접 확인, 33개 한계·문서 링크 검사 통과.
별도 change-reviewer도 수치·자료 구분·이미지를 확인했고 Critical/Warning/Suggestion 없음으로 검수했다.

## 03. 첫 물리 step 전 전신–기타 겹침 진단

2026-10-06, run `initial_overlap_v2`. 관절각/스트랩 초기 설정을 자주 변경하는 실험의
첫 검사 도구다. 기존 공용 H0/S0를 그대로 생성하고, prepare 후 초기 상태를 복원한 native
world body pose에서 원본 XML 충돌 형상을 검사했다. query는 CPU MuJoCo 3.2.3으로 수행하며
MuJoCo dynamics와 추가 native physics step을 실행하지 않았다. run별 초기값 입력과 자동 reset은 다음 단위다.

### 그림 7. 초기 전신·기타 충돌 형상과 겹침 후보

![첫 물리 스텝 전 전신과 기타의 원본 충돌 형상 CPU 진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/images/initial_overlap_v2_geometry.png)

왼쪽은 전신, 오른쪽은 기타 주변을 다른 방향에서 본 그림이다. 빨간색은 음수 query 값이
나온 R_Hip와 G:body **전체 형상**이며 실제 관통 영역이나 관통 깊이의 색상 지도는 아니다.
파란색은 나머지 기타 형상, 회색은 나머지 사람 형상이다. R_Hip는 오른쪽 허벅지 링크다.
축은 world 좌표의 m 단위다. 원본 충돌 mesh의 convex hull·box·capsule을 native world pose에
배치한 진단 그림으로, 실제 Isaac Gym 시각 렌더·접촉 힘·PhysX cooked mesh 캡처가 아니다.
chair/ground·strap 천은 그림과 쌍 검사 범위에 포함하지 않았다.

### 결과와 해석

| 항목 | 결과 |
|---|---|
| 활성 형상 | humanoid 54개, 기타 26개; 양손·몸통·다리·발 포함 |
| 전체 쌍 query | 1,404쌍; 각 쌍은 20mm 이내 검색 |
| native 형상 수 대조 | 총 55/28개에서 비활성 proxy 제외, 부위별 활성 수 일치 |
| 음수 후보 | R_Hip–G:body 1쌍, backend signed gap -1.331mm |
| 다른 근접 쌍 | R_Elbow–G:body, backend signed gap +7.154mm |
| 검사로 인한 상태 변경 | 없음; native 관절·몸체 상태 정확히 동일 |
| 추가 native physics step | 0 |

현재 H0는 **무관통 초기 상태로 확인되지 않았다**. 첫 step에서 기타가 튀거나 이동할 경우
이 후보를 초기 장력·손 지지와 함께 조사한다. 이번 검사만으로 이전 0.1초 drift의 원인으로
확정하거나 허벅지 각도를 자동 변경하지 않는다. 기타 초기 목표 p/q는 변경하지 않았다.

음수의 크기는 물리 관통 깊이로 보정되지 않았다. 합성 상자에서 실제 관통 100mm에
backend 값 -50mm가 나왔으므로 -1.331mm를 실측 관통 깊이로 인용하지 않는다.
분리 10mm·접촉 0·관통 부호·검색 범위 밖 제외를 확인했고, 이 의미를 JSON에도 기록했다.
PhysX cooked mesh·접촉 skin과 대조 전이므로 양수 결과도 실제 무관통 보증은 아니다.
20mm 밖의 쌍은 정확한 최단 거리 대신 검색 범위 밖이다. 1e-7m는 수치적 부호 분류 기준이며
허용 관통 깊이/접촉 허용치는 아니다. 정상 지지 접촉을 금지하는 기준도 정하지 않았다.

### 검증·실패 기록과 다음 단계

새 합성 검사 1개(4상황)와 기존 물리/제어 계약 6개, 문법 검사가 통과했다.
로그의 native visual-geom 경고는 기존 CPU 환경 경고이며 실제 렌더는 여전히 미검증이다.
v1은 query 크기를 정확한 관통 깊이로 가정한 검사와 MuJoCo 선행 import에 실패했다.
v1 원본 로그·그림·JSON은 보존하고, Gym 선행 import와 query 의미를 명시한 v2를 기준으로 삼는다.

증거: [v2 report](results/initial_overlap_v2/report.json), [실행 로그](results/initial_overlap_v2/run.log),
[7개 검사 로그](results/initial_overlap_v2/tests.log), [v1 실패 로그](results/initial_overlap_v1/tests.log).
그림은 v2의 `geometry.png`와 동일한 바이트 사본이다.

다음 흐름은 run별 관절 초기각/절대 rest length 입력 → 초기 geometry·손바닥·관절 한계 검사 →
자유 기타 rollout → 초기 p/q 오차·속도·접촉 기록 → 보정 또는 trial 종료 → 새 설정 trial이다.
runtime 감시·허용 거리·제어/종료 기준은 초기 장면과 PhysX 대조를 검토한 뒤 정한다.
실행 중 pose 덮어쓰기를 feedback 보정으로 사용하지 않는다.

별도 change-reviewer는 7개 검사를 직접 실행하고 초기 query를 독립 재현했다.
수치·native 상태 불변·source hash·이미지·설명·명령을 확인했고 CPU 정적 보조 진단 범위에서
Critical/Warning/Suggestion 없음으로 판정했다. [검수 기록](results/initial_overlap_v2/review.md)과
[보존·문서 검증 기록](results/initial_overlap_v2/validation.json)을 함께 보존한다.

## 04. 기울어진 넥과 왼손의 대응 단면 시각화

2026-10-06, run `neck_palm_visual_v2`. 사용자가 요청한 국소 높이 비교를 현재 native
시뮬레이션 초기 상태 H0/S0에 표시했다. 자세·기타 목표·controller·제약을 변경하지 않았으며,
추가 physics step 0과 native 관절/몸체 상태 불변을 확인했다. GPU renderer가 사용 불가하므로
native world pose에 원본 충돌 형상을 배치한 CPU 그림이다. 실제 Isaac Gym 렌더는 아니다.

### 그림 8. 실제 초기 배치와 대응 지점의 높이 차

![현재 초기 시뮬레이션 배치의 손바닥 중심과 대응 넥 단면 표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/images/neck_palm_visual_v2_native.png)

왼쪽: 녹색 P는 LH:palm 원본 충돌 convex hull의 **부피 중심**이며 손목 origin·손끝·표면
접촉점과 다르다. 보라색 선은 넥 길이 방향 기준선, Q는 P를 그 선에 직교 투영한 대응 지점이다.
P–Q 점선은 3D 투영 관계다. 표시는 형상에 가려지지 않도록 위에 겹쳐 그렸다.
파란색은 기타, 녹색 형상은 왼손 palm, 나머지 사람/손가락은 회색이다.
표시 중심점은 이번 진단용 기준이며 해부학적 손바닥 중심의 최종 정의는 검토 후 정한다.

오른쪽: 가로축은 넥 길이 좌표 s, 세로축은 world Z다. P를 투영한 s*에서만 높이를 비교한다.
파란 띠는 그 길이 위치의 원본 neck convex-hull 단면 전체가 갖는 world Z 하단~상단 범위다.
주황색 세로선은 대응 단면, 녹색 점선은 실제 palm 중심 높이, 화살표는 중심선 대비 높이 차다.
넥 표면 최단 거리나 3D 접촉 간격을 나타내는 그림은 아니다.

| 현재 H0 측정 항목 | 값 |
|---|---|
| palm 중심 world XYZ | (-0.201964, 0.061520, 0.696280)m |
| 대응 중심선 Q world XYZ | (-0.153267, 0.111226, 0.805629)m |
| 대응 길이 좌표 s* | 0.194184m, 전체 형상 길이 0.497136m 안쪽 |
| palm 중심 − 대응 중심선 world Z | -109.349mm |
| 대응 단면의 world Z 범위 | 0.774466~0.836877m |
| palm 중심 − 단면의 world Z 하단 | -78.186mm |
| palm 중심과 중심선의 3D 직교 거리 | 129.612mm |
| palm보다 단면 전체가 낮은 다른 구간 | 이번 161개 샘플에서는 0개 |

현재 palm은 대응 넥 아래에 있지만 중심선과 멀다. 높이 조건만으로 넥 지지·접촉·연주 준비
성공이라 판단하지 않는다. 초기 관통 검사에서 나온 R_Hip–G:body 후보도 그대로 남아 있다.
이번에는 높이 조건을 hard gate로 적용하거나 손을 이동/부착하지 않았다.

### 그림 9. 다른 넥 부분이 손바닥보다 낮아도 되는 경우 — 설명용

![같은 기타 형상에서 다른 구간의 높이를 제외하는 국소 비교 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/images/neck_palm_visual_v2_example.png)

기타 형상·기울기·높이 띠는 그림 8과 같은 실제 H0다. 주황색 P′만 설명용 가상점이다.
P′는 s=0.347995m에서 대응 단면 하단보다 world Z 기준 10mm 아래로 정했다.
가상점의 world Z=0.818105m, 그 단면 하단 Z=0.828105m다.
가상점은 중심선에 투영했을 때 같은 s를 갖도록 구성했다. humanoid 관절을 변경하거나
그 위치에 손을 옮긴 물리 실험이 아니다. **10mm는 설명을 위한 값이며 채택된 목표 간격이나 허용치가 아니다.**

회색으로 강조한 몸체 쪽 구간은 P′보다 낮지만, 손과 대응되는 단면이 아니므로 이 국소
높이 조건의 위반으로 세지 않는다. 높이만의 설명이며 관통·손바닥 방향·횡방향 거리·운지
영역 같은 다른 조건을 면제하지 않는다. 이 가상점이 실제 관절 자세로 가능하고 넥을 지지하는지도 미검증이다.

### 기준 정의·검증과 남은 결정

기준선은 source neck1/neck2 두 mesh의 guitar-local x/z 범위 중점에서 local Y를 따라 만든
직선이다. **헤드 부분도 포함한 형상 길이**이며 전체 길이가 운지 가능한 범위라는 뜻은 아니다.
최종 운지 범위와 넥만의 작업 구간은 별도로 정한다. 각 단면은 local Y=s의 평면과
원본 convex-hull edge의 교점을 world로 변환해 구했다. 기타 local Z를 world 위쪽으로 간주하지 않는다.
투영이 길이 범위 밖이면 검토 불가로 기록하며 끝점으로 clamp하여 정상 판정하지 않는다.

문법 검사, 실행, native 상태 보존, 투영 직교성, 단면 범위 및 source hash를 확인했다.
단순 box의 4개 단면 범위와 범위 밖 오류도 확인했다. v1 그림은 표시점이 형상에 가려진
첫 출력이며 보존한다. v2에서 표시점 가시성과 별도 설명용 그림을 추가했다.

증거: [실제 좌표·조건 JSON](results/neck_palm_visual_v2/report.json),
[실행 로그](results/neck_palm_visual_v2/run.log). 두 이미지는 run 원본 PNG의 바이트 사본이다.
현재 기준점/기준선은 시각 진단용이다. 실제 지지 자세의 표면 거리, 관절각 후보와 초기 높이
조건의 필수/선호 구분, 실행 중 허용 범위는 이 그림을 검토한 뒤 결정한다.

별도 change-reviewer는 출력 파일을 저장하지 않고 단면 계산과 native 좌표를 독립 재현했다.
높이 차·직교 거리·투영 직교성·상태 불변·추가 step 0·source hash와 이미지 두 장을 대조했다.
국소 높이 설명 시각화 범위에서 Critical/Warning/Suggestion 없음으로 판정했다.
기존 실험 87개 파일과 과거 자료 49개는 보존되었다.
[검수 기록](results/neck_palm_visual_v2/review.md), [검증 기록](results/neck_palm_visual_v2/validation.json).

## 05. 초기 설정 입력·batch 부분 재개 기능 진단

2026-10-06, `batch_contract_v1`. 초기 관절 절대각/절대 strap rest length를 입력하는 세 trial을 각각 CPU PhysX로 0.1초(24 physics steps) 실행했다. 이 단계는 설정 전달·초기 불변조건·고유 run 기록·batch 재개 계약의 기능 진단이다. 세 report 모두 `stability_success: null`이며 물리적 안정성 성공을 선언하지 않는다.

### 그림 10. 세 설정에서 측정한 기타 오차와 스트랩 길이

![세 batch trial의 기타 위치·회전 오차와 스트랩 길이 시계열](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/batch_contract_v1/batch_contract_comparison.png)

위치 오차의 단위는 mm, 회전 오차는 deg, 스트랩 길이는 m이며 가로축은 0.1초 구간의 시간(s)이다. 각 곡선은 checkpoint `completed`에 기록된 report와 trace를 읽어 그렸다. H0 +0.001m의 일곱 sample 기타 trajectory는 H0 baseline과 정확히 겹친다. 이 길이 변경을 개선 후보로 선정하지 않는다. 그림은 CPU PhysX rollout data plot이며 실제 장면 render가 아니다.

| Trial | 관절/절대 rest 길이 입력 | 최대 위치 오차 | 최대 회전 오차 |
|---|---|---:|---:|
| H0_LA | H0 / 1.0891851746440693m | 65.315253mm | 7.318146° |
| H0_RElbow_plus002_LA | R_Elbow_x −0.3378295232598935rad / 1.0891851746440693m | 65.330385mm | 7.315286° |
| H0_LA_plus001 | H0 / 1.0901851746440692m | 65.315253mm | 7.318146° |

H0의 기준 R_Elbow_x는 −0.35782952325989353rad이고, 두 번째 설정은 +0.02rad 변화다. 세 조건 모두 초기 기타 goal p/q, 속도 0, humanoid 고정 root, torso held target 유지 검사를 통과했다. H0의 모든 초기 query에는 R_Hip–G:body signed gap −1.331165mm가 있다. CPU source-shape query의 관통 후보이며 실제 penetration depth나 PhysX clearance 판정은 아니다. 손바닥 normal signed-dot z는 0.869692208이나 해부학 방향 부호는 시각 검증 전이다.

strap `last_applied_tension_n` 필드는 control sample마다 그 직전 physics substep에 적용한 값이다. 기록된 sample 값이 0이라고 하여 나머지를 포함한 24 physics steps 전체의 장력이 0이었다고 해석하지 않는다. GPU device는 사용할 수 없었고 visual geom 로드 오류가 로그에 남아 GPU renderer는 검증되지 않았다.

### 실행·재개 및 보존 확인

`--max-trials 1` partial 실행 후 resume로 세 trial을 완료했다. resume 검증은 첫 완료 report의 bytes와 mtime 불변, 전체 3 report의 현재 code hash 일치를 확인했다. 현재 CLI의 13개 검사가 통과했다. 보존 검사에서 기존 실험 87개와 2026-08-19 원본 자료 49개 모두 unchanged였고 parent가 닫힌 뒤 child가 batch lock을 유지하다 종료 때 lock을 해제함을 확인했다. 상세 표·실행 예시·원자료 경로는 [batch 결과 안내](results/batch_contract_v1/README.md)에 있다.

## 06. H0 native contact와 strap 장력 시계열 진단

2026-10-06, `physx_contact_v1/h0_detailed`. 저장된 240Hz CPU PhysX 24-step contact/state 자료를 분석했다. 실제 GPU/renderer 재생이나 별도 실험 실행은 하지 않았다. clearance, 자동 gate, 안정성 성공 및 contact 인과관계는 판정하지 않는다.

### 그림 11. 기타 드리프트·L_Hip 각도·raw contact signed field

![H0 240Hz 진단의 기타 위치/회전 오차, L_Hip 각도 변화, contact field marker](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/physx_contact_v1/images/physx_contact_v1_timeline.png)

그래프는 report/trace/states/contacts 원자료를 그린다. step 11 (0.0458333초)의 기타 오차 5.183mm/0.690°에서 step 12 (0.05초) 60.272mm/6.319°로 바뀐다. step 12에 `guitar/guitar × human/L_Knee` contact row 2개가 각각 raw `initialOverlap` −35.9199mm/−34.2896mm를 기록했다. `guitar/guitar`는 두 neck mesh를 가진 기타 root body로 별도 `G:body`와 구분되며, raw body label만으로 두 neck mesh를 개별 특정할 수 없다. contact timestamp는 completed-step 기준이며 `initialOverlap` 값은 그 step이 시작될 때의 값이다.

첫 contact sample step 1 (0.00416667초)의 `guitar/G:body × human/R_Hip` raw signed gap은 −1.33114mm였다. 같은 sample의 R_Ankle과 R_Toe ground contact는 약 −9.69mm와 −8.89mm다. 값은 raw native feature field다. `minDist`는 요청한 target distance로 clearance 측정이 아니며 `lambda` 단위도 교정되지 않았다.

### 그림 12. 기록 pose에서 source collision geometry 비교

![t=0과 step 11의 saved state에 배치한 humanoid와 기타 source collision geometry](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/physx_contact_v1/images/physx_contact_v1_source_geometry_t0_step11.png)

회색 humanoid와 파란 기타 geometry는 원본 충돌 형상이다. 빨간색과 ×는 saved pose에서 실행한 별도 source-shape query의 음수 pair 형상·witness점이다. t=0/step 11에서 음수 pair는 각각 1/9개다. 이 이미지는 원본 shape를 저장된 pose에 놓은 CPU 재구성이며 Isaac Gym 렌더나 PhysX contact image가 아니다.

strap의 적용 장력 최대값은 전 24 physics step에서 0N이었다. 그렇다고 contact 부재나 collision response 부재를 뜻하지 않는다. step 12 무릎 contact의 raw lambda는 0이지만 force/impulse 해석은 교정되지 않았다. 초기 왼쪽 엉덩이 target에서 step 11 actual 각도 편차는 x −60.09°, y +45.31°, z +45.01°였고 왼쪽 무릎 world Z는 초기 0.48980m에서 0.77163m로 변했다. 고정 humanoid root는 하체 관절/몸체 고정을 뜻하지 않는다. 이 동시 변화만으로 기타 drift의 원인을 확정하지 않는다.

별도 isolated analytic box calibration은 10mm 분리에서 contact 없음, 0.05mm 간격에서 양수 raw field contact, 접촉 0에서 0, 1mm overlap에서 약 −1mm raw field를 확인했다. 이는 box의 sign behavior만 확인하며 mesh별 침투 깊이 환산은 아니다. native API 초기 enum 실패 로그와 조건이 달랐던 default-substeps 교정 기록은 보존했고 H0 수치 해석에는 사용하지 않았다. test log에는 15개 검사가 통과한 것으로 기록됐다. [상세 결과·원자료 인덱스](results/physx_contact_v1/README.md).

별도 change-reviewer 검수는 그림까지 확인해 완료했다.

## 07. 하체 PD·solver 조합의 짧은 진단 비교

2026-10-06, `lower_body_pd_v1`. 공통 초기 상태와 절대 strap rest length에서 14개 조건을 각각 0.1초 실행한 CPU PhysX 요약 JSON을 시각화했다. 이미지의 첫 패널은 위치 오차 로그축, 다음은 회전 오차, 마지막 두 패널은 raw 하체 각도 편차와 native scalar-limit 위반이다.

### 그림 13. 하체 제어·solver 진단 결과

![14개 짧은 진단의 기타 오차와 하체 target 편차 및 scalar-limit 위반](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_pd_v1/images/lower_body_pd_v1_comparison.png)

`pgs`는 기타 오차 27.685mm/3.945°로 낮아졌지만 하체 raw target 편차 17.744°와 최대 scalar-limit 위반 2.754°가 남아 안정 후보로 선택하지 않았다. 최소 기타 위치 오차는 `solver16_leg_kd01`의 17.946mm지만 raw 하체 편차가 246.060°다. `pgs16`은 위치 오차 17.582m, 최종 속도 410.610m/s로 폭주했다. baseline은 65.315mm/7.318°이며 raw 하체 편차는 107.805°다. 각도편차는 wrapping하지 않은 actual−target 직접 차다. 모든 검사 flag가 true라는 것이 안정 성공을 의미하지 않는다.

분리된 humanoid-only, zero-gravity probe에서 baseline hold 편차 6.771702°와 drive-off 0.000389°를 기록했지만, 이는 원인 하나를 확정하거나 최종 환경을 정한 결과가 아니다. 이 그림은 JSON 요약을 그린 데이터 시각화이며 native renderer 출력이 아니다. 전체 14행과 제약·재생성 경로는 [하체 PD 진단 결과](results/lower_body_pd_v1/README.md)에 기록했다.

## 08. 기타 초기 Z 오프셋의 정적 source-shape preview

2026-10-06, `guitar_z_preview_v1`. 기타를 초기 world Z 방향으로 0/2/5/10/15mm 옮긴 정적 CPU source-shape query를 비교했다. 각 오프셋에서 human–guitar 형상쌍 1,404개를 확인했으며, 사람 관절 초기각/root와 기타 회전은 유지했다. native rollout이나 기타 목표 변경은 수행하지 않았다.

### 그림 14. 정적 형상 간격과 strap route 길이

![기타 Z 오프셋의 signed source-shape gap 및 route 길이 차이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_preview_v1/images/guitar_z_preview_v1_static.png)

Sol은 정적 형상 기준 다음 비교 후보로 +5mm를 권고했다. 해당 위치의 R_Hip/R_Elbow query gap은 3.30269/4.20840mm이고 route 길이는 1.083374161466m로, 공통 절대 rest length 1.0891851746440693m보다 5.811mm 짧다. +2mm의 hip gap은 0.52238mm이며 +15mm에서는 elbow gap −0.79598mm다. 기준 0mm query에는 음수 pair 1개, +5mm에는 0개였다. signed gap은 보정된 침투 깊이나 PhysX clearance가 아니며, 정적 route 길이만으로 strap 장력/자세/안정성을 판단하지 않는다. +5mm는 권고한 실험 후보이며 native 목표 설정 승인이나 안정 성공 선언이 아니다.

그림은 실제 preview JSON 수치의 source geometry 정적 plot이며 PhysX 또는 Isaac Gym render가 아니다. 측정 표와 재생성 명령은 [기타 Z preview 결과](results/guitar_z_preview_v1/README.md)에 있다.

07·08절의 산출물은 별도 change-reviewer 검수를 통과했다. 최소 gap 집계·수치·단위·raw 각도 해석을 대조하고 두 PNG를 임시 경로에서 픽셀까지 동일하게 재생성했다. 남은 Critical/Warning/Suggestion 없음이며, 원자료 JSON·PNG는 보존했다. [검수 기록](results/guitar_z_preview_v1/review.md), [변경 파일·실제 줄 번호](results/guitar_z_preview_v1/CHANGED_FILES.md).

## 09. 고관절 native drive 독립 fixture 진단

2026-10-06, `hip_drive_probe_v4`. 1-hinge/3-hinge fixture, authored/wide ±180° limit, 0/−90° 시작각, position/off/effort drive의 24조건 요약과 3-hinge −90° 시계열을 기록했다. 메인 humanoid 또는 기타 목표 설정은 바꾸지 않았다.

### 그림 15. 3-hinge fixture의 L_Hip_y 각도편차

![authored/wide bounds에서 세 drive mode의 기록된 L_Hip_y raw 편차 시계열](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hip_drive_probe_v4/images/hip_drive_probe_v4_three_hinge_minus90.png)

3-hinge −90° position 조건에서 최대 raw 편차는 authored 4.291274°, wide 4.196023°였다. bounds를 넓혀도 이 fixture에서 position-drive 이탈은 해소되지 않았다. authored의 off/effort는 target 근처였지만, wide explicit effort는 4.186622° 편차를 보였다. 표와 곡선의 편차는 실제 DOF 측정값이다. EFFORT trace의 `previous_submitted_torque_nm`만 제출 명령 필드이며 실측 토크가 아니다. position drive의 implicit torque는 계측하지 않았다.

초기 DOF 자세/속도와 PD readback, solver, 중력 runtime getter 0, 종료 시 velocity-target getter 0, finite state 및 contact 없음이 확인됐다. native joint type은 `Revolute`다. 이 결과는 격리된 fixture로, 실제 human hip 동작·기타 결합의 원인을 단독 확정하거나 stable candidate/success로 판정하지 않는다. v4의 trace는 v3와 24조건 모두 일치한다. 표·원자료·실패 이력은 [hip drive fixture v4 결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hip_drive_probe_v4/README.md)에 있다.

09절은 별도 change-reviewer 검수를 통과했다. 24 native case 전체와 원자료를 exact 재현하고, 실제 DOF 편차와 제출 torque 필드의 구분을 확인했다. 남은 Critical/Warning/Suggestion 없음이다. [검수 기록](results/hip_drive_probe_v4/review.md), [변경 파일·실제 줄 번호](results/hip_drive_probe_v4/CHANGED_FILES.md).

## 10. 하체 damping-zero native H0 비교

2026-10-06, `lower_kd0_v1`. 하체 native damping=0인 TGS 4/2와 PGS 4/2 조건을 실제 H0에서 각각 0.1초 실행한 요약 결과다. 상체 66개/몸통 9개 gain·target, 초기 전신 자세/root, 기타 목표와 strap rest length는 공통 H0 값이며 main baseline은 바꾸지 않았다. 기타 Z +5mm는 적용하지 않았다.

### 그림 16. TGS/PGS damping-zero 진단 결과

![TGS 4/2와 PGS 4/2의 기타 오차 및 하체 raw 편차 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_kd0_v1/images/lower_kd0_v1_comparison.png)

TGS 4/2는 기타 위치/회전 오차 182.725mm/18.948°와 하체 raw 편차 92.622°를 기록했다. PGS 4/2의 기타 오차는 19.908mm/3.551°였지만 하체 raw 편차 99.455°와 native scalar-limit 위반 55.292°가 남아 두 조건 모두 실패다. `damping=0`으로 문제가 해결되었다고 결론내리지 않는다.

그림은 비교 JSON으로 생성한 진단 요약이며 native renderer 출력이 아니다. 조건·한계·원자료 링크는 [damping-zero 비교 결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_kd0_v1/README.md)에 기록했다. 별도 change-reviewer가 실제 두 조건의 전체 trace·상태·접촉과 native damping/solver, 초기 상태·하체 외 gain 보존을 독립 재현했다. 기존 14조건·새 두 조건·hip 그림의 임시 재생성 결과도 픽셀까지 동일했다. 남은 Critical/Warning/Suggestion 없음이다. [검수 기록](results/lower_kd0_v1/review.md).

## 11. 승인된 초기 기타 Z +5 mm paired native 진단

2026-10-06, `guitar_z_trial_v1`. H0와 실제 기타 초기 world Z +5 mm trial을 각각 240 Hz × 24 steps (0.1초) 비교했다. 사람 초기 상태/root, held targets와 PD/solver, 기타 회전, 공통 절대 strap rest length를 유지했다.

### 그림 17. 초기 source collision shape와 native trial curves

![저장된 t=0 source collision shape에서 H0와 기타 Z +5 mm 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/images/guitar_z_trial_v1_source_geometry_t0.png)

![H0와 기타 Z +5 mm의 target 위치오차, 공통 H0 목표오차, 회전오차 및 strap 경로 시계열](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/images/guitar_z_trial_v1_timeline.png)

초기 source query의 음수 pair는 1,404 human–guitar shape pair 중 H0 1개에서 +5 mm 0개로 바뀌었고 R_Hip signed gap은 −1.331165 mm에서 +3.302684 mm가 됐다. 이 source query는 native cooked-mesh clearance 인증이나 penetration-depth 보정이 아니다. Native first completed step에서도 H0에만 guitar/R_Hip contact row가 있었지만, +5 mm가 전체 scene clearance를 보장하지 않는다. 두 run의 같은 sample에는 R_Ankle −9.690888 mm, R_Toe −8.885874 mm raw ground-contact feature gaps가 있었다. 0.05초에는 두 run 모두 raw label `guitar/guitar × human/L_Knee` contacts가 나타났다.

Candidate goal 기준 최대 위치 오차는 65.315253→63.033062 mm였지만, 공통 원본 H0 목표 기준 +5 mm 최대 위치 오차는 65.348676 mm다. 최대 회전 오차는 7.318146→7.320381°로 사실상 유지됐고 strap tension 기록은 두 run 모두 0 N이다. 따라서 초기 배치 접촉 후보는 개선했으나 안정 자세 성공을 의미하지 않는다. 다음 작업은 발 초기 겹침과 lower-pose hold를 우선 다루며 상체/몸통 PD는 고정한다. 하체 각도/표현 변경은 별도 중요 결정 검토를 거친다. 결과·원자료·후처리 실패 이력은 [paired trial 결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/README.md)에 기록했다. 별도 change-reviewer 검수를 통과했다. 17개 테스트·두 run의 전체 상태/접촉/trace와 그림 픽셀을 독립 재현했고, 후처리 재시도 파일 보존 수정도 검증했다. 남은 지적은 없다. [검수 기록](results/guitar_z_trial_v1/review.md), [변경 파일·실제 줄 번호](results/guitar_z_trial_v1/CHANGED_FILES.md).

## 12. 제한된 하체 초기 자세 탐색과 native 비교

2026-10-06, `lower_initial_pose_v1`. 정적 source-shape 탐색의 101개 설정과 baseline/c01/c02/c03 native 24-step trial을 비교했다. 초기 기타 Z +5 mm, root, 상체/몸통 PD, solver 및 절대 strap 길이는 공통이다.

### 그림 18. 기타 오차와 source-ground gap, 하체 자세 변화

![하체 초기 자세 탐색의 source/native 기록 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/images/lower_initial_pose_v1_comparison.png)

### 그림 19. c02 저장 native pose의 source shape 재구성

![c02의 t=0 및 t=0.1초 저장 pose를 같은 world bounds와 view에서 재구성한 source collision shapes](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/images/lower_initial_pose_v1_c02_poses.png)

파랑은 기타, 주황은 pelvis와 다리, 반투명 회색은 나머지 humanoid다. 저장된 native state의 시작과 24번째 step을 사용한 source collision geometry 재구성이며 PhysX/Isaac renderer 출력은 아니다. 같은 world bounds와 시점에서 시작과 끝 자세를 비교한다. 116.689°는 전체 구간의 peak(step 15, 0.0625초, L_Knee)이며 그림의 끝 시점(step 24) 최대 편차는 L_Ankle 90.608°다. 추가 physics 실행 없이 두 저장 pose만 시각화했다.

c02(L_Hip_x −0.025 rad 추가)는 기타 candidate 목표 최대 오차를 7.174 mm/1.591°까지 낮추고 0.1초 안에 knee/neck contact를 기록하지 않았다. 동시에 raw 하체 actual−target 편차와 native scalar 위반이 90.755°, leg body orientation 변화가 116.689°였으며 source-ground 최소 gap −9.443 mm, 바닥 음수 pair 2개가 남았다. 이는 안정성 성공이 아니다. source-gap은 CPU source-shape query라 PhysX clearance 보장이 아니며, 제한된 탐색은 전 공간을 증명하지 않는다. 결과 표, 수치 한계와 재생성 명령은 [하체 초기 자세 결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/README.md)에 기록했다. 별도 change-reviewer 검수를 통과했다. 20개 테스트와 native 기록·탐색 순위·두 그림의 독립 재현을 확인했고, 구간 peak와 그림의 끝 시점을 구분하는 설명도 검수했다. 남은 지적은 없다. [검수 기록](results/lower_initial_pose_v1/review.md), [변경 파일·실제 줄 번호](results/lower_initial_pose_v1/CHANGED_FILES.md).

## 13. 상체 손 위치와 strap 길이 native 비교

2026-10-06, `pose_strap_v1`. 0.1 s의 strap 5조건과 upper-joint set 17조건(reference 1개와 perturbation 16개), 0.5 s 7조건, 1.0 s 4조건을 comparison_v2 및 저장 trace에서 비교했다. 모든 trial에서 하체는 기존 설정으로 물리 실행했으며 이번 평가에서는 관찰 전용으로 두었다.

### 그림 20. strap 조건별 기타 오차 시계열

![0.1초 strap 조건과 0.5/1초 유지에서 위치 및 회전오차 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/images/pose_strap_v1_native_curves_v2.png)

route-fit 0 N reference는 0.1초에 6.845 mm/1.520°였고, legacy는 7.174 mm/1.591°였다. 20 N preload는 0.1초 7.821 mm/2.226°, 0.5초 51.079 mm/8.618°, 1초 200.537 mm/75.128°였다. 위치 오차만 낮아진 장시간 조건도 회전 오차가 크게 남았으므로 어떤 조건도 지속 유지 성공/최종 채택이 아니다.

### 그림 21. 저장 native pose의 source 손·기타·strap geometry

![reference run t=0, 0.5, 1초의 기타와 양손 source shape, strap route, palm-normal proxy](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/images/pose_strap_v1_reference_geometry_v2.png)

초기 왼손 palm centroid는 대응 넥 단면 하단보다 82.533 mm 낮았고 normal proxy up-dot은 0.869692였다. 초기 source query는 음수 pair 0개였지만 이것이 hand contact나 하중 지지를 증명하지 않는다. 0.5초까지 양손 contact row가 없으며 1초의 contact row도 힘·지지 판정이 아니다. 두 그림은 저장 trace/state 및 source convex collision geometry를 재구성한 CPU visualization이며 Isaac Gym/PhysX renderer 출력이 아니다. 원자료, 33조건 시간별 표와 재생성 명령은 [pose/strap 결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/README.md), 플롯 입력·헬퍼·asset hash는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/plot_manifest.json)에 기록했다.

## 14. 왼손–넥 초기 근접도와 strap 길이 native 진단

2026-10-06, `hand_support_v1`. 저장된 source QP search와 10개 native comparison을 표·그림으로 정리했다. 첫 그림은 reference/p3/p08 시작 자세와 p08 0.5 s saved pose를 같은 world bounds와 카메라 시점으로 재구성하고, 두 번째는 old absolute length와 route-matched strap, p3/p08 유지 trace를 비교한다.

![초기 hand–neck hull witness 및 p08의 0.5초 source pose](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/images/hand_support_v1_source_poses.png)

![0.1초 old/new absolute length와 0.5초 route-match 오차 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/images/hand_support_v1_native_curves.png)

QP unsigned hull 거리의 시작 0.800 mm 수준은 p08에서 0.5 s 종료 시 146.550 mm가 됐고 LH/guitar native contact row는 없었다. 0.5 s p3/p08 위치오차도 61.484/61.483 mm로 이전 reference 58.452 mm보다 컸다. 가까운 source geometry는 hand support나 안정 유지 성공을 입증하지 않는다. signed cutoff query의 sign 한계와 10개 시간별 표는 [hand support 결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/README.md), plotter/helper/input/output hash는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_support_v1/plot_manifest.json)에 기록했다. 두 그림은 저장 pose와 source convex geometry의 CPU 재구성이며 native renderer 출력이 아니다.

## 15. 상체 arm-joint actual-error feedback paired 진단

2026-10-06, `joint_hold_v1`. 24개 arm joint 목표에 bounded actual-error PI correction을 적용한 ON과 held `q_play` OFF를 0.1/0.5/1.0초 저장 native trace로 비교했다. 하체와 몸통/손가락 목표, guitar 및 strap 설정은 유지했다.

### 그림 22. 1초 기타 오차, arm drift 및 보정 포화

![1초 OFF/ON saved trace comparison](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_hold_v1/images/joint_hold_v1_1s_off_on.png)

최대 arm raw drift는 20.997°에서 14.314°로 줄었지만 ON 기타 최대 오차도 196.035 mm/33.994°로 남았다. 최대 delta는 0.15 rad로 제한되며 saturation 수는 240 Hz physics sample 기준이다(1초 212 samples; 독립 60 Hz update 수가 아님). 왼손–기타 contact row는 모두 0이고, palm up-dot proxy 최소는 0.926704였다. 공통 arm scalar-limit violation 0.029066°도 남는다. `decision.json`의 1초 ON raw contact 행은 `human/R_Shoulder` 65, `human/RH:thumb2` 35, `human/RH:thumb3` 78이며 OFF에서는 이 세 부위가 각각 0, 양쪽의 `human/R_Hip`는 각각 239다. 이는 행 개수일 뿐 지지력이나 개선 원인을 입증하지 않으며 LH 지지 성공도 아니다.

### 그림 23. 저장된 공통 시작 및 paired hand–guitar source pose

![t=0 공통 시작과 0.5초/1초 OFF·ON source-shape 재구성](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_hold_v1/images/joint_hold_v1_source_pose_comparison.png)

저장된 상태에서 source collision shape와 strap route를 CPU로 재구성했으며 native renderer 출력이나 contact/clearance 검증이 아니다. 보정은 guitar-error feedback이 아닌 arm joint actual-error PI target-only 방식이고, FK task rejection/rate limit은 미구현이다. six-run audit 및 paired prefix 확인과 controller 경계 tests 4개가 통과했지만, 이는 안정성 성공이나 조건 채택을 뜻하지 않는다. 조건별 최대치와 제한은 [joint-hold 결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_hold_v1/README.md), 최신 입력·asset·출력 해시는 [plot manifest v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_hold_v1/plot_manifest_v2.json)에 기록했다. 기존 `plot_manifest.json`은 재구성에 읽힌 geometry asset hash가 빠진 과거 provenance로 보존한다.

## 16. 오른손 초기 자세 탐색과 native short-run 비교

2026-10-06, `right_support_v1`. 승인된 오른팔 12개 관절의 초기각 범위에서 185개 static source-shape 평가 후, reference와 선택된 세 후보를 각 0.1초 native run으로 비교했다. 왼팔 p08, fingers 42, torso 9, C02 하체, root, guitar +5 mm goal 및 strap 절대 길이 1.1010801317960974 m를 유지했다.

### 그림 24. native 기타 오차와 접촉 행 시점

![Reference와 세 right-arm candidate의 0.1초 위치/회전 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_support_v1/images/right_support_v1_native_curves.png)

Reference 최대 오차는 6.878 mm/1.521°였고 후보들은 각각 15.556 mm/3.495°, 15.542 mm/3.492°, 15.534 mm/3.491°였다. 후보의 R_Shoulder × guitar raw contact 행은 step 3 (0.0125 s)과 step 4 (0.016667 s)에 관찰됐다. 첫 행의 raw `initialOverlap`은 약 −4.092 mm이며 관통 깊이로 환산하지 않는다. 행의 발생은 오차 차이의 원인이나 지지를 증명하지 않는다.

### 그림 25. RH:palm/G:body witness와 기타 neck/body source shapes

![Reference와 candidate_01의 저장 t=0/0.1초 오른손 및 기타 neck/body source shapes](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_support_v1/images/right_support_v1_source_geometry_v2.png)

초기 unsigned RH:palm/G:body source hull distance는 100.306 mm에서 후보 3.230/7.044/7.180 mm로 줄었으나 0.1초 종료에는 106.523 mm 대 23.201/27.712/27.233 mm였다. 모든 조건의 LH/RH hand contact 행은 0, hip 행은 각각 23이며 후보의 shoulder 행은 2다. 이는 행 계수이며 지지력이나 안정성 성공 판단이 아니다. 그림은 saved native pose의 source shape 재구성으로 native renderer/cooked clearance 판정이 아니다. long run은 없어 prefix/장기 유지 주장은 하지 않는다. 원자료 표와 제약은 [right-support 결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_support_v1/README.md), 최신 입력·asset·helper·PNG 해시는 [plot manifest v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_support_v1/plot_manifest_v2.json)에 기록했다. 이전 `right_support_v1_source_geometry.png`와 `plot_manifest.json`은 이전 neck/body 캡션이 반영되지 않은 보존 표시 초안이다. 이전 `comparison.json`은 초기 후처리 기록으로 보존되며 현재 산출물은 `comparison_v2.json`을 참조한다. palm-position feedback 제안은 사용자 승인 대기 중이다.

## 17. 오른어깨 source-query audit와 contact sample 정렬

2026-10-06, `right_shoulder_audit_v1`. `audit_v2.json`의 source-query 100행과 `contact_alignment.json`의 native contact 관측 두 개만 정리했다. 왼손 조건은 동일하며, 시작 RH:palm/G:body source hull 거리는 100.306→3.230 mm, R_Shoulder/G:body는 35.395→0.787 mm였다. 손과 어깨가 동시에 가까워진 source proxy이며 접촉 지지나 clearance를 뜻하지 않는다.

### 그림 26. 다섯 저장 pose의 source 거리와 두 contact 관측값

![오른어깨 source-hull 거리의 5개 저장 상태와 관측된 native/source gap 값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_shoulder_audit_v1/images/right_shoulder_audit_samples.png)

step 3/4의 raw native `initialOverlap`은 각각 이전 저장 step의 source signed gap과 2.04e−8 m, 6.71e−9 m 차이였다. 동일 번호 저장 step의 값과는 일치하지 않았다. 이 비교는 관측 행 두 개에만 해당하며 모든 solver 단계나 cooked geometry로 일반화하지 않는다.

### 그림 27. 시작 pose의 오른손·어깨와 기타 source geometry

![reference와 candidate 시작 source geometry 및 R_Shoulder/RH palm witness](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_shoulder_audit_v1/images/right_shoulder_audit_initial_geometry.png)

저장 pose의 source collision shape를 CPU로 재구성한 그림이며 native renderer 출력이나 clearance 인증이 아니다. source query 100개의 검사는 모두 통과했고 이전 80행 `audit.json`과 `source_v1` script도 보존했다. 다음 관측 방향은 손·어깨·상완을 함께 보는 초기각 진단이며 hard gate나 controller는 추가하지 않았다. palm-position feedback은 승인 대기 중이다. 원자료·표·재생성 명령은 [오른어깨 audit 결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_shoulder_audit_v1/README.md)에, geometry asset 및 PNG 해시는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_shoulder_audit_v1/plot_manifest.json)에 기록했다.

## 18. 오른팔 각도 조건의 source 거리와 짧은 native 비교

2026-10-06, `right_clearance_v3`. 기준과 세 통과 후보의 0.1초 저장 trace를 비교했다. 기타 위치·회전 오차 및 shoulder contact 행 시점은 그림 28에 표시했고, reference와 `ty015_sx010`의 t=0/0.1초 source pose는 그림 29에 같은 축 범위와 시점으로 재구성했다.

### 그림 28. 네 native run의 기타 위치·회전 오차 trace

![right_clearance_v3 네 조건의 0.1초 위치·회전 오차와 shoulder contact 행 시점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_clearance_v3/artifacts/right_clearance_v3_native_curves.png)

### 그림 29. reference 및 ty015_sx010의 저장 source pose

![reference와 ty015_sx010의 시작·종료 source geometry](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_clearance_v3/artifacts/right_clearance_v3_source_poses.png)

초기 RH palm/G:body 거리 100.306 mm에서 후보별 38.250/20.827/12.065 mm, R_Shoulder/G:body 거리는 35.395 mm에서 5.565/2.663/2.910 mm였다. 그러나 최종 RH palm source gap은 106.523/56.265/40.294/32.353 mm로 모든 run에서 커졌다. `ty015_sx010`의 최대 오차는 reference와 2.363 µm/0.001069° 차이여서 의미 있는 개선으로 단정하지 않는다. `ty0175` 두 run의 shoulder contact 행은 각 2개이며 손 contact 행은 모두 0이다. 행 수와 source proxy는 지지·원인·clearance·안정 유지 성공을 입증하지 않는다. 그림의 주황색 witness는 가독성을 위해 source surface 위에 겹쳐 표시했으며 실제 앞뒤 가림 관계를 나타내지 않는다. 제한, 원자료 및 재현 명령은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_clearance_v3/README.md), 현재 이미지/input/helper/asset hash는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_clearance_v3/artifacts/plot_manifest.json)에 기록했다. 이전 source witness 선분이 덜 보이는 버전은 [artifacts_v1 보존본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_clearance_v3/artifacts_v1)이다.

## 19. 오른손 distal 초기각과 고정 PI의 OFF/ON 비교

2026-10-06, `right_distal_v1`. 65개 초기 source-query 조건 중 candidate_01–03과 기준의 0.1초 native run, 이어서 candidate_01 초기각의 기존 joint-hold PI OFF/ON 6개 저장 run을 요약했다. 그림 basename `joint_hold_v1`은 기존 plotter 명칭이고, 이번 run 경로는 `right_distal_v1/joint_hold`다.

### 그림 30. 1초 OFF/ON trace, arm drift 및 보정 포화

![right_distal_v1 1초 OFF/ON trace 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_v1/artifacts/images/joint_hold_v1_1s_off_on.png)

### 그림 31. 시작·0.5초·1초 저장 source pose

![right_distal_v1의 source collision shapes와 strap route 재구성](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_v1/artifacts/images/joint_hold_v1_source_pose_comparison.png)

0.1초 native 결과는 약 6.876 mm/1.52°였고 손·어깨 행은 모두 0이다. PI ON은 arm drift와 0.5/1초 기타 오차를 낮췄지만 1초에도 121.298 mm/29.759°가 남고 0.030295° scalar-limit 위반이 계속됐다. 0.1초 run에서는 손 접촉 행이 없었고, 이후 긴 실행에서 오른엄지 접촉 행이 관찰됐지만 물리적 지지를 보장하지 않으며 첫/마지막 sample만으로 연속 접촉을 말할 수도 없다. 안정 연주 자세로 채택하지 않는다. 다음은 같은 초기각에서 기존 승인 범위의 strap preload matched short comparison이다. 그림은 저장 pose 기반 CPU source geometry 재구성이며 native renderer나 clearance 인증이 아니다. 상세 표와 제한은 [right_distal_v1 결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_v1/README.md), 입력·자산·출력 해시는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_v1/artifacts/plot_manifest.json)에 기록했다.

## 20. 오른손 distal 초기각의 고정 strap-load OFF/ON 비교

2026-10-06, `right_distal_strap_v1`. 0.1초 0/5/10/20 N 초기 law tension 네 조건과 0.5초 0/5 N OFF/ON 저장 trace를 한 그림에 비교했다. 같은 candidate_01 초기각, 고정된 run별 absolute rest length와 기존 PI 설정을 사용했다.

### 그림 32. preload별 기타 위치 및 회전오차

![0.1초 0/5/10/20 N와 0.5초 0/5 N OFF/ON 기타 오차 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_strap_v1/artifacts/right_distal_strap_v1_curves.png)

0.1초에서는 load별 기타 위치·회전 오차 곡선만 OFF/ON 간 정확히 겹쳤다. 이는 다른 humanoid 상태까지 같다는 뜻이 아니다. 5 N은 위치오차를 낮추면서 회전오차를 높였고, 10/20 N은 두 지표 모두 0 N보다 높았다. 0.5초 PI ON은 각 load 안에서 오차를 낮췄지만, 0/5 N 간 비교에서는 위치와 회전 모두를 개선하는 load가 없었다. 더 긴 run은 진행하지 않았고 0 N을 진단 기준으로 유지한다. LH/어깨 contact 행은 모두 0이며 오른엄지 contact row 수는 지지력이나 원인을 나타내지 않는다. rest length는 run 내 고정값이고 strap-law 적용 tension은 상태에 따라 바뀐다. 결과 표와 제한은 [right_distal_strap_v1 결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_strap_v1/README.md), 사용 입력·코드·출력 hash는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_strap_v1/artifacts/plot_manifest.json)에 기록했다.

## 21. 오른손 distal 각 미세 조정과 고정 PI 진단

2026-10-06, `right_distal_fine_v1`. 37개 정적 source-query 중 기준과 후보 3개의 0.1초 native 결과, 선택 후보 02의 새 joint-hold PI OFF/ON 6회 및 이전 c01의 기존 저장 OFF/ON 6회(재실행 없음)를 비교했다. 후보 02는 c01 대비 `R_Elbow_x +0.01 rad`, `R_Wrist_x −0.005 rad`다. 나머지 초기 조건과 절대 LA 1.1010801317960974 m는 유지했다.

### 그림 33. 이전 c01과 후보 02의 0.1/0.5/1초 기타 오차 trace

![이전 c01과 후보 02 저장 run의 OFF/ON 기타 위치·회전 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/artifacts/right_distal_fine_v1_curves.png)

### 그림 34. 기준 및 후보 02의 저장 source pose

![기준과 후보 02의 t=0 및 t=0.1초 source collision 형상과 unsigned witness 표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/artifacts/right_distal_fine_v1_source_poses.png)

후보 02 초기 RH palm/body unsigned source-hull 간격은 2.257 mm, 기준은 3.937 mm였고 세 후보 모두 source gate를 통과했다. 0.1초 기타 오차는 후보 02가 6.872 mm/1.519°로 기준 6.876 mm/1.520°와 거의 같았다. 후보 02 PI ON의 0.5초 최대 오차는 34.975 mm/4.871°, 1초는 76.099 mm/14.184°로 이전 c01의 35.848 mm/5.052°, 121.298 mm/29.759°보다 낮았다. 그러나 1초 arm drift 14.280°와 212개 physics sample의 보정 포화, 0.030294° scalar-limit 위반이 남아 안정 연주 성공으로 보지 않는다. LH·어깨 접촉은 없고, RH thumb3 187행/69개 sample 및 thumb2 6행/4개 sample의 관측은 접촉 지지력이나 연속성을 입증하지 않는다. 주황 witness 선·점과 패널의 gap 수치는 `comparison_v3.json` unsigned source-hull overlay이며 clearance 판정이 아니다. 이전 v2 입력 manifest는 보존되지 않은 downstream manifest 시점 해시를 포함해 현 provenance로 쓰지 않고, v3는 실제 raw/source/helper 의존성만 담는다. 초기 source 간격은 cooked clearance 보장이 아니며 source 형상 그림은 native 렌더가 아니다. 선택 후보를 다음 진단 기준으로 보존하되 새 제어기·gain·gate는 적용하지 않는다. 상세 수치·제한·재현 명령은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/README.md), 입력·helper·asset·출력 해시는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/artifacts/plot_manifest.json)에 기록했다.

## 22. 오른손 손목각 유지 구간 비교

2026-10-06, `right_wrist_retention_v1`. fine c02 자세에서 `R_Wrist_x`만 −0.0025/−0.005/+0.0025 rad 바꾼 0.5초 ON 비교와, 기준/+0.0025의 1초 ON 및 +0.0025 OFF 저장 trace를 묶었다. 기준을 포함해 새 native run은 총 13개이며, 기존 fine c02 raw 기준 재현 검사도 통과했다.

### 그림 35. 0.5초 선택각 및 1초 기준/후보 trace

![오른손 손목 offset 0.5초 네 ON 조건 및 1초 ON/OFF 기타 오차 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_retention_v1/artifacts/right_wrist_retention_v1.png)

+0.0025 rad 조건은 0.5초 최대오차가 34.743 mm/4.818°로 기준 34.975 mm/4.871°보다 낮았지만, 1초 ON은 84.746 mm/16.983°로 기준 76.099 mm/14.184°보다 높았다. +0.0025 OFF의 1초 오차는 137.369 mm/33.307°였다. 단기 개선은 더 긴 유지 성공을 뜻하지 않으며 손목 offset은 최종 채택하지 않는다. 1초 reference ON에서 RH thumb3 187행/69 sample, +0.0025 ON에서 168행/58 sample 및 +0.0025 OFF에서 133행/41 sample이 관측됐다. LH·어깨 행은 0이며, 접촉 행·sample 수는 지지력·원인·관통깊이 또는 연속 접촉 인증이 아니다. 다음 진단은 기존 fine c02 자세와 LA를 유지한다. 입력 hash는 plot 전 검증됐고, 상세 수치·제한·재생 명령은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_retention_v1/README.md), 코드·입력·출력 hash는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_retention_v1/artifacts/plot_manifest.json)에 있다.

## 23. 오른팔 팔꿈치 초기각의 유지 구간 비교

2026-10-06, `right_elbow_retention_v1`. fine c02에서 팔꿈치 한 축만 조정한 초기 source query와 통과 조건의 0.1/0.5초 저장 trace, 1초 reference/y+0.005 ON trace를 비교했다. 초기 `R_Elbow_x +0.0025 rad`는 음수 source pair로 제외했다.

### 그림 36. 0.5초 네 조건 및 1초 reference/y+0.005

![오른팔 elbow 초기각 0.5초 네 ON 조건과 1초 두 ON trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_retention_v1/artifacts/right_elbow_retention_v1.png)

y +0.005 rad는 0.5초 위치·회전 오차를 33.889 mm/4.696°로 낮췄지만, 1초에는 118.323 mm/29.068°로 기준 76.099 mm/14.184°보다 커졌다. 1초에는 x/z 후보나 OFF 조건을 실행하지 않았다. LH·어깨 contact 행은 없고, RH thumb3 최초/최종 관측은 기준 step 84–160, y 조건 step 82–143이다. 이 구간의 끝점만으로 연속 접촉이나 물리 지지를 단정할 수 없다. 두 run 모두 PI 보정이 212 physics samples에서 포화됐다. 기존 fine c02 진단 기준을 유지하고 손목·팔꿈치 후보의 안정 연주/feedback/학습 성공은 주장하지 않는다. 정확한 수치·제한·재생 명령은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_retention_v1/README.md), 검증 입력과 그림 해시는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_retention_v1/artifacts/plot_manifest.json)에 기록했다.

## 24. 오른팔 팔꿈치 Y 음수 초기각 비교

2026-10-06. 기준과 `R_Elbow_y −0.00125 rad`의 저장 ON trace를 0.1초와 0.5초로 비교했다. 다른 세 초기 후보는 source 음수 pair 1개로 제외되어 native 실행하지 않았다.

### 그림 37. 기준과 음수 각도 후보의 기타 위치·회전 오차

![0.1초 및 0.5초 기준/음수 후보 저장 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_y_negative_v1/artifacts_v2/right_elbow_y_negative_v1.png)

0.1초의 최대 위치/회전 오차는 기준 6.872016 mm/1.519281°, 후보 6.871872 mm/1.519261°로 거의 같았다. 0.5초는 기준 34.975339 mm/4.871416°, 후보 35.237610 mm/4.909962°로 후보가 조금 높았다. 1초와 OFF run은 수행하지 않았고 후보를 채택하지 않아 fine c02를 유지한다. 0.5초 run의 PI 포화는 각 92 physics sample이며 LH/어깨 contact 행은 0이다. RH 엄지 접촉 행·sample 수는 지지력이나 연속 접촉을 보장하지 않는다. source 검사는 cooked clearance 인증이 아니다. 이전 고정 패널 그림은 `artifacts/`와 `artifacts_v1/`에 보존했고, 현재 canonical 그림은 [artifacts_v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_y_negative_v1/artifacts_v2/right_elbow_y_negative_v1.png)에 있다. 상세 표와 재생 명령은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_y_negative_v1/README.md), 최신 입력·출력 SHA는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_y_negative_v1/artifacts_v2/plot_manifest.json)에 기록했다.

## 25. 팔 초기각 음수 후보의 후기 구간 비교

2026-10-06, `negative_pose_late_v1`. 기준과 fresh source 검사를 통과한 손목 X −0.0025/−0.005 rad 및 팔꿈치 Y −0.00125 rad를 0.1/0.5/1초 ON으로 직접 비교했다. 손목 −0.005 rad만 세 구간의 ON/OFF 저장 run을 보유한다.

### 그림 38. 세 기간의 기타 위치·회전 오차 trace

![네 초기 조건 및 손목 X minus0.005 rad OFF trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/artifacts/negative_pose_late_v1.png)

손목 X −0.005 rad는 0.5초 최대 위치/회전 오차가 기준보다 컸지만, 1초 ON에서는 73.660431 mm/13.502121°로 기준 76.099207 mm/14.183879°보다 낮았다. 같은 조건 OFF는 144.260293 mm/36.309554°였다. 1초 ON에는 212 physics samples의 PI 포화와 큰 종료 속도가 남아 있으며, 설정은 다음 진단 reference일 뿐 안정 연주 후보로 인증되지 않았다. RH thumb3 관측 행·sample 수는 접촉력이나 연속 지지를 뜻하지 않고 LH·어깨 contact 행은 0이다. 기타 오차 feedback을 추가하지 않았다. 수치·제한·재생 명령은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/README.md), 생성 provenance는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/negative_pose_late_v1/artifacts/plot_manifest.json)에 기록했다.

## 26. 개선 wrist 자세에서 초기 strap 길이 비교

2026-10-06, `wrist_pose_strap_v1`. `R_Wrist_x −0.005 rad` 자세를 고정하고 0/5/10/20 N 초기 law-tension 설정의 절대 strap rest length를 비교한 저장 ON run 12개를 정리했다. 재사용 plotter가 0.1/0.5/1초 trace를 별도 기간 축에 그린다.

### 그림 39. 네 초기 strap 길이 조건의 기타 위치·회전 오차

![0/5/10/20 N 초기 law 설정의 저장된 기타 오차 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/artifacts/wrist_pose_strap_v1.png)

0.1초에서는 5 N 설정의 위치 오차가 낮지만 회전 오차는 높았다. 1초에서는 어떤 rest length도 0 N 기준보다 위치·회전 오차를 함께 줄이지 못해 새 길이를 채택하지 않았다. 0 N + 개선 wrist 자세는 다음 진단용 reference이며 연주 안정 성공이 아니다. 각 run의 rest length는 고정되지만 law tension은 변하며, 20 N 초기 설정의 최대 적용 tension은 53.2533 N에 도달했다. 1초 ON은 모두 212 physics samples 동안 PI 포화됐다. contact 행은 물리적 지지를 인증하지 않는다. 표와 재현 명령은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/README.md), 생성 provenance는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/wrist_pose_strap_v1/artifacts/plot_manifest.json)에 기록했다.

## 27. 작은 초기 strap preload 비교

2026-10-06, `small_preload_v1`. 개선 wrist 자세에서 0/1/2 N 초기 law 설정에 대응하는 고정 rest length의 9개 저장 ON run을 0.1/0.5/1초로 비교했다. 기존 0 N 입력은 byte-exact 중복으로 재사용했다.

### 그림 40. 세 초기 strap 길이의 기타 위치·회전 오차

![0/1/2 N 초기 law 설정의 0.1/0.5/1초 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/artifacts/small_preload_v1.png)

1 N의 0.1/0.5초 작은 개선은 1초에 유지되지 않았고, 2 N은 1초에서 기준보다 크게 악화됐다. 따라서 0 N 길이를 진단 reference로 유지하고 새 길이는 채택하지 않았다. run 동안 rest length는 고정이지만 law tension은 시간에 따라 변한다. 1초 세 run은 모두 212 physics sample 동안 PI 포화가 있었으며 접촉 행은 지지력 인증이 아니다. 상세 표·제한은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/README.md), 저장 provenance는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_preload_v1/artifacts/plot_manifest.json)에 기록했다.

## 28. 오른손 손목의 추가 음수 초기각

2026-10-06, `right_wrist_negative_extension_v1`. 기존 wrist reference와 추가 −0.0025/−0.005 rad의 source 통과 세 설정을 0.1/0.5/1초 ON 저장 trace로 비교했다.

### 그림 41. 오른손 손목의 세 기간 기타 오차

![기준 및 두 추가 음수 손목 각도의 기타 오차 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/artifacts/right_wrist_negative_extension_v1.png)

두 추가 음수 각도 모두 1초 위치·회전 오차가 reference보다 높아 채택하지 않았고 OFF 조건도 실행하지 않았다. 1초 ON 세 run은 각각 212 physics samples 동안 PI 포화됐다. 접촉 행·sample은 힘이나 지지력을 인증하지 않는다. 다음 방향은 현재 기준각의 양옆 ±0.00125 rad를 fresh source 검사하는 것이다. 세부 수치와 제약은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/README.md), raw·plot SHA는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_negative_extension_v1/artifacts/plot_manifest.json)에 기록했다.

## 29. 오른손 손목의 국소 초기각 비교

2026-10-06, `right_wrist_local_v1`. 기존 wrist reference와 좌우 ±0.00125 rad의 세 source 통과 조건을 0.1/0.5/1초 ON 저장 trace로 비교했다.

### 그림 42. 손목 국소 초기각과 기타 위치·회전 오차

![기준 및 손목 양옆 0.00125 rad의 세 기간 오차 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/artifacts/right_wrist_local_v1.png)

+0.00125 rad는 0.5초에서 오차 두 값이 조금 낮았지만 1초에는 기준보다 높았다. 두 조정각 모두 채택하지 않았고 OFF run도 추가하지 않았다. 1초 ON은 각 212 physics sample의 PI 포화가 남았으며 contact 관측은 힘·지지를 인증하지 않는다. wrist 세분 탐색 대신 다음에는 현재 자세에서 팔꿈치 X 설정을 fresh source 검사한다. 세부 표와 제한은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/README.md), provenance는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_wrist_local_v1/artifacts/plot_manifest.json)에 있다.

## 30. 고정 손목 자세의 오른쪽 팔꿈치 X 초기각 비교

2026-10-06, `right_elbow_wrist_combo_v1`. 손목 기준각을 유지하고 `R_Elbow_x` 기준 및 −0.0025/−0.005 rad의 source 통과 조건 3개를 세 기간 ON trace로 비교했다.

### 그림 43. 팔꿈치 X 후보의 기타 오차 trace

![고정 손목 자세에서 팔꿈치 X 세 초기각의 기간별 기타 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/artifacts/right_elbow_wrist_combo_v1.png)

두 팔꿈치 조정각은 모두 1초 위치·회전 오차가 기준보다 커 채택하지 않았고 OFF run은 추가하지 않았다. 1초 ON에서 PI 포화가 각각 212 physics samples 동안 있었고 LH·어깨 접촉 행은 0이다. RH thumb 접촉 관측은 힘이나 지지를 인증하지 않는다. 오른팔 distal 세분화는 보류하고 같은 손목·LA에서 왼팔 elbow/wrist 초기각을 fresh source 검사한다. 자세, 시험 범위, 표는 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/README.md), trace 입력·그림 해시는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_elbow_wrist_combo_v1/artifacts/plot_manifest.json)에 기록했다.

## 31. 왼팔 distal 단일축 초기각 비교

2026-10-07, `left_distal_initial_v1`. 오른팔·손목 reference와 초기 법칙 장력 0 N에 해당하는 고정 LA를 유지하고 왼팔 elbow/wrist의 초기각 후보를 source 검사했다. 통과한 6개 조건의 0.1/0.5/1초 ON 저장 trace 18개를 비교했다.

### 그림 44. 왼팔 초기각별 기타 위치·회전 오차

![왼팔 distal 통과 조건 및 기준의 세 기간 저장 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/artifacts/left_distal_initial_v1.png)

다섯 후보 모두 1초 위치·회전 오차가 기준보다 높아 새 각도를 채택하지 않았고 OFF 연장도 하지 않았다. 기준도 큰 drift와 속도가 남아 안정 연주 성공이 아니다. 가까운 LH:palm source query는 native 접촉이나 지지력을 보증하지 않는다. 각 1초 run에서 arm 24개 관절 중 하나 이상이 212 physics samples 동안 PI 포화됐고, 최대 scalar-limit 차이가 남았다. 상세 수치와 제한은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/README.md), provenance는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_distal_initial_v1/artifacts/plot_manifest.json)에 기록했다.

## 32. 왼손바닥 source 경계 방향의 초기각 비교

2026-10-07, `left_palm_boundary_v1`. fresh source 검사를 통과한, 기준을 포함한 초기조건 6개의 ON trace 18개, 상위 두 각도의 OFF 대조 6개를 저장 자료에서 비교했다. source negative pair를 보인 두 설정은 native 실행하지 않았다.

### 그림 45. 왼팔 초기각별 기타 위치·회전 오차 trace

![왼팔 source 통과 조건과 기준의 ON/OFF 기타 오차 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/artifacts/left_palm_boundary_v1.png)

1초 ON 세 후보가 기준보다 조금 낮았고 `L_Wrist_x −0.0125 rad`가 가장 낮았지만, ON도 73.268255 mm/13.439339°의 오차와 212 physics samples PI 포화가 남아 안정 연주 성공은 아니다. 같은 각도의 OFF 오차는 144.267967 mm/36.395296°였다. 다음 진단 기준으로만 보존하고, 전체 pose에서 초기 strap-length 조건을 다시 검사한다. 표·제한·재생 명령은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/README.md), SHA provenance는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/artifacts/plot_manifest.json)에 기록했다.

## 33. 새 왼손목 기준 자세의 초기 strap 길이

2026-10-07, `left_wrist_strap_v1`. 새 왼손목 `L_Wrist_x = −0.9063641667366027 rad`에서 초기 법칙 장력 0/1/2 N에 대응하는 절대 rest length의 저장 ON trace 9개를 비교했다. rest length는 각 run 동안 고정이고 실제 strap tension은 변한다.

### 그림 46. 세 초기 strap 길이의 기타 위치·회전 오차

![새 왼손목 기준 자세에서 0/1/2 N 초기 조건의 저장 기타 오차 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_wrist_strap_v1/artifacts/left_wrist_strap_v1.png)

1초에서 1 N과 2 N은 0 N 기준보다 위치·회전 오차가 커 채택하지 않았다. 0 N 설정은 새 자세의 진단 기준일 뿐 안정 연주 성공이 아니며, 1초 ON 세 run은 arm PI 포화 212 physics samples와 큰 drift가 남는다. 기존 `wrist_minus0050` 경로명은 이전 결과를 뜻하지 않는 reference alias다. 다음은 같은 pose의 3초 후기 상태 관찰이며 새로운 안정성 기준이 아니다. 입력과 수치·제약은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_wrist_strap_v1/README.md), 그림 provenance는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_wrist_strap_v1/artifacts/plot_manifest.json)에 기록했다.

## 34. 저장된 3초 pose와 후기 오차 관찰

2026-10-07, `quiescent_3s_v1`. 동일 초기 설정과 joint-error PI로 3초 ON native 실행을 한 번 수행했다. 그 trace 및 0/1/3초 저장 pose로 그래프와 형상을 재구성했으며, 산출물 생성 과정에서는 추가 native 실행을 하지 않았다.

### 그림 47. 저장 pose의 source geometry와 strap route

![3초 run의 저장 native pose를 source collision shapes로 재구성한 세 panel](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/artifacts/geometry/quiescent_3s_source_geometry.png)

세 panel은 같은 camera·world bounds를 사용한 source-shape 재구성이지 native PhysX renderer가 아니다. 오른쪽 손·팔·골반 contact 행이 기록됐지만 행/sample counts는 힘·원인·연속 지지·관통 깊이를 증명하지 않으며 LH/어깨 contact 행은 0이다. 종단 선속도/각속도는 낮아도 목표 오차 236.386968 mm/77.801738°와 arm drift가 남아 안정성 성공으로 보지 않는다. 3초는 관찰 구간이지 WAIT 조건이나 새 성공 기준이 아니다. trace 수치와 limits는 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/README.md), source asset 및 출력 provenance는 [geometry manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/artifacts/geometry/plot_manifest.json)에 기록했다.

### 그림 48. 저장된 3초 기타 오차 trace

![저장된 3초 CPU PhysX 기타 위치·회전 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/artifacts/trace/quiescent_3s_v1.png)

3초 종료 위치·회전 오차는 236.386968 mm/77.801738°였고 arm PI는 692/720 held physics samples에서 포화됐다. 이 trace만으로 연주 안정성이나 지속 지지를 인증하지 않는다. 재생 명령과 검증 범위는 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/README.md), trace provenance는 [trace manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/artifacts/trace/plot_manifest.json)에 있다.

## 35. 저장된 palm 기준점 변위 audit

2026-10-07, `palm_frame_audit_v1`. 최종 `measurements_validated/audit.json`과 CPU Jacobian descriptor를 읽어 저장된 0·1·3초 좌표의 차이를 그렸다. 이 시각화 과정에서는 native 실행이나 physics step을 추가하지 않았다. 이전 8-check 그림·입력은 검수 이력으로 보존했고, 추가된 양손 palm 행 nonzero 검사를 포함한 9개 audit 검사가 모두 통과한 최종 자료를 아래 canonical figure로 사용한다.

### 그림 49. 좌우 palm 기준점의 이산 변위

![저장된 0초 대비 1초·3초 palm 기준점 변위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/artifacts_validated/palm_frame_displacement.png)

왼쪽·오른쪽 panel은 source convex-hull volume center, palm body origin, wrist origin의 t=0 기준 변위를 1초와 3초에서 비교한다. LH hull center/body origin/wrist는 1초 138.278/127.095/119.911 mm, 3초 144.535/131.942/124.347 mm였고, RH는 각각 20.822/22.886/25.630 mm와 25.635/28.264/31.255 mm였다. hull center는 접촉점·해부학적 중심·native COM이 아니며, 막대는 이산 저장 표본일 뿐 연속 궤적이 아니다. audit 9개 검사와 CPU fixed-root Jacobian shape/nonzero-row 준비 검사는 통과했지만 frame/FK/J 정확성, 접촉, 안정성 또는 제어 적합성을 인증하지 않는다. 세부 표와 한계는 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/README.md), 최종 입력·plotter·출력 SHA는 [validated plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_frame_audit_v1/artifacts_validated/plot_manifest.json)에 기록했다. 다음 단계는 승인된 초기 조건 안에서 native FK 유한차분으로 frame 기준을 검증하는 설계 검토다.

## 36. Native palm Jacobian과 fresh FK 좌표 오차

2026-10-07, `palm_jacobian_fk_v1`. Final validated raw comparison과 좌표 보정 comparison의 JSON에서 그림을 만들었다. 이는 한 초기 자세의 12개 왼팔 관절 좌표 변화에 대한 오차 요약이며 추가 native query를 수행하지 않았다.

### 그림 50. 관절군별 최대 Jacobian/FK 좌표 오차

![초기 왼팔 관절군별 raw 및 좌표 보정 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/artifacts_validated/palm_fk_coordinate_errors.png)

각 막대는 관절군의 x/y/z 좌표별 오차 norm 중 최댓값이며 로그 축이다. JSON의 위치 오차 m/rad 값은 mm/rad로 환산해 그렸다. 첫 두 panel은 native Jacobian raw 비교와 expmap tangent 보정 후 fresh FK 차분을 대조한다. 세 번째 panel은 tangent를 적용한 뒤 선형 Jacobian의 기준점을 body origin으로 가정해 source center로 옮긴 경우와 COM 기준으로 옮긴 경우를 비교한다. 최대 COM 위치 오차는 0.215649087에서 0.000275001 m/rad로, angular 오차는 0.678072945에서 0.000194957 rad/rad로 줄었다. 그러나 선형 Jacobian의 기준점을 body origin으로 가정해 source center로 옮기면 최대 0.042214636 m/rad가 남았고 COM 기준 이동 후 값은 0.000274299 m/rad였다. 현재 초기 조건의 좌표 차분은 tangent 및 COM 기준 설명을 뒷받침하지만 importer 전반, runtime Jacobian, 접촉이나 안정성의 보증은 아니다. 형상 중심은 접촉점·해부학적 중심·native COM이 아니다. 표·재생성 명령·한계는 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/README.md), 입력 및 출력 provenance는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/artifacts_validated/plot_manifest.json)에 있다.

## 37. Runtime palm Jacobian cache와 velocity residual

2026-10-07, `palm_jacobian_runtime_v1`. 저장된 24 physics steps와 25 query 표본의 JSON에서 잔차 그래프를 만들었다. 이번 그림 작업에서는 native run이나 설정 변경을 추가하지 않았다.

### 그림 51. Pre-refresh/refreshed Jacobian velocity 오차

![24-step 동안 좌우 palm Jacobian과 native velocity 잔차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/artifacts_validated/palm_runtime_velocity_residuals.png)

곡선은 물리 완료 step 1–24만 포함하며 t=0 pre-refresh zero buffer는 제외했다. 초기 refresh는 직전 성공 초기 Jacobian과 exact match였고 이후 pre-refresh cache 값은 직전 query의 refreshed 값과 exact match했다. 좌·중 panel은 각각 COM 선속도/각속도 잔차를 pre-refresh와 refreshed Jacobian에서 비교하고, 우 panel은 refreshed Jacobian 예측을 native body linear velocity가 COM 속도라는 가설과 origin 속도라는 가설로 각각 대조한다. origin 가설은 native body linear velocity에 `ω × (COM − origin)`을 더해 COM 속도로 옮기며, Jacobian 기준점을 바꾼 비교가 아니다. 최대 refreshed COM 가설 오차는 LH 1.500569 mm/s, RH 1.371527 mm/s이고, native body linear velocity를 origin 값으로 해석해 COM에 옮긴 오차는 각각 68.134978 mm/s, 49.273723 mm/s였다. 관측된 cache timing 동작은 모든 importer/실행 시점 계약이나 runtime 제어 정확성의 증명이 아니다. 기타 목표는 종료 시 6.874401 mm/1.519676° 오차가 남아 있으며 안정성 성공으로 보지 않는다. 상세 수치·제한은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/README.md), raw input·producer·output provenance는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/artifacts_validated/plot_manifest.json)에 있다.

## 38. Palm 위치 보정의 독립 축별 world-axis authority

2026-10-07, `palm_task_authority_v1`. 25개 저장 runtime query에서 계산된 기존 관절 delta box의 독립 축별 선형 범위와 필요한 world XYZ displacement를 그렸다. 산출물 생성 과정에서 추가 native run이나 제어 변경은 하지 않았다.

### 그림 52. XYZ 필요 보정과 축별 선형 interval

![0.1초 저장 query별 XYZ 요구 보정과 축별 선형 범위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_task_authority_v1/artifacts_validated/palm_axis_authority.png)

파란 band는 각 저장 시점의 `A(q_actual)`와 기존 delta box에서 얻은 독립 world-axis 선형 interval이고, 빨간 선은 `p_goal − p_current` world displacement다. A는 해당 시점 q_actual의 3×12 위치 map이며, 선형화는 local이지만 표시 좌표는 world XYZ다. 25개 표본 모두 세 필요 좌표가 각각 해당 시점의 축 interval 안에 있었다. 이는 위치 task를 축별 범위만으로 배제할 수 없다는 관찰이며, 동일 관절 보정이 세 축을 동시에 맞춘다는 증명은 아니다. 필요값·범위 요약과 제한은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_task_authority_v1/README.md), raw input 및 그림 provenance는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_task_authority_v1/artifacts_validated/plot_manifest.json)에 있다. Full FK 도달성, contact, drive 유효성, 기타 안정성 및 새 위치 controller는 검증·승인·구현되지 않았다.

## 39. 초기 왼손–기타 근접 source query 관찰

2026-10-07, `left_early_source_v1`. 기존 저장 실행의 7개 초기 시점과 0/0.1초 source triangle snapshot을 읽어 정적 그림으로 만들었다. 산출 과정에서 추가 native 실행은 하지 않았다.

### 그림 53. 초기 거리 query와 손 proxy 관측

![초기 왼손 source 거리와 proxy 측정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_early_source_v1/artifacts/left_early_source_measurements.png)

초기 unsigned source-hull 0.545306 mm와 backend signed query 0.167218 mm는 처음부터 값이 다르며, 차이의 원인은 이 비교에서 판정하지 않았다. Unsigned source-hull 간격은 0.1초에 29.787930 mm로 커졌다. Backend signed query는 별개이며 0.1초 값 20.000 mm는 20 mm cutoff로 기록됐다. Normal-Z proxy는 0.926890→0.965232, 손 중심의 local neck lower section 대비 높이는 −24.728→−57.601 mm였다. Step 0 contact field는 `null`이며 뒤의 6개 완료-step 표본은 접촉 행이 없다. 이 값들은 초기 clearance, force, 지속 지지 또는 원인 판정이 아니다. 세부 표와 제한은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_early_source_v1/README.md), SHA는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_early_source_v1/artifacts/plot_manifest.json)에 기록했다.

### 그림 54. 저장 pose의 source geometry 재구성

![0초와 0.1초 native 저장 pose의 source triangles 및 witness overlay](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_early_source_v1/artifacts/left_early_source_geometry.png)

두 panel은 같은 camera/world bounds를 쓴 CPU source-triangle 재구성이지 native renderer가 아니다. 주황 witness 선과 점은 overlay annotation이며 clearance/depth 증거가 아니고, 화살표는 해부학적 방향 부호 미검증 normal proxy다. 상세 제한과 재생성 명령은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_early_source_v1/README.md), 산출물 provenance는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_early_source_v1/artifacts/plot_manifest.json)에 있다.

## 40. 승인된 세 가지 왼손 위치 제어의 0.1초 비교

2026-10-07, `palm_position_compare_v1`. 승인된 PI, RATE_PI, PALM_RATE 각 24 physics steps의 저장 query·trace·control 자료를 그렸다. 이 그림 제작에는 추가 native 실행이나 query가 없다.

### 그림 55. 손 위치 거리·기타 오차·팔 목표 변화

![PI, RATE_PI, PALM_RATE의 0.1초 saved comparison](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_position_compare_v1/artifacts/palm_position_compare.png)

PALM_RATE의 최대 source-center–goal 거리는 47.473935 mm로 RATE_PI의 48.835811 mm보다 1.361875 mm 작았다. 기타 위치/회전 trace는 세 조건에서 정확히 같아 그림에 동일 선으로 겹쳐 보인다(인위적 offset 없음). 세 조건의 24-step LH/RH contact 행은 모두 0이며, 이것은 지지력이나 안정성 성공을 증명하지 않는다. PALM_RATE의 마지막 위치-task 계산 잔차는 약 0.689 mm였지만 실제 source-center–goal 최대 거리는 47.473935 mm였다. 선형 계산 잔차와 실제 물리 응답을 구분하며 원인을 단정하지 않는다. 팔 목표 변화와 active-bound 갱신 count를 포함한 수치·제한은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_position_compare_v1/README.md), 입력·producer·출력 SHA는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_position_compare_v1/artifacts/plot_manifest.json)에 기록했다.

## 41. 왼손 위치 task의 0.5초 저장 비교

2026-10-07, `palm_position_half_second_v1`. 세 승인 mode의 120 physics-step states, queries, traces, controls를 요약했다. 이 그림 제작 과정에는 추가 native 실행이나 설정 변경이 없다.

### 그림 56. 0.5초 왼손 거리·기타 오차·팔 목표 변화

![0.5초 세 mode 저장 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_position_half_second_v1/artifacts/palm_position_half_second.png)

PALM_RATE의 source-center–goal 최대 거리는 90.540508 mm로 PI 115.511587/RATE_PI 115.675290 mm보다 작지만 큰 이탈이 남았다. 최대 기타 위치오차는 PI/RATE_PI/PALM_RATE 35.481594/35.690658/36.091149 mm였고 최대 회전오차는 4.991597/5.005785/4.761921°였다. 기타 상태의 mode별 차이는 raw 관측이며 그림은 offset 없이 표시했다. 1초 실행은 이 단계에 포함되지 않았다. contact 행, joint limit 기록, update target 정의와 한계는 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_position_half_second_v1/README.md), provenance는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_position_half_second_v1/artifacts/plot_manifest.json)에 기록했다.

## 42. 저장된 팔 목표와 실제 4-step 응답

2026-10-07, `palm_target_response_v1`. 저장된 0.5초 response JSON의 30개 갱신 창을 읽어 비교했다. 이 산출물 작성 과정에는 native 실행이나 설정 변경이 없다.

### 그림 57. 목표 좌표 차이와 측정된 source-center 이동 방향

![PI, RATE_PI, PALM_RATE의 목표 gap 및 4-step 실측 projection](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_target_response_v1/artifacts_final/palm_target_response.png)

최대 왼팔 scalar 좌표 차이는 PI/RATE_PI/PALM_RATE에서 21.038724/21.062126/21.462316°였고, 최대 오른팔 차이는 17.213643/17.228633/17.236607°였다. 이 값은 관절별 native 좌표 차이지 상대 회전각이나 토크가 아니다. 각 조건의 30개 창 중 29개 실제 4-step source-center 이동에서 초기 목표 복귀 방향의 반대 투영 성분이 있었고, 초기 창 투영은 원자료 그대로 undefined/null이다. 이는 구간 방향 관측이며 거리 단조 변화나 원인을 증명하지 않는다. 마지막 PALM_RATE 창은 정적 선형 목표 이동 177.530793 mm와 실제 이동 0.745714 mm, 복귀 방향 투영 −0.613600 mm로 구별된다. 정적 계산은 응답시간 예측이 아니며 실제 이동에는 전체 humanoid 움직임이 포함된다. 점 정의, 전체 표 및 한계는 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_target_response_v1/README.md), 입력과 출력 provenance는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_target_response_v1/artifacts_final/plot_manifest.json)에 기록했다.

## 43. PALM_RATE 두 어깨의 DOF force sensor 관측

2026-10-07, `dof_force_observation_v1`. 보존된 성공 attempt_v2의 120개 완료-step 센서 값과 target–actual scalar gap을 그렸다. artifact 생성 중 추가 native 실행은 없다.

### 그림 58. 두 어깨 총 DOF force와 완료-step 좌표 차이

![L_Shoulder_x와 R_Shoulder_z의 force 관측 및 scalar gap](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dof_force_observation_v1/artifacts/dof_force_observation.png)

L_Shoulder_x 총 DOF force의 signed 최소/최대는 −14.536089/+0.112701 Nm, R_Shoulder_z는 −1.187056/+5.564084 Nm였으며 두 절댓값 최대 모두 step1에서 나왔다. 완료-step scalar gap의 최대/최종은 각각21.619762°와17.266792°였다. Step0 센서 측정은 없고 첫 점은 step1이다. 105개 native DOF 모두 회전형 type code 1/Nm로 기록됐다. 이 센서 총힘은 actuator-only 토크나 접촉력·포화·PD 원인으로 해석하지 않으며, 120개 nonzero sample은 관측일 뿐 gate가 아니다. 기타/손 오차는 이전 결과 그대로 유지 실패가 남는다. 실패 attempt와 v2 성공, 단위·시점·한계는 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dof_force_observation_v1/README.md), 입력/출력 provenance는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dof_force_observation_v1/artifacts/plot_manifest.json)에 기록했다. 어깨 stiffness 변경은 별도 제안이며 아직 확인·실행되지 않았다.

## 44. Native 저장 목표 readback의 24-step 관측

2026-10-07, `native_target_readback_v1`. 기존 PALM_RATE 0.1초 실행에서 step 전·후 native 저장 목표 getter 48회를 기록했다. 이 그림은 저장 기록만 읽었으며 추가 native 실행은 없다.

### 그림 59. L_Shoulder_x target readback과 105축 차이

![제출 목표와 native 저장 목표, 105축 전체 max difference](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/native_target_readback_v1/artifacts_validated/native_target_readback.png)

현재 원자료에서 제출 목표와 `L_Shoulder_x` native 저장 목표는 48개 실제 getter read에서 겹치고, 105축 전체 최대 차이는 0 rad로 계산됐다. Before/after reads는 같은 physics time의 중복 x값을 순서대로 보이며, 초기 step0 before read도 실제 측정값이다. 이 짧은 구간의 readback 일치는 액추에이터/PD 원인 또는 후기 기타 유지 성공을 증명하지 않는다. 7개 기존 배열과 24-step 범위의 검사는 통과했으며, 조건·시점·입력 provenance는 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/native_target_readback_v1/README.md) 및 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/native_target_readback_v1/artifacts_validated/plot_manifest.json)에 기록했다.

## 45. PALM_RATE 초기 strap law 0/1/2 N의 0.5초 저장 trace

2026-10-07, `palm_preload_v1`. 0.5초 0/1/2 N 초기법칙 비교의 실제 trace 121시점을 그렸다. 산출 과정에는 추가 native 실행이 없다.

### 그림 60. 기타 오차와 baseline 대비 signed scalar 차이

![0.5초 preload 위치/회전오차와 0N 대비 차이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_preload_v1/artifacts/palm_preload_hold.png)

0.5초 위치/회전 최대오차는 0/1/2 N에서 36.091149/36.077130/36.087686 mm와 4.761921/4.757473/4.770926°였다. 1 N의 최대오차 차이는−0.014019 mm/−0.004448°로 작았고 LH source 이탈은 0.003779 mm 더 컸다. 작은 tradeoff일 뿐 통계적 유의성, 안정후보 또는 채택 근거가 아니다. 아래 panel은 오차 scalar 간 pointwise 차이며 이동 벡터나 controller 보정이 아니다. 0/1/2 N은 초기 strap law label이고 runtime 장력 고정값이 아니다. 상세 6행 비교, 적용장력, 접촉표 한계와 재생성 정보는 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_preload_v1/README.md), source와 PNG hash는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_preload_v1/artifacts/plot_manifest.json)에 기록했다. 1초는 측정하지 않았고 기존 0 N 진단 기준과 PD를 유지한다.

## 46. Shoulder stiffness 200→300의 0.5초 저장 trace

2026-10-07, `shoulder_pd_compare_v1`. 네 fresh rollout 중 두 stiffness의 저장된 0.5초 trace와 완료-state L_Shoulder_x scalar gap을 그렸다. 산출 과정에는 추가 native 실행이 없다.

### 그림 61. 기타 오차·LH source 이탈·L_Shoulder_x 목표 차이

![Shoulder 200/300 saved trace 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_pd_compare_v1/artifacts_v3/shoulder_pd_hold_05s.png)

stiffness 300의 0.5초 최대 기타 위치/회전오차는 200보다 0.311118 mm/0.211380° 작았지만, 종료 위치오차는 1.006964 mm 더 컸고 LH source 이탈도 0.944862 mm 더 컸다. L_Shoulder_x/R_Shoulder_z scalar gap과 실제 arm scalar 한계위반은 증가했다. LH contact는 0행, RH contact 행은 135→100으로 관찰됐으나 행 수는 힘·지속 지지·인과 증거가 아니다. stiffness 300은 채택하지 않고 기준 200을 유지하며 1초 결과는 미측정이다. 표·해석·재현은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_pd_compare_v1/README.md), 최신 plot provenance는 [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/shoulder_pd_compare_v1/artifacts_v3/shoulder_pd_hold_05s.manifest.json)에 기록했다.

## 47. 원본·현재 CPU 진단의 nominal PD 경로 대조

2026-10-07, `pd_actuation_paths_v1`. 105축 감사값과 실제 source/API 문서의 정적 경로만 그림으로 옮겼다. native 초기화와 physics step은 모두 0이다.

### 그림 62. Explicit force-tensor와 position-target 경로

![원본 explicit force와 현재 position-target 경로](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1/artifacts/pd_actuation_paths.png)

105축의 Fret/Strike/Main66/Torso9 nominal kp/kd/cap 숫자는 저장 native200 property와 일치했지만 경로는 다르다. 원본은 POS stiffness0·solver damping과 함께 explicit clipped `kp(target−q)` force tensor를 제출하며 설치 문서는 tensor force가 EFFORT mode에만 적용된다고 설명한다. Runtime 응답은 검증하지 않았으므로 원본 torque가 무시됐다거나 오류라는 판정은 없다. 현재 팔은 solver position target 경로다. 그림의 표는 105행 JSON에서 읽은 값이고 물리 rollout 결과가 아니다. source links, 수치 그룹과 한계는 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1/README.md), 입력·producer·출력 SHA는 [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pd_actuation_paths_v1/artifacts/pd_actuation_paths.manifest.json)에 기록했다.

## 48. 승인된 단일 hinge POS/EFFORT torque fixture 관측

2026-10-07, `tensor_effort_api_v1`. 저장된 CPU PhysX single-hinge trace 6개, 각 24-step의 25개 상태를 그렸다. 그림 생성에서는 native 초기화와 physics step을 추가하지 않았다.

### 그림 63. Native hinge q와 angular velocity

![L_Shoulder_x fixture의 POS/EFFORT × 0/±1 Nm](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/artifacts_final_v2/tensor_effort_api.png)

EFFORT의 ±1 Nm에서는 약 ±0.00197642 rad과 ±0.00023759 rad/s의 종료 변화가 관측됐고, POS의 ±1 Nm는 25개 q/velocity 상태가 각 mode의 0 Nm 기준과 정확히 같았다. POS trace는 0선에 겹치며 인위적 offset을 주지 않았다. 각 API 제출은 accepted였고 contact 행은 없었다. 로그에는 여섯 fixture 시작 때 CUDA device 탐색 오류가 기록됐지만 CPU PhysX 실행은 모두 완료됐다. Native property readback은 두 mode 모두 `hasLimits=false`, lower=upper=0이며 `initial_within_limits`는 비활성 native 제한의 lower/upper 수치에서 통과한 검사이며 native limit 인증이 아니다. 초기 q=0과 저장된 모든 q가 source authored ±90° 안에 있음은 별도 XML·상태 대조로 확인했다. 이 isolated CPU positive-control 결과는 원본 GPU나 humanoid actuator 동등성, 구동 실패 원인 또는 기타 안정화 성공을 증명하지 않는다. 표·fixture 조건·한계는 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/README.md), 최신 그림 provenance는 [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/tensor_effort_api_v1/artifacts_final_v2/tensor_effort_api.manifest.json)에 기록했다.

저장 EFFORT +1Nm의 마지막 구간 Δq/Δt는 0.01976547763rad/s, SDK 완료-step velocity는
0.0002375884214rad/s로 달랐다. 구간 평균과 완료시점 측정은 서로 다른 양이며 원인/단위
오류를 단정하지 않는다. 이후 torque-PD 감쇠·velocity feedback은 별도 검증한다.

## 49. 기존 최선 실행의 시작부터 종료까지 source-geometry 재생

2026-10-07, `best_run_video_v1`. 기존 54개 1초 이상 저장 실행에서 최대 기타 위치·회전 오차가 함께 가장 작은 run의 241개 native 저장 자세를 모두 재생했다. 이 재생 과정에서는 native simulation이나 physics step을 추가하지 않았다.

### 그림 64. 시작·중간·종료 미리보기

![저장된 native 자세의 source geometry 재생 미리보기](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/render_v2/images/preview_step_120.png)

전신과 기타, 손과 넥 확대 화면을 나란히 배치했다. 인체는 회색, 기타는 파랑, 왼손은 초록, 오른손은 자홍색이며 주황색 선은 해당 trace에 저장된 strap route다. 영상은 source collision geometry 재구성으로 PhysX 렌더가 아니다. 0.25배속 60 fps 전체 영상은 [여기](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/render_v2/videos/best_run_slow_0p25x.mp4), 실시간 240 fps 영상은 [여기](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/render_v2/videos/best_run_realtime_1x.mp4)에서 확인할 수 있다.

선택 기준상 최대 오차는 73.268255 mm와 13.439339°였지만 `stability_success`는 false이며 종료 시에도 선속도 0.293 m/s, 각속도 1.192 rad/s로 움직임이 남았다. 후보 동작의 가시화이지 안정성·연주 성공 판정이 아니다. 전체 조건과 재현 경로는 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/README.md), frame·asset·producer provenance는 [render manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/render_v2/render_manifest.json)에 있다. [최종 독립 검토](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/review.md:7)는 완료됐고 남은 지적사항이 없다.

## 50. 하체 물리 고정 조건의 1초 기타 재생

2026-10-07, `lower_body_fixed_v1`. 오른발 자세 자체를 바꾸지 않고, 이전 최선 실행의 초기 링크 자세에서 하체 관절을 제거한 물리 고정 조건으로 새 1초 run을 실행했다. 이 단계는 그 저장된 241개 상태를 source collision geometry로 재생하며, 재생 중 native simulation 또는 physics step은 추가하지 않았다.

### 그림 65. 하체 고정 조건의 중간 저장 자세

![하체 고정 run의 중간 시점 source-geometry 재생](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/images/preview_step_120.png)

전신·기타와 손·넥 확대를 동시에 표시한다. source collision geometry 재구성이므로 PhysX 렌더나 cooked clearance 인증이 아니다. 8개 하체 링크의 저장된 전체 pose와 선·각속도는 run 전체에서 동일했다. quaternion 비교의 `acos` 잔차 최대는 0.000002415°다. 기타의 1초 최대·종료 오차는 149.372986 mm / 62.331933°, 종료 속도는 0.892343 m/s와 3.413599 rad/s였다. 이 값은 이전 동적 하체 기준 73.268255 mm / 13.439339°보다 나쁘다. 따라서 하체를 고정한 사용자 요청 조건의 관찰 결과이지 안정성·연주 성공이나 오른발 원인 확인이 아니다. 숫자와 한계는 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/README.md), 영상은 [0.25배속](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/videos/best_run_slow_0p25x.mp4) 및 [실시간](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/videos/best_run_realtime_1x.mp4), 재생 provenance는 [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/render_manifest.json)에 기록했다. 첫 제작본은 [render_v1/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v1/)에 보존했으며, report의 null과 불일치하는 footer 때문에 archive-only다. 최종 `render_v2` footer는 “Stability success not certified”다. 이전 manifest의 경로 변경은 [relocation 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v1/relocation_manifest.json)에 별도 보존했다. [최종 독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/review.md:7)는 완료했고 남은 finding이 없다.

## 51. 양손 source convex hull 교차 여부

2026-10-07, `hand_hand_collision_audit_v1`. 사용자가 본 손 겹침이 실제 저장 pose의 형상 교차인지 확인했다. 독립 LP는 5개 대표 시점 중 0.5초·0.670833초·1초에서 source convex hull 교차를 확인했으며 0초와 0.058333초에서는 교차 쌍을 찾지 못했다.

### 그림 66. 0.5초 저장 pose의 양손

![초록색 왼손과 자홍색 오른손의 source geometry preview](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_fixed_v1/render_v2/images/preview_step_120.png)

0.5초 표본에서는 289개의 shape pair 중 18쌍이 공통 convex-hull 내부구 검증을 통과했다. 0.670833초의 `LH:pinky3`–`RH:palm` 쌍은 공통 내부구 반지름 6.642477 mm로 확인됐으며 관통 깊이는 아니다. 0.1 m signed query의 첫 음수(step 14, −0.193690 mm)는 cutoff artifact 가능성이 있고 같은 표본 LP 교차는 0쌍이므로 교차 onset으로 읽지 않는다. 전체 1초의 완료 240 step 접촉 기록에서 왼손–오른손 사이 contact 행은 0이고 모든 양손 shape pair가 shared exclusion bit를 가져 native 충돌 처리에서 제외된다. 이는 source convex hull 교차와 모순되지 않는다. contact 행은 반력 측정값이 아니다.

이 감사는 source convex hull 및 capsule 다각형 근사이며 PhysX cooked geometry, 침투 깊이, 힘, 연속 구간의 시작 시점을 인증하지 않는다. 원자료와 LP 결과는 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_hand_collision_audit_v1/README.md), [원 signed-query/native filter report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_hand_collision_audit_v1/report.json), [대표 프레임 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_hand_collision_audit_v1/hull_verification.json)에 기록했다. [최종 독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hand_hand_collision_audit_v1/review.md:7)는 완료했고 남은 finding이 없다.

## 52. 허벅지·왼손 초기 접근 후보의 짧은 저장 pose 재생

2026-10-07, `thigh_palm_support_v1`. 다섯 개의 기존 0.1초 native 결과 중 초기 source gap이 가장 가까운 `clear_2um`의 25개 저장 pose를 재생했다. 새 native 초기화와 physics step은 0이다.

### 그림 67. 시작 투영 witness와 종료 자세

![2D witness overlay가 표시된 초기 source-geometry 자세](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/render_v2/images/initial_annotated.png)

주황색과 파란색 표식은 기존 witness를 MuJoCo camera에 투영한 설명 overlay로, geometry 가림을 무시하고 표시하며 원 크기는 거리 척도가 아니다. R_Hip의 기타 점은 baseline witness에 후보 생성 이동만 적용한 참고점이고, 손바닥–넥 점은 후보의 초기 source hull witness다. 새 clearance나 native 접촉을 뜻하지 않는다. 종료 frame, 위치·회전 trace, 전체 25-frame 느린 재생은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/README.md)와 [render_v2 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/render_v2/videos/clear_2um_saved_pose_0p05x.mp4)에서 볼 수 있다.

`clear_2um`의 초기 unsigned source hull gap은 1.896279 µm였지만 native LH:palm contact 행은 24개 완료 step 모두 0이었다. source gap은 step 1에서 0.212747 mm, step 24에서 38.065514 mm로 벌어졌다. 기타 최대 오차는 4.041302 mm / 0.641189°였고 기준은 2.279551 mm / 0.997176°였다. 마지막 source sample의 손 사이 hull 교차도 남아 이 후보를 지속 지지 자세로 채택하지 않았다. 그림은 저장 native pose를 source geometry로 재구성한 것이며 PhysX 렌더·cooked clearance·접촉력 인증이 아니다.

실행 직전 producer 사본, 116개 입력 경로 SHA와 실제 종료 시 재계산한 값, ffprobe 결과는 [v2 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/render_v2/render_manifest.json)와 [실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/render_execution_v2.json)에 있다. 이전 media와 manifest는 [render_v1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/render_v1/render_manifest.json)에 보존했다. v1 producer 원문 사본은 없어 manifest에 남은 당시 SHA만 식별자로 유지한다. [최종 독립 검토](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/thigh_palm_support_v1/review.md:7)는 완료됐고 남은 지적사항이 없다.

## 53. Humanoid self-collision OFF/ON의 source-geometry 재생

2026-10-07, `self_collision_v1`. 같은 초기 상태의 저장된 OFF/ON 실행을 비교했고, ON의 25개 saved pose를 재생 영상으로 만들었다. 이 그림·영상 생성에 추가 native 초기화와 physics step은 없다.

### 그림 68. ON 초기 pose와 step 24 손 확대 비교

![ON 초기 pose의 source-geometry 전신 및 손 확대](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/render_v2/images/initial_on.png)

![OFF/ON 완료 step 24 손 확대와 raw 접촉 기록 행 수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/render_v2/images/off_on_hands_step_024.png)

ON에는 같은 `LH:palm`–`RH:index1` body pair의 native self-contact 기록 9행이 step 20–24에 남았고, raw `lambda`는 6행에서 양수였다. 이는 9개의 별도 충돌 이벤트나 교정된 힘 단위가 아니다. 초기 step-0 contact query는 사용할 수 없고, 이 contact 행으로 지속 지지·침투 깊이·원인을 추론하지 않는다. ON mask는 일부 비인접 human pair와 양손 상호작용을 허용하면서 같은 손 내부와 연결부의 importer 제외를 유지한다. 그림은 source geometry를 재생한 것으로 PhysX 렌더나 cooked collider 인증이 아니다.

[전체 저장 pose 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/render_v2/videos/self_collision_on_saved_poses_0p05x.mp4)은 25 frame, 0.05배속 12 fps다. OFF/ON의 최대 기타 오차는 각각 4.041302/4.035079 mm와 0.641189/0.639349°였고, LH:palm–기타 contact는 둘 다 0이다. 작은 오차 차이는 기타 안정화 성공으로 판정되지 않는다. 원자료와 mask 범위는 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/README.md), asset/helper/raw/output provenance는 [canonical manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/render_v2/render_manifest.json), 변경 경로는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/CHANGED_FILES.md:1)에 있다. [최종 독립 검토](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/self_collision_v1/review.md:7)는 완료됐고 남은 지적사항이 없다.

## 54. Isaac Gym native camera 초기 시점

2026-10-07, `isaac_gym_camera_v1`. 앞 절은 저장된 native pose를 MuJoCo source geometry로 재구성한 결과였고, 이번 PNG는 Isaac Gym camera sensor가 직접 저장했다.

### 그림 69. Native camera의 초기 전신·손 장면

![Isaac Gym native camera 전신 시야, physics step 0](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/front/whole_body.png)

![Isaac Gym native camera의 손 visual geometry, physics step 0](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/front/hands.png)

두 이미지는 초기 step 0이며 캡처 중 physics step은 0이다. strap은 native scene에 렌더 형상이 없어 표시되지 않는다. 이 자료는 접촉력, 충돌 성공, cooked geometry 또는 안정성 인증이 아니다. `hands_collision.png`는 저장됐지만 hands visual image와 byte-identical하여 별도 collision geometry 장면은 확인되지 않았다.

로그에는 PhysX CPU device와 GPU pipeline 비활성화가 기록됐다. `graphics_device_id=0`은 GPU 실행이나 Lavapipe 사용을 뜻하지 않으며 Vulkan backend는 확인되지 않았다. `front/capture.json`의 73개 입력과 3개 PNG SHA는 일치하고 capture checks 및 mask audit도 통과했다. 자세한 경고·제한은 [결과 안내](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/README.md), 실제 경로는 [변경 파일 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/CHANGED_FILES.md:1)에 있다. [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/review.md:9)는 완료됐고 남은 지적사항은 없다.

## 55. 왼손 finger seed, preload, palm feedback의 저장 결과

2026-10-07, `finger_grip_hold_v1`. 0.1/0.5/1초 native trace의 기타 오차를 비교했다. 이후 Isaac Gym native camera run을 포함해 79회 native initialization / 1,872 physics steps가 기록됐다. 아래 figure 생성과 영상 post-processing에서는 physics step을 추가하지 않았다.

### 그림 70. 저장 기타 오차: 0.5초와 1초 비교

![0.5초 baseline·seed/preload 및 feedback, 1초 baseline·feedback·cap 0.30 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/artifacts_feedback_v2/guitar_error_feedback_hold.png)

0.5초 palm-feedback `v2` 최대오차는 16.170221 mm / 2.379811°였고 baseline은 18.740199 mm / 2.842119°였다. 같은 0.5초의 seed/preload/hold 조합은 26.522614 mm / 3.497190°였다. 0.5초 feedback v2의 206 contact rows는 step 14–120 범위에 있지만 중간 소실 구간이 있다. 기록된 LH–기타 pair는 fret10/middle3, fret11/ring3 및 기타 root body/ring3였고, 반대 엄지 또는 LH:palm 접촉은 없다. 1초 `v2`는 최대 16.170221 mm / 2.517144°, 종료 15.322712 mm / 2.488597°로 baseline 20.341143 mm / 5.282789°보다 작지만, 목표 유지 성공으로 판정하지 않는다. 0.30-rad cap은 같은 최대오차와 LH 접촉 마지막 step을 보이고 종료값만 15.240242 mm / 2.454898°로 약간 낮아 cap 확대를 채택하지 않았다. 초기 기타 target은 base Z +5 mm와 기존 회전에 near2 µm 접근 보정 translation (−0.415437, +0.012261, −1.026976) mm을 적용한 위치였고, 모든 비교에서 같은 p/q target을 썼다. finger seed와 arm preload, palm/world feedback은 함께 바뀐 조건이므로 효과를 finger seed 하나로 분리할 수 없다.

### 그림 71. 선택한 1초 run의 native camera frame montage

![Isaac Gym native camera 전신과 손 장면, t=0, 0.2, 0.533, 1.0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/native_video/render_v2/native_camera_montage.png)

[전체 native camera 영상은 0.2×, 12 fps로 재생한다.](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/native_video/render_v2/finger_grip_hold_0p2x.mp4) 원 camera frame은 0–240 physics step에서 4 step 간격으로 61회 저장했다. 캡처용 native run의 states/trace/contacts/controls/leg-torques 자료는 선택한 1초 `seed120_palm_feedback_v2` raw와 일치한다. 그림·영상은 Isaac Gym visual-camera 출력이며 MuJoCo source replay가 아니다. 실행은 CPU PhysX, graphics device id 0였고 graphics backend identity는 조회되지 않았다.

1초 `v2` LH–기타 contact row는 step 131 (0.545833 s)까지 있고 이후에는 없다. 양의 raw lambda는 step 130 (0.541667 s)까지 관측됐다. 이는 force/support 인증이 아니다. native `LH:palm` link 원점의 최대 world displacement는 31.381602 mm였고 종료 Z 변화는 −31.052768 mm였다. torso 최대 actual drift는 3.899911°다. palm-up proxy 최소값 0.927708은 관측치이며 해부학적 방향 검증이 아니다. 0.30-rad cap의 native raw LH contact window도 같은 step에서 끝났고 종료 기타오차 감소는 0.08247 mm / 0.03370°뿐이어서 채택하지 않았다. 이어갈 검토는 엄지의 반대 방향 접촉과 상체 목표 drift이며, 이 자료는 안정화·연주 성공을 인증하지 않는다.

0.1초 feedback-prefix 수치는 anti-windup 수정 전 `short/seed120_palm_feedback` raw에 해당하며, 별도의 feedback-v2 short run은 없다. state/trace prefix는 0.5초 feedback-v2 run과 일치한다. `contact005`는 위치오차 3.048302 mm로 낮고 회전오차 0.733724°로 커지는 tradeoff라 연장하지 않았다. contact row는 분리된 저장 접촉 관측이며 연속 접촉, 지지력, 인과를 의미하지 않는다. table, 재현 provenance, raw links는 [phase README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/README.md), input·output SHA와 실제 경로는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/CHANGED_FILES.md)에 정리했다.

## 56. 파란 기타 neck 측면 target과 왼손 palm의 저장 camera 비교

2026-10-07. 파란 기타 neck의 아래 측면에 왼손 palm이 닿도록 한 배치의 저장 camera 비교다. 그림 생성 자체에는 native 실행을 추가하지 않았다. Cyan 다각형은 probe에 기록된 world-space target polygon을 저장 camera의 eye/target 및 FOV로 2D에 투영한 설명 overlay이며, 가려진 면도 표시할 수 있다. 그림은 native camera 장면 위에 추가된 표시이지 별도의 geometry render가 아니다.

### 그림 72. Front camera: baseline, target 초기 배치, 첫 native contact, 0.1초

![Front camera 네 시점의 파란 neck target overlay. 첫 step panel의 네 빨간 표식은 raw contact 좌표 투영.](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/artifacts/comparison_front.png)

### 그림 73. Side camera: 같은 저장 시점과 target

![Side camera의 baseline 및 새 배치 step 0, step 1, step 24.](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/artifacts/comparison_side.png)

첫 physics step에서 LH:palm–guitar contact 4점이 기록됐지만 lambda는 모두 0이다. 0.1초 종료에는 palm contact가 없고 기타 오차는 5.107730 mm / 0.969008°다. 따라서 초기 접촉 관측은 지속 지지나 안정성 성공을 뜻하지 않는다. 카메라는 Isaac Gym native CPU PhysX scene이며 GPU pipeline은 비활성화됐다; graphics backend identity는 알 수 없고 strap 형상은 나타나지 않는다. 상세 표, 개별 이미지, projection 식과 제한은 [phase README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/README.md), 실제 경로·SHA는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/CHANGED_FILES.md)에 있다.

## 57. 파란 측면 palm 추적의 초기·단기 응답

2026-10-07. 초기 source 간격을 좁힌 뒤 OFF, startup bias, bias+tracking을 각각 0.1초 저장 실행으로 비교했다. 세 조건 모두 첫 completed step에서만 LH:palm–guitar contact 4행이 기록됐고 raw `lambda`는 모두 0이며, step 2–24에는 해당 contact 행이 없다. 추적점 최대오차는 71.909699→49.465670→48.323668 mm로 줄었지만 종료에도 약 48.3 mm가 남고, 기타 최대오차는 각 조건에서 5.107730 mm / 0.969008°로 같다. 이 결과는 지속 지지나 기타 안정화 성공이 아니다.

### 그림 74. 손 추적점과 기타 위치·회전 오차

![저장 trace의 손 추적점 및 기타 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1/artifacts/palm_side_feedback_metrics.png)

### 그림 75. 저장 native camera frame 비교

![이전 fixed-target와 신규 tracking 실행의 native camera 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1/artifacts/palm_side_feedback_camera_comparison.png)

청록 다각형은 각 camera frame의 `target_polygon_W_m`를 해당 카메라 사양으로 투영한 설명 overlay이고, 주황 점은 source palmar-facet local point를 같은 시점의 native LH:palm 자세로 변환해 투영한 점이다. 두 표시 모두 cooked surface 접촉점이나 압력 중심이 아니다. step 1 접촉 정보는 raw로만 보고했으며 다른 시점의 화면에 투영하지 않았다. 상세 결과와 한계는 [phase README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1/README.md), 파일·SHA 경로는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1/CHANGED_FILES.md)에 있다.

## 58. 저장 native pose의 손바닥 source 평면 정렬

`validated/measurements.json`의 25개 샘플/조건을 이용해 source facet 법선 대향각, signed source point-to-plane 간격, target patch 중심까지의 접선 거리를 표시했다. Tracking 종료에서 이 값들은 각각 4.750409°, 40.495078 mm, 26.445653 mm였다. 초기 signed 간격은 0.050075 mm이며 과거 hull–patch 최소 거리와 다른 측정이다. 이는 source pose 기하 관측이지 cooked 접촉이나 접촉력 측정이 아니다.

### 그림 76. OFF·bias·tracking의 평면 정렬 지표

![저장된 source 평면 정렬 지표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/artifacts/palm_plane_alignment.png)

법선 대향각은 전체 SO(3) 방향 오차가 아니다. 가까운 평행 평면만으로 접촉을 보장할 수 없으며, 면의 반대 방향 outward normal과 법선 gap 및 finite patch 내 위치를 함께 고려하는 설계안을 검토할 수 있다. 기존 제어기는 초기 상대 회전을 유지하고 normal-only controller는 구현·시험되지 않았다. 원자료와 설계 설명은 [phase README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/README.md), 입력·출력 SHA와 실행 경로는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/CHANGED_FILES.md)에 정리했다.

## 59. Palm normal-only 짧은 제어 비교

Full 0.15, Normal 0.15, Normal 0.30, Normal 0.50의 0.1초 저장 trace를 비교했다. Normal 0.30은 종료 법선각 1.280689°와 접선 거리 2.989581 mm, Normal 0.50은 손 추적점 최대오차 11.963341 mm로 각각 작은 값을 보였지만 palm contact 행의 raw lambda는 모두 0이고 기타 오차는 네 조건에서 같다. 첫-step cap 응답은 실제 추적점 오차가 예측값보다 훨씬 커 startup 선형 예측이 맞지 않았다. 지속 지지나 안정성 성공을 뜻하지 않는다.

### 그림 77. 저장 손·법선·기타 오차 곡선

![네 조건의 저장 trace 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/artifacts/palm_normal_control_curves.png)

### 그림 78. 이전 Full 조건과 Normal 0.30의 저장 native camera 비교

![front/side 시점의 기존 native camera frame 및 source overlay](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/artifacts/palm_normal_control_camera.png)

두 그림은 저장 자료만 시각화했다. 카메라 비교의 source facet 표식은 각 이미지와 같은 시점의 palm 자세를 사용하며 cooked contact 위치나 압력 중심이 아니다. 상세 표와 제한은 [phase README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/README.md), 입력·출력 경로는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/CHANGED_FILES.md)에 있다.

## 60. Palm support-weight 저장 trace 비교

0.08, 0.02, 0 m/rad의 orientation scale을 비교했다. 0에서 source 추적점 오차와 법선각이 커졌고 기타 위치·회전 오차는 세 조건에서 동일했다. Contact 행은 모두 raw lambda 0이므로 추가 contact 행을 지지력이나 하중으로 보지 않는다.

### 그림 79. 손 추적점·source 법선각·기타 오차

![세 orientation scale 조건의 저장 trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/artifacts/palm_support_weight.png)

법선각 곡선은 scale 0 조건도 같은 0.08 m/rad로 환산해 그렸다. 표와 해석은 [phase README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/README.md), 실행 및 SHA 인덱스는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_weight_v1/CHANGED_FILES.md)에 있다.

## 61. Palm-side strap 길이·초기 tension-law 비교

0.1초 저장 비교에서 10 N 초기-law 조건은 기타 최대오차가 가장 작았지만, 첫-step 기타 오차가 더 컸고 palm 접촉의 양의 raw lambda는 한 행뿐이었다. 0.1초에서 지속 지지나 안정화 성공으로 판정하지 않는다.

### 그림 80. 기타 오차, PRESTEP strap tension, 손 추적점

![네 rest-length/initial-law 조건의 저장 curve](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/artifacts/palm_side_strap_curves.png)

### 그림 81. 10 N 초기-law 실행의 저장 native camera frame

![physics step 0·24의 front/side camera view와 source overlay](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/artifacts/palm_side_strap_camera.png)

카메라 그림은 기존 capture를 재사용했다. 청록 target과 주황 source facet 표시는 저장된 같은 시점의 pose를 보여주며 cooked 접촉점이나 압력 중심이 아니다. 표·제한은 [phase README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/README.md), 입력·출력 SHA와 실행 정보는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_v1/CHANGED_FILES.md)에 정리했다.

## 62. Palm-side strap 0.5초 저장 비교

네 strap 조건의 0.5초 저장 결과다. 0.1초에서 보인 작은 기타 오차는 유지되지 않았다. Contact 행은 초기 몇 step에만 관측됐고 raw lambda만으로 지속 지지를 말하지 않는다.

### 그림 82. 기타 오차, PRESTEP 장력, 손 추적점 오차

![네 strap 조건의 0.5초 기타 p/q·tension·palm 추적점 저장 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/artifacts/palm_side_strap_long_curves.png)

### 그림 83. Current 조건의 native camera step 0/120

![front/side view의 저장 camera frame과 source overlay](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/artifacts/palm_side_strap_long_camera.png)

기존 31개 native frame으로 만든 [60 fps 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/artifacts/palm_side_strap_long_realtime.mp4)과 [6 fps 느린 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/artifacts/palm_side_strap_long_slow.mp4)은 저장된 장면만 재생한다. [표·한계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/README.md)와 [입력·출력 SHA 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_strap_long_v1/CHANGED_FILES.md)를 함께 확인한다.

## 63. 손바닥 지지를 위한 0.1초 팔 목표 응답

평행에 가까운 방향은 선호이며 실제 손바닥 지지와 기타 초기 위치·회전 유지가 우선이다.
같은 초기각·기타·절대 LA·PD에서 팔 목표각만 바꿨다. 전체 보정은 손 추적점 오차를
14.208→6.671mm로 줄였지만 기타 오차는5.108mm/.969°→8.219mm/1.292°로 커졌다.
양의 palm raw lambda는step1–4에만 나타났고 접촉은step8 이후 없어 지속지지는 아니다.

### 그림 84. Constant bias 기준과 1/4·1/2·전체 보정

![0.1초 constant-bias 손과 기타 오차 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/artifacts/palm_finite_response_constant.png)

### 그림 85. 기존 tracking PI의 기준과 1/4 bias 보정

![0.1초 tracking의 bias만 바꾼 분리 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/artifacts/palm_finite_response_tracking.png)

새 유한시간 응답 B를 feedback에 넣은 시험이 아니다. 1/4 tracking의 종료point오차는
12.187→9.712mm로 줄지만 source normal gap9.524mm/palm raw lambda0/후기접촉 소실이
남는다. 기타 차이 약.0146mm/.00045°만으로 유지 성능이 좋아졌다고 인증하지 않는다.

### 그림 86. 전체 constant 보정의 실제 Isaac Gym 초기/0.1초

![실제 Gym front·side camera의 step0과24, 전체 보정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/artifacts/palm_finite_response_camera_corrected_bias.png)

### 그림 87. 1/4 tracking 보정의 실제 Isaac Gym 초기/0.1초

![실제 Gym front·side camera의 step0과24, 1/4 tracking](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/artifacts/palm_finite_response_camera_quarter_tracking.png)

위행은 초기, 아래행은0.1초며 왼쪽front/오른쪽side다. 청록은 선택된 넥 source 목표면,
주황점은 손바닥 source facet 추적점이다. 청록 overlay는 손에 가려진 영역도 표시하며
그림에서 겹쳐 보이는 것만으로 물리 접촉을 판정하지 않는다. 두 카메라는 기록된PD명령을
실제Gym물리에서 재실행했고 headless5raw와exact다. pose 덮어쓰기/손부착은 없다.
source면은cooked 접촉·압력 인증이 아니며 평행성 자체로 지지 성공을 판정하지 않는다.
[수치·해석·한계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/README.md),
[절대경로·실제줄번호·원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1/CHANGED_FILES.md)를 함께 확인한다.

## 64. 손바닥 접촉 경계에서 기타 응답 비교

같은 초기 자세·기타·절대LA·PD에서 왼팔 목표 bias의 배율만 바꿨다.
새4조건4init96steps와 이전2조건 저장자료를 비교했다. alpha.40→.45에서
기타 최대 오차는5.048mm/.967°→5.341mm/1.006°로 커지고 양의 palm raw lambda는
없음→step2 두 행으로 바뀌었다. 이는 표본 경계이며 유일한 임계값이나 지속지지가 아니다.

### 그림 88. 기타 오차·손바닥 source 간격·접촉 반응

![저장된 Isaac Gym 원자료의 여섯 조건 비교 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/artifacts_validated/palm_contact_boundary.png)

위는 설정 초기 목표 대비 기타 위치·회전 오차, 아래는 source normal gap과
step별 최대 palm raw lambda다. 점선은 native 실제t0 기준의 drift이며 설정 목표와
float32 readback의 작은 차이를 분리했다. 저장 원자료의 과학 그래프이며 camera 이미지가 아니다.
source gap은 cooked clearance가 아니고 raw lambda를 N으로 환산하지 않았다.
[측정표·한계·재생성](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1/README.md)를 따른다.

## 65. 접촉 구간에서 관절별 손·기타 응답 측정

alpha.45 기준에서 왼팔12 목표각을 각각+.005rad 바꾸고, 독립 조합+.001rad를
비교했다. 초기 자세·기타·절대LA·PD·몸통9/다른 관절 목표는 동일하다.14init336steps며
기준5배열은 이전.45와exact, report는 새경로 metadata가 달라 실행계약을 따로 검증했다.

### 그림 89. 단일 관절 목표 변화와 손·기타 오차

![Isaac Gym 저장 원자료의 관절별 손 위치·기타 위치와 회전 및 독립 조합 예측 차이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/artifacts/palm_coupled_response.png)

왼위는 종료 손 추적점 오차, 오른위/왼아래는 전체 .1초 기타 최대 위치/회전 오차다.
점그래프의 세로축은 작은 차이를 보도록 관측 구간을 확대했다. 파란점은 단일 관절
probe, 회색은 기준, 주황은 독립 조합이다. 오른아래는 종료 선형 예측과 실제 차이다.
손 위치.030036mm/법선회전벡터.002525°, 기타 위치.024734mm/world회전벡터.003647°다.
허용오차나 성공기준이 아니다. 저장된 native 원자료의 과학 그래프이며 camera 장면이 아니다.

L_Thorax_x와L_Shoulder_y의작은보정은손위치와기타오차를함께줄였다. L_Elbow_y는
기타5.341mm/1.006°→5.061mm/.967°로줄지만양의palm raw lambda가사라진다.
나머지조건도양의palm raw lambda는step2뿐이라지속지지를확보하지못했다.
행렬은손6+기타world6의12×12 유한시간응답이며FK나feedback Jacobian으로사용하지않았다.
평행을강제하지않고실제지지와초기기타p/q유지를함께다루는
[다음 작은 보정 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_COUPLED_CORRECTION_PLAN.md:1)으로이어간다.
[전체 표·원자료 한계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/README.md),
[코드·설정·실제 줄번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/CHANGED_FILES.md)를 따른다.

## 66. 작은 손·기타 결합 목표 보정의 실제 비교

이전 응답 행렬로 각 축 ±.001rad 목표 보정을 만들고 1/4·1/2·전체를 동일 초기 상태에서
각 24step(.1초) 검증했다. 3init/72steps이며 초기 q/기타/절대 LA/PD는 같고 상수 목표만 다르다.
기타 p/q feedback 구현 시험이 아니며 법선 정렬은 soft 선호다.

### 그림 90. 세 보정과 기준의 기타 오차·손바닥 source 간격·접촉 반응

![저장된 native 0.1초 응답의 기타 위치·회전 및 palm source 간격과 raw lambda](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/artifacts/palm_coupled_correction.png)

위는 설정 초기 목표 대비 기타 위치/회전 오차, 아래는 source 법선 간격과 step별 최대 palm raw λ다.
전체 보정은 손 추적점 9.289→9.113mm, 기타 최대 이동 5.341→5.099mm/회전 1.006→.973°로
줄지만 양의 raw λ는 step2 한 행뿐이다. 종료 source gap 9.048mm가 남아 유지 지지 성공은 아니다.
이 그림은 native 저장 자료의 과학 그래프이며 camera 장면이 아니다. Source 간격은 cooked
clearance가 아니고 raw λ를 N으로 환산하지 않았다. actual−goal 기타 world rotvec와
목표−actual 손 task의 부호/단위가 다르며 Euler/DOF 차이로 해석하지 않는다.

Full 모델 예측 차이는 손 위치 .127097mm/법선 rotvec .009713°, 기타 위치 .107389mm/world rotvec
.014706°다. 예측 통과 기준이나 feedback 정확도 인증은 아니다. 원 fit producer/실행 입력을
보존하고 입력 소비 시점만 고친 refit의 11개 결과 필드가 exact이며 추가 native 실행은 없었다.
[측정표·한계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1/README.md),
[관절 유지의 다음 관측 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_HOLD_OBSERVATION_PLAN.md:1)을 따른다.

## 67. 실제 관절 좌표와 총 DOF force 관측

두 목표각 조건에 계측만 추가해 2init/48step을 실행했다. 각 조건의 이전 states/trace/
tasks/contacts/controls 5배열과 exact다. baseline은 기존 .45 bias, full은 작은 결합 보정
전체이며 sensor OFF/ON 비교가 아니다. 질량과 native PD property는 두 조건에서 같다.

### 그림 91. 왼쪽 Shoulder_x·Elbow_y의 좌표 오차와 총 관절 힘

![저장된 native 관절 좌표와 완료 step의 총 DOF force 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/artifacts_v2/palm_hold_observation.png)

위는 실제 DOF 좌표와 각 조건의 Python 상수 제출 목표의 차이(rad), 아래는 완료 step의
total DOF force(Nm)다. 좌표는 t0 포함25개, 힘은 step1–24의24개이며 t0 힘을 만들지 않았다.
native 목표 getter 또는 whole-joint SO3 오차 인증이 아니다. 총 힘으로 drive-only torque,
effort 포화·중력 부족을 분리하지 않는다. 과학 그래프이며 camera 장면이 아니다.
[표·관측 한계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1/README.md)를 따른다.

## 68. 같은 초기 자세에서 왼팔 PD 강성·감쇠 비교

left12 kp/kd 1/1.5/2배만 바꾸고 초기 q·기타 p/q·절대 LA·상수 목표는 유지했다.
첫 v1 3init/72step은 setter 성공 반환값 누락 이력으로 보존한다. v2 3init/72step은
성공 반환값까지 검사하고 같은 배율의 첫 원자료5배열을 exact 재현했다.

### 그림 92. PD 배율별 기타 오차와 손바닥 지지 반응

![동일 초기 상태의 PD 배율에 따른 기타 위치·회전과 palm source 간격·raw lambda](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/artifacts/palm_hold_pd.png)

기타 최대 이동 5.099/5.631/6.145mm와 회전 0.973/1.039/1.100°로 gain 증가를 채택하지 않는다.
종료 손 추적점은 9.113/9.025/9.336mm, source 법선 gap은 9.048/9.015/9.271mm다.
양의 palm raw lambda는 기준 step2 한 행, 증가 조건 step1–2 다섯 행이며 이후 유지되지 않는다.
source 간격은 cooked clearance가 아니며 lambda를 N으로 환산하지 않았다. 과학 그래프다.
실제 몸통 최대 좌표 편차도 0.961/0.967/0.972°로 따로 측정했다.
[결과·검증 범위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/README.md),
[다음 강성 분리 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_STIFFNESS_ONLY_PLAN.md:1)을 따른다.

## 69. 실험별 초기 값과 실제 Isaac Gym5초 녹화

앞으로 새 실험은 초기 값과 실제 camera 영상을 함께 저장한다. 기존 기준의 초기 q/
기타 p·q/절대 LA/상수 목표/PD를 유지한 한 실행을1200step 연속 녹화했다.
처음24step states/trace/tasks/contacts/controls는 이전 기준과 exact이며 render는 상태를 쓰지 않는다.

### 그림 93. 같은 실행의0·2.5·5초 실제 camera 장면

![실제 Isaac Gym 전신·손 근접 camera의 초기 및 중간·종료 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/artifacts/recorded_trial_5s_contact_sheet.png)

위·아래는 같은 물리 실행의 전신·손 근접 시점이다. 저장된 native camera PNG를 조합했으며
MuJoCo 이미지나 저장 pose를 재생하는 영상이 아니다. MP4는 각151frame/30fps로5.033333초다.
시뮬레이션 endpoint는 정확히5초이며 이후 물리 적분을 추가해 영상 길이를 맞추지 않았다.
기타 최대 이동82.047mm/회전10.831°, 종료80.435mm/10.564°, 손 추적점100.688mm가 남는다.
source palm-up proxy 위반0은 전체 자세 제약이나 지지 성공 인증이 아니다.

### 실제5초 영상과 초기 값

![Isaac Gym 전신5초 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/whole_body.mp4)

![Isaac Gym 손 근접5초 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/hands.mp4)

[초기 settings·81관절각·기타 world p/xyzw q·PD·절대LA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/baseline/initial_values.json:1)를 저장했다.
별도 중단 시험은 SIGTERM에28step/4frame으로 종료하며 partial 두 영상과 사유를 남겼다.
신규2init1228step이며 중단 trial을 기준5초와 연결하지 않는다. constructor 시도와 정상
완료 횟수를 분리하며 실패 중 실제 create_sim 성공 횟수를 임의로 확정하지 않는다.
[설명·검증 범위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/recorded_trial_5s_v1/README.md:1)를 따른다.

## 70. 왼팔 stiffness만 변경한 실제 Gym5초 비교

초기 자세/기타worldp·q/절대LA1.1018469719600776m/상수 목표는 같다.
왼팔12의kp만1/1.5/2배,kd1배이며3init/3600step의 별도 실제 실행이다.
각조건의 초기값과0–5초 전신·손30fps151frame영상을 저장했다.

### 그림94 — 세 조건의 연속5초 기타 오차와source 법선간격

![왼팔 stiffness-only 저장곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/artifacts/palm_stiffness_only_curves.png)

처음0.1초 최대p/q오차는5.099/7.629/10.972mm,0.973/1.265/1.660°였다.
전체5초 최대값은82.047/246.612/241.007mm,10.831/76.100/74.383°,
종료값은80.435/236.592/240.967mm,10.564/73.508/73.437°다.
직전kp와kd를함께바꾼0.1초비교와조건/시간이같지않으므로동일결과로취급하지않는다.

종료source normal gap65.863/−101.071/−100.750mm는 현재기타frame의 유한target patch에
대한 손 추적점 법선투영이다. 음수를 cooked 형상의 실제 관통으로 단정하지 않는다.
양의palm raw lambda는step2/1–3/1–4에만있으며N하중인증이나지속지지증거가아니다.
몸통9초기목표는 유지했지만 실제 최대좌표변화4.227/4.400/4.457°를별도로측정했다.

### 그림95 — 같은 실행의 실제 초기전신·5초손근접frame

![세 조건의 실제 초기전신·5초손근접](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/artifacts/palm_stiffness_only_camera.png)

2×3배열의 열은kp1/1.5/2,윗행은전신t0(step0),아랫행은손근접t5(step1200)다.
실제Gym camera 저장PNG에서만조합했다. 같은시각/카메라의조건간비교이며
윗행과아랫행은카메라가달라위치변화를픽셀변위로해석하지않는다.
전체 경과는 [kp1 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/kp_1/whole_body.mp4),
[kp1.5 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/kp_1p5/whole_body.mp4),
[kp2 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/kp_2/whole_body.mp4)에서확인한다.
각조건의손영상과초기값은 [phase결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/README.md)에있다.

상향kp는채택하지않으며kp/kd1배를유지한다. 다음은절대LA current/taut/초기law5N의
[초기strap5초비교](/home/ajou/yigyu/3/stability_adapter_2/STRAP_FIVE_SECOND_PLAN.md:1)이고아직미실행이다.
기타p/qfeedback·학습·기타유지성공은아직없다. 기타자유/root하체고정/self-collisionON조건을유지했다.

## 71. 다면 그립 초기 자세의 실제 5초 비교

2026-10-08. baseline과 두 초기각 seed를 각각 5초 실행했다. 세 면의 초기 source 접근 조건은 모두 false였다. 기타 최대 위치/회전 오차는 baseline 82.047 mm/10.831°, seed 1 47.437 mm/12.769°, seed 2 26.773 mm/8.323°다. seed 2는 세 조건 중 기타 오차가 가장 작지만 안정성 성공은 아니다. source gap은 cooked clearance가 아니며 named-body 접촉만으로 기타 넥의 뒷면·앞면·옆면 접촉을 판별하지 않았다.

### 그림 96 — 5초 저장 trace의 기타 오차

![다면 그립 비교의 5초 기타 오차 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/artifacts/multi_face_grip_curves.png)

### 그림 97 — 실제 Gym 손 카메라 프레임

![세 조건의 실제 Gym 손 카메라 t=0 및 t=5초 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/artifacts/multi_face_grip_hands_camera.png)

위 행은 각 native 실행의 t=0/step 0, 아래 행은 같은 실행의 t=5.0 s/step 1200이다. 이미지들은 저장된 실제 Isaac Gym 카메라 PNG를 조합했으며 source-shape 재구성이나 MuJoCo 장면이 아니다. seed 1에서 엄지 양의 raw lambda는 step 63에서 마지막으로 관측됐고 palm/index 기록은 종료까지 남았다. seed 2에서는 thumb/index/middle 양의 raw lambda가 step 1200까지 기록됐고 palm의 마지막 양의 raw lambda는 step 121이며, 값이0인 접촉행은 step 134까지 남았다. 샘플 기록은 연속 접촉·지지력 인증이 아니며 raw lambda를 N으로 환산하지 않는다. 상세 값·초기 source gap·6개 영상은 [단계 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/README.md), 입력과 출력 provenance는 [artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/artifacts/artifact_manifest.json)에 기록했다.


## 72. 손바닥 여유를 둔 refinement 초기자세의 5초 비교

2026-10-08. 기존 seed 2 저장 실행과 새 α=0.5/α=0.25 5초 실행을 비교했다. 새 두 조건 모두 기타 최대 및 종료 오차가 이전 seed 2보다 커 채택하지 않았다. α=0.5의 여섯 초기 source gap은 3 mm 이내였고 α=0.25는 기준을 만족하지 않았다. 이 source gap은 cooked PhysX clearance가 아니며 named-body 접촉으로 넥의 특정 면을 판별하지 않는다.

### 그림 98 — 저장된 5초 기타 위치·회전 오차

![기존 seed 2와 두 refinement 실행의 기타 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/artifacts_v4/grip_palm_refinement_curves.png)

### 그림 99 — 세 실행의 실제 Gym 손 카메라 초기·종료 프레임

![기존 seed 2 저장 실행과 두 새 실행의 t=0 및 t=5초 손 카메라](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/artifacts_v4/grip_palm_refinement_hands_camera.png)

위 행은 각 실행의 step 0/t=0, 아래 행은 step 1200/t=5.0 s다. 왼쪽 열의 seed 2는 별도 이전 실행이며 이번 단계에서 다시 초기화하지 않았다. 손 접촉은 named-body 기록일 뿐 넥 접촉면이나 연속 지지를 인증하지 않고, raw lambda는 뉴턴 단위 힘이 아니다. 세부 수치·초기값·영상은 [단계 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/README.md), v4 provenance는 [artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/artifacts_v4/artifact_manifest.json)에 있다.

## 73. Seed 2 strap 초기조건의 5초 비교

2026-10-08. current, taut, 초기 law 5 N 조건을 각각 5초 실행했다(3 init/3600 physics step). 처음 0.1초 위치/회전 오차는 current 5.108 mm/0.969°, taut 3.545 mm/0.505°, 5 N 3.197 mm/0.428°였다. 5초 최대 위치 오차는 26.773/35.020/35.293 mm로 taut와 5 N이 더 컸지만 최대 회전 오차는 current보다 조금 작았다. 종료 위치/회전 오차는 current 23.189 mm/7.413°, taut 35.020 mm/7.542°, 5 N 35.292 mm/7.516°다. 초반의 낮은 오차가 5초 동안 유지되지 않았으며 안정화 성공이나 최종 길이 채택으로 해석하지 않는다. current의 이번 원자료 다섯 배열은 이전 Seed 2 기준과 exact 일치했다.

### 그림 100 — 기타 오차와 strap law 제출 scalar

![current, taut, 초기 law 5 N의 5초 기타 오차와 제출 scalar](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts_v3/seed2_strap_initial_curves.png)

곡선은 저장 trace의 위치(mm), 회전(도), 제출된 strap-law scalar(N)를 나타낸다. 하단 scalar는 native force sensor 계측값이 아니며 각 점의 시간은 law 입력 구간 시작 시각이다. 초기 5 N은 실행 내내 일정한 장력이 아니다. 여섯 부위가 모두 3 mm 이내여야 하는 통합 초기 source 접근 조건은 세 조건 모두 미달했다. current의 LH thumb3/index3/middle3 양의 lambda 기록은 step 1200까지, palm은 마지막 양의 기록 step 121 및 마지막 접촉행 step 134였다. taut/5 N의 palm과 middle은 step 1200까지 양의 기록이 있었고, thumb/index는 각각 step 74/145 및 78/147에서 마지막 양의 기록이 있었다. 이 named-body 기록은 넥 면을 분류하지 않고 raw lambda는 뉴턴 힘이나 연속 지지 인증이 아니다.

### 그림 101 — 실제 Gym 손 카메라 시작·종료 프레임

![세 strap 조건의 실제 Gym 손 카메라 t=0 및 t=5초 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts_v3/seed2_strap_initial_hands_camera.png)

2×3 배열의 윗행은 각 run의 step 0/t=0, 아랫행은 step 1200/t=5초다. 이미지는 native 실행 중 저장한 카메라 프레임에서 가져왔다. 초기 자세와 route 길이는 세 조건에서 같고 absolute rest length만 다르다. strap mesh는 camera render에 표시되지 않아 이미지로 rest length 차이를 구분할 수 없다. 결과 표·영상·원자료 링크는 [phase README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/README.md)에 있다. source/native contact 한계 및 안정화 성공 여부는 별도로 인증하지 않았다.

## 74. Seed 2 왼팔 초기 목표 편차 비교

2026-10-08. 세 조건을 각각 새로 5초 실행했다(3 init/3600 physics steps). 시작 목표 편차 0/0.5×/1×에서 1×의 기타 5초 최대 오차가 가장 낮았으나 위치 26.773 mm와 회전 8.323°가 남았다. 승인된 판단에 따라 full bias/current LA를 다음 진단 기준으로 유지하며 안정화 성공은 아니다. 점선은 초기 왼팔 목표 편차 최대값, 실선은 12 native scalar 좌표의 실제 `|q(t)-q(0)|` 최댓값이며 같은 관절 오차나 SO(3) 각도가 아니다.

### 그림 102 — 기타 오차와 왼팔 목표 편차·실제 드리프트

![세 조건의 기타 위치·회전 오차 및 왼팔 좌표 변화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/artifacts/seed2_startup_target_curves.png)

### 그림 103 — 실제 Gym 손 카메라 t=0 및 t=5초 비교

![실제 Gym 손 카메라의 세 조건 시작·종료 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/artifacts/seed2_startup_target_hands_camera.png)

2×3 배열에서 윗행은 t=0, 아랫행은 t=5초다. strap mesh는 렌더되지 않는다. 여섯 부위 통합 source 접근 조건은 세 조건 모두 미달했고, 이는 cooked clearance가 아니다. 접촉 자료는 면별 또는 지속 지지를 입증하지 않는다. [결과 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/README.md) 및 [입출력 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/artifacts/artifact_manifest.json).

## 75. Seed 2의 어깨·손목 목표 변화에 대한 5초 응답

2026-10-08. 동일 초기 q, 기타 목표, 절대 strap 길이, PD 및 solver에서 기준 1회, 왼팔 Shoulder/Wrist 단일축 목표 probe 6회, 결합 heldout 1회를 각각 5초 실행했다(8 init/9600 physics step). 단일축 요청은 한 축에 +0.002 rad이며 heldout 요청은 6축에 약 ±0.001 rad다. heldout 최대 기타 위치 오차는 26.774777 mm로 기준 26.772807 mm보다 0.001970 mm 컸고, 최대 회전 오차는 8.124454°로 기준 8.323296°보다 낮았다. 회전의 소폭 개선은 안정성 성공이나 자세 채택이 아니다.

### 그림 104 — 저장된 5초 기타 위치·회전 오차

![기준, 여섯 단일축 probe, 결합 heldout의 오차 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/artifacts/seed2_guitar_response_curves.png)

두 패널은 저장 trace의 기타 위치 오차(mm)와 world SO(3) 회전 오차(도)를 0–5초 전체에서 나타낸다. 점선은 heldout이다. 여섯 probe 응답행렬의 rank는 0.1초 창에서 0이었고, 마지막 1초 창의 rank 6/condition 56,647은 잠정 0.1 m 회전 lever를 사용하는 선형 식별값이다. 마지막 1초 평균 예측 잔차 0.789333 mm/0.155463°는 기준 대비 실제 변화 벡터 0.152794 mm/0.028116°보다 커서 역행렬 runtime 보정의 근거가 되지 않는다.

### 그림 105 — 실제 Gym 손 카메라의 기준·Wrist Z·heldout 프레임

![세 run의 실제 손 카메라 t=0 및 t=5초 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/artifacts/seed2_guitar_response_hands_camera.png)

각 열은 별도 native run이며 윗행은 step 0, 아랫행은 step 1200이다. 초기 여섯 source 부위의 통합 접근 조건은 충족되지 않았다. Heldout의 RH hand–guitar 접촉 행은 없고, palm 양의 raw lambda는 step 117에서 마지막으로 관측됐다. Named-body 접촉은 면별·연속 지지를 인증하지 않으며 raw lambda는 뉴턴 힘이 아니다. 모든 run의 기타 이탈은 남아 있고 `stability_success`는 false다. 전체 수치·초기값·영상·제약은 [단계 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/README.md), 입력·출력 SHA는 [artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/artifacts/artifact_manifest.json)에 기록했다.

## 76. Seed 2의 음의 축 방향과 절반 heldout 비교

2026-10-08. 세 조건을 각각 새로 5초 실행했다(3 init/3600 physics step). 새 `L_Shoulder_y` −0.002 rad는 기준 대비 최대·종료 p/q가 모두 낮았고, 새 `L_Wrist_z` −0.002 rad의 최대 회전과 half heldout의 최대 위치 오차는 기준보다 높았다. 이는 안정화 성공이나 제어기 채택이 아니다. 그래프에 함께 보이는 positive Shoulder Y/Wrist Z와 full heldout은 이전 저장 참조이며 이번 3회 실행에 포함되지 않는다.

### 그림 106 — 신규 실행과 저장 참조의 5초 기타 오차

![세 신규 실행과 네 저장 참조의 위치·회전 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifacts/seed2_response_locality_curves.png)

실선은 새 −Shoulder Y, −Wrist Z, half heldout이고 점선은 저장된 기준·두 positive probe·full heldout이다. 위치 오차는 mm, world SO(3) 회전 오차는 도다. 세 신규 초기 기타 위치/자세의 step 0–24, 총 25개 관측(24 physics step)은 저장 기준과 exact 일치했다. `L_Shoulder_y`와 `L_Wrist_z` 양·음 방향 endpoint secant로 만든 6×2 응답행렬은 0.1초 rank 0, 마지막 1초 평균 rank 2/condition 4.805(잠정 0.1 m 회전 lever)였다.

### 그림 107 — 실제 Gym 손 카메라 시작·종료 프레임

![세 신규 조건의 실제 Gym 손 카메라 step 0과 1200](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifacts/seed2_response_locality_hands_camera.png)

2×3 배열은 세 신규 run의 실제 Isaac Gym 저장 이미지로, 윗행은 step 0, 아랫행은 step 1200/t=5초다. 초기 여섯 source 부위의 통합 접근 조건은 충족되지 않았다. 각 run에서 R_Hip의 positive contact가 1200개 고유 step 모두에 기록됐고 RH hand–guitar contact 행은 0개였다. named-body 접촉행과 raw lambda는 넥 면·연속 지지·힘을 인증하지 않으며, 모든 run의 기타 이탈은 남았다. 첫 성공 후처리 v2는 step 0–24 exactness boolean을 true 통과조건으로 사용했으며, 편집 전 산출물과 입력 SHA 확인은 [v2 archive](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifacts_attempt_v2>)에 보존됐다. 현재 canonical producer는 boolean 형식만 검사하며 false도 허용하고, 두 PNG는 v2와 byte-identical이다. 표·제약·초기값·영상은 [phase README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/README.md), 입출력 SHA는 [artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifacts/artifact_manifest.json)에 있다.


## 77. Seed 2 어깨 보정 크기와 실제 기타 오차 feedback

실행일: 2026-10-08. Run ID: `seed2_guitar_feedback_v1`. 신규 세 조건은 각 5초, 총 3 initialization/3600 physics step이다. 저장된 기준 곡선 2개는 비교 참조이며 신규 실행 수에 포함하지 않는다. q/G/LA/PD 시작 조건과 최종 66축 제어 인터페이스를 유지했다.

| 조건 | 종료 위치 오차 (mm) | 종료 회전 오차 (°) | index 양 lambda 마지막 step | palm 양 lambda 마지막 step |
|---|---:|---:|---:|---:|
| 저장 기준 | 23.188748 | 7.413329 | — | — |
| 저장 Shoulder Y −0.002 | 22.883315 | 7.338493 | — | — |
| 신규 constant −0.008 | 22.182777 | 7.114842 | 87 | 123 |
| 신규 constant −0.016 | 21.989056 | 7.096635 | 95 | 124 |
| 신규 guitar feedback | 21.953773 | 7.096483 | 255 | 124 |

constant −0.008의 원자료 종료 위치 오차는 22.182776609 mm이며 표는 22.182777 mm로 반올림했다. constant 조건의 계산 rate는 적용되지 않았고 목표 offset은 고정이었다. feedback의 최대 requested rate는 0.1051752932474102 rad/s이며 rate-limited requested rate 최대는 0.008 rad/s다. 실제 float32 target rate 최대는 0.008003711700439453 rad/s다. 요청값과 실제 제출값을 구별한다.

### 그림 108. 저장 곡선과 신규 조건의 기타 오차·어깨 목표 offset

![저장 기준 두 개와 신규 세 조건의 기타 오차 및 Shoulder Y 목표 offset](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/artifacts/seed2_guitar_feedback_curves.png)

위치 오차는 world 위치 norm(mm), 회전 오차는 SO(3) log norm(°)이다. 목표 offset 패널은 신규 세 run의 요청 및 실제 float32 제출 목표를 mrad로 표시한다. 각 run은 300회, 60 Hz 제어 update다. 상수 조건의 computed rate는 목표에 적용되지 않았다.

### 그림 109. 신규 조건의 실제 Isaac Gym 손 카메라 프레임

![신규 조건 세 개의 step 0 및 step 1200 손 카메라 캡처](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/artifacts/seed2_guitar_feedback_hands_camera.png)

열은 constant −0.008, constant −0.016, feedback 순서이고 위/아래 행은 step 0/1200이다. 실제 Isaac Gym 카메라 캡처다. 각 조건의 손/전신 영상은 151 frame, 30 fps이며 ffprobe duration은 5.033333초다. 물리 기록 구간은 step 0–1200의 5초다. [0.008 손](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/native/constant_0p008/hands.mp4>) · [0.008 전신](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/native/constant_0p008/whole_body.mp4>) · [0.016 손](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/native/constant_0p016/hands.mp4>) · [0.016 전신](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/native/constant_0p016/whole_body.mp4>) · [feedback 손](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/native/guitar_feedback/hands.mp4>) · [feedback 전신](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/native/guitar_feedback/whole_body.mp4>).

thumb/middle의 양 lambda는 세 run 모두 마지막 step 1200에 관측됐다. index는 마지막 step 87/95/255, palm은 123/124/124였고 각각 총 양 lambda 고유 step은 index 24/34/46, palm 21/24/22였다. palm의 마지막 전체 접촉 step은 131/138/136이다 (body-group contact row 수는 32/38/48). `R_Hip` 양 lambda는 각 1200 고유 step에 관측됐고 RH hand contact 행은 0이다. 이는 body 이름/raw lambda 기록이며 특정 기타 면의 접촉, 연속 지지, 힘 단위, 관통 부재, 안정성을 판정하지 않는다. 초기 여섯 손 부위 source 접근 조건은 미달이다. 안정 연주 성공이나 안정성 주장을 하지 않는다.

시작·종료 요약, 추가 한계, 실행·산출물 provenance는 [단계 README](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/README.md>), [analysis.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/analysis.json>), [artifacts manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_feedback_v1/artifacts/artifact_manifest.json>)에서 확인한다. 다음 미실행 작업은 [support-pose warm start 계획](</home/ajou/yigyu/3/stability_adapter_2/SEED2_SUPPORT_POSE_WARMSTART_PLAN.md>)이다.

## 78. Same-target three-face initial-pose comparison

2026-10-08. 세 신규 조건을 각각 5초 실행했다(3 native initializations/3600 physics steps). 초기 왼쪽 33개 좌표만 baseline repeat, quarter, half 순으로 달랐고 absolute 81축 PD target과 absolute strap rest length 1.1018469719600776 m는 같았다. 초기 strap route 길이는 posture에 따라 1.0866096862/1.0867203139/1.0868332052 m로 달라 route geometry와 resulting tension은 동일하게 고정되지 않았다. Baseline repeat의 저장 states/trace/tasks/contacts 및 두 영상은 이전 기준과 exact 일치했으나 controls는 로그 schema 변경으로 exact하지 않았다. 이 재현 관측은 통과 gate가 아니다.

| 조건 | 첫 0.1초 최대 p/q | 5초 최대 p/q | 5초 종료 p/q |
|---|---:|---:|---:|
| Baseline repeat | 5.108 mm / 0.969° | 25.281 mm / 7.753° | 21.989 mm / 7.097° |
| Quarter | 5.108 mm / 0.969° | 25.487 mm / 7.821° | 22.176 mm / 7.142° |
| Half | 4.719 mm / 0.936° | 25.229 mm / 7.771° | 21.913 mm / 7.092° |

p는 goal 대비 world 기타 위치 norm, q는 world SO(3) 회전 오차다. Half는 최대 위치 오차가 baseline보다 0.052 mm 낮았지만 최대 회전 오차는 0.017° 높았다. half의 여섯 초기 source hull gap은 모두 3 mm 이내였지만 이는 cooked PhysX clearance나 기타 면 접촉 인증이 아니다. half의 raw positive lambda 기록은 index step 81, palm step 123까지였고, 마지막 contact row는 각각 step 83/132다. thumb/middle raw positive lambda는 step 1200에도 기록됐다. body contact row, distinct positive-lambda step, source gap은 서로 다른 관측이며 face-specific/continuous support를 입증하지 않는다. 안정성 성공 선언이나 후보 채택은 없다.

### 그림 110 — 동일 목표에서 기타 오차와 여섯 손 부위의 초기 source gap

![저장된 기타 위치·회전 오차와 세 trial의 6-body 초기 source-hull gap 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/artifacts/three_face_same_target_curves.png)

두 곡선은 저장된 실제 240 Hz trace의 0–5초 위치 오차(mm)와 회전 오차(°)다. 막대는 thumb3, index3, middle3, ring3, pinky3, palm의 초기 source-hull gap(mm)이며 세 실행을 색으로 구분한다. 작은 양수도 표시값을 0으로 반올림하지 않는다. Source 형상 거리는 cooked clearance가 아니다.

### 그림 111 — 실제 Isaac Gym 손 카메라의 시작·종료 프레임

![세 조건의 실제 Isaac Gym 손 카메라 t=0 및 t=5초 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/artifacts/three_face_same_target_hands.png)

각 열은 baseline repeat, quarter, half이며 위 행은 step 0, 아래 행은 step 1200/t=5초다. 실제 native camera PNG를 모은 이미지다. 조건별 손/전신 영상과 initial values는 [단계 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/README.md)에서 열 수 있다. Named-body 접촉과 raw lambda는 특정 넥 면, 연속 지지, 힘 단위 또는 안정성을 판정하지 않는다. 과거 source-only 거절 branch는 native initialization 0으로 보존됐으며, 이번 세 admitted run은 각각 native 초기화 1회와 1200 step을 완료했다. 전체 입력·수치·제약은 [analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/analysis.json), 생성 provenance는 [artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/artifacts/artifact_manifest.json)에 기록한다.

산출 후처리 첫 시도는 Python 3.8에 없는 `str.removeprefix` 호출로 실패했고 native call은 0이었다. 해당 producer·실행 로그·metadata는 [artifact_attempt_v1](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/artifact_attempt_v1>)에 보존했다. 문자열 처리 호환성을 보완한 뒤 저장 자료만으로 재생성했으며 성공 실행은 exit 0, 0.866초, 입력 19개 전후 SHA 일치, native_calls 0이다. 최종 독립 검수와 보존 대조 기록은 [review.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/review.md>)와 [final_verification.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/final_verification.json>)에서 확인한다.

## 79. Three-face finger target hold 비교

2026-10-08. 두 조건을 각각 새로 5초 실행했다(2 native initializations/2400 physics steps). 초기 81개 관절 좌표, 기타 목표, 절대 strap 길이, PD와 solver를 유지하고 왼손 손가락 21개 absolute PD target만 바꿨다. 팔 12축과 나머지 48축 목표는 고정했고 최종 제어 인터페이스는 66축이다.

| 조건 | 첫 0.1초 최대 p/q | 5초 최대 p/q | 5초 종료 p/q | 마지막 1초 최대 p/q |
|---|---:|---:|---:|---:|
| Saved finger targets | 4.719 mm / 0.936° | 25.229 mm / 7.771° | 21.913 mm / 7.092° | 21.915 mm / 7.093° |
| Initial finger targets | 3.934 mm / 0.872° | 26.112 mm / 7.725° | 26.047 mm / 7.715° | 26.112 mm / 7.725° |

p는 기타 목표 대비 world 위치 거리, q는 world SO(3) 회전 오차다. Initial finger targets는 초기에 낮은 오차를 보였지만 최대·종료 위치 오차가 더 컸다. 안정화 성공이나 후보 채택으로 해석하지 않는다.

| Trial / body | 마지막 양 raw-lambda step | 양 lambda 고유 step 수 |
|---|---:|---:|
| Saved — LH thumb3 | 1200 | 991 |
| Saved — LH index3 | 81 | 23 |
| Saved — LH middle3 | 1200 | 1072 |
| Saved — LH palm | 123 | 30 |
| Initial — LH thumb3 | 1200 | 1052 |
| Initial — LH index3 | 106 | 33 |
| Initial — LH middle3 | 1200 | 1086 |
| Initial — LH palm | 123 | 50 |
| Saved — R_Hip (right thigh) | 1200 | 1200 |
| Initial — R_Hip (right thigh) | 1200 | 1200 |

이 표의 마지막 step과 고유 step 수는 post-physics 저장 양 raw-lambda sample을 센 결과다. Raw lambda는 힘 단위가 아니며 face-specific 또는 continuous contact를 인증하지 않는다. body group이 없으면 양 lambda 고유 step은 0개(empty step set)로 기록하며 이를 physics step 0의 접촉으로 뜻하지 않는다. 특히 index 마지막 양 lambda step은 81에서 106으로 늦어졌고 palm은 양 고유 step이 30에서 50으로 늘었지만 마지막 step은 양쪽 모두 123이다. 두 trial 모두 6-body initial source-approach 조건은 true였으나 cooked PhysX clearance나 면 접촉 인증은 아니다.

Saved-target 재실행의 states/trace/tasks/contacts/controls 다섯 raw arrays와 hands/whole-body 두 영상은 저장 기준과 byte-exact 일치했다. 이는 관측된 재현성 기록이며 성능 gate가 아니다. 각 run의 native hands 및 whole-body 녹화는 151 frames, 30 fps, 5.033333초이고 물리 구간은 step 0–1200이다.

### 그림 112 — 기타 오차와 양의 raw-lambda body sample

![두 조건의 기타 위치·회전 오차와 post-physics 양의 raw-lambda sample 타임라인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/artifacts/three_face_finger_hold_curves.png)

곡선은 저장된 240 Hz trace의 0–5초 기타 위치 오차(mm)와 world SO(3) 회전 오차(°)다. 타임라인은 양 raw-lambda post-physics sample을 physics step/240초에 표시하며 두 조건의 표식을 세로로 ±0.1씩 분리했다. 점은 lambda 크기나 연속 접촉 구간을 뜻하지 않는다.

### 그림 113 — 실제 Isaac Gym 손 카메라 시작·종료 프레임

![두 조건의 실제 Isaac Gym hands camera t=0 및 t=5초 프레임 2×2 montage](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/artifacts/three_face_finger_hold_hands.png)

실제 native camera의 step 0과 1200 저장 PNG를 2×2로 배치했다. 초기 source 간극과 body 이름/raw-lambda 기록은 기타 면의 접촉, 연속 지지, 힘 또는 안정성을 인증하지 않는다. 시작 조건·측정 전체와 제한 사항은 [phase README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/README.md), 원자료 수치는 [analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/analysis.json), 입력·출력 provenance는 [artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/artifacts/artifact_manifest.json)에서 확인한다.

네 개의 151-frame/30-fps 기록: [saved target hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/native/saved_finger_targets/hands.mp4>) · [saved target whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/native/saved_finger_targets/whole_body.mp4>) · [initial target hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/native/initial_finger_targets/hands.mp4>) · [initial target whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/native/initial_finger_targets/whole_body.mp4>). 산출물 실행은 [artifact_execution.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/artifact_execution.json>)에 기록했다(exit 0, 0.7420416880631819 seconds, `native_calls: 0`). 최종 교차검수와 hash 대조는 [review.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/review.md>) 및 [final_verification.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_finger_target_hold_v1/final_verification.json>)에 남긴다.

## 80. Three-face source geometry support-loss diagnostics

2026-10-08. Fresh `saved_finger_targets` native run: initialization 1회, 1200 physics step/5.0 s, runner elapsed 95.3363209029194 s. Root와 하체 고정, torso 9개 PD target 유지, 양팔·손을 포함한 66축 제어 연결, 동일 기타 목표와 절대 strap rest length 1.1018469719600776 m를 사용했다. Report checks는 모두 true이고 constraint violation은 없었다. 이는 안정성 성공 판정은 아니다.

그림의 여섯 시점 자료는 fresh run과 구분한다. 두 이전 조건의 저장 body pose를 `[0, .1, .25, .5, 1, 5] s`에서 CPU source geometry에 배치했다. 각 시점은 범주형으로 같은 간격에 표시됐으며 선은 표본 안내다. 보간 궤적이나 연속 접촉을 나타내지 않는다.

| 조건 | 시점 | LH palm hull gap (mm) | 최대 좌표 오차 arm12 / finger21 / torso9 (°) |
|---|---:|---:|---:|
| Saved finger targets | 0 s | 2.129621 | 16.526690 / 2.686505 / 0 |
| Saved finger targets | 5 s | 9.894188 | 21.711862 / 0.567693 / 4.229168 |
| Initial finger targets | 0 s | 2.129621 | 16.526690 / 0 / 0 |
| Initial finger targets | 5 s | 5.392989 | 21.731453 / 0.071113 / 4.232301 |

### 그림 114 — 여섯 표본의 source gap·좌표 오차·facet 방향

![두 저장 조건의 이산 시점 source 간극, 관절 좌표 오차와 선택 facet inward alignment](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifacts_v3/support_loss_metrics.png)

좌측은 `rows.metrics[LH:palm].hull_gap_m × 1000` (mm), 가운데는 `max_abs_coordinate_error_rad` arm12/finger21/torso9 (degree), 우측은 LH thumb3/palm의 `inward_alignment_dot` (dimensionless)다. coordinate error는 SO(3) 회전 오차가 아니다. palm 선택 facet alignment는 0.994174에서 0.979404/0.978361로 변했고 thumb facet은 t=0에 −0.816388이었다. Hull proximity나 facet 방향은 cooked PhysX clearance, anatomical pad, 기타 면별 접촉 또는 지지 상실 원인을 입증하지 않는다.

### 그림 115 — 저장 actual pose의 기타 좌표계 source geometry 배치

![step 0, 120, 1200의 여섯 손 source hull과 rear/front/side polygon](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifacts_v3/support_loss_source_geometry.png)

각 패널은 G-local mm, 공통 축 범위, 같은 축 비율로 표시한 CPU source geometry다. Isaac Gym 렌더나 cooked 형상·접촉 검증이 아니다. fresh native 실행의 실제 151 frame/30 fps/5.033333 s 영상은 [hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/native/saved_finger_targets/hands.mp4>)와 [whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/native/saved_finger_targets/whole_body.mp4>)다. 실제 시작 관절각, 기타 위치·xyzw 회전·속도, PD 및 기타 초기값은 [initial_values.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/native/saved_finger_targets/initial_values.json>)에서 확인한다. t=0 오차는 첫 제출 전 planned target과 비교하고, 이후는 매 step 직전 로그된 target과 비교했다.

Fresh report의 양 actor material readback은 friction 1.0, contact offset 약 0.0001 m, rest offset 0 m였다. Raw contact friction을 물성 계수로 읽지 않으며 RSP thickness는 Flex-only 필드다. shape query가 상태·PD·Python target을 보존했다. 같은 저장 조건 재실행에서 다섯 raw array와 두 영상 SHA가 exact 일치한 사실은 관측 재현성이지 성능 gate가 아니다. Named body 접촉 또는 raw lambda는 면별·연속 지지나 힘을 인증하지 않는다.

산출물은 v3 producer exit 0, 11.23134584305808 s, `native_calls: 0`으로 생성했고 manifest의 입력 10,679개 SHA가 실행 전후 같으며 PNG 두 개를 기록한다: [artifact execution v3](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifact_execution_v3.json>), [manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifacts_v3/artifact_manifest.json>). 첫 시도는 font-family lookup 실패(exit 1, native 0)로 [보존](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifact_attempt_v1/>), v2는 렌더 성공 후 축 label/legend 겹침으로 [보존](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifact_layout_v2/>)했다. v3에서 배치를 수정해 시각 QA를 통과했다. 자세한 입력·제약·출처는 [phase README](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/README.md>), 변경 색인은 [CHANGED_FILES.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/CHANGED_FILES.md>), 독립 검수·보존 대조는 [review.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/review.md>)와 [final_verification.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/final_verification.json>)에서 확인한다. 다음 미실행 계획은 [THREE_FACE_ARM_INITIAL_TARGET_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_ARM_INITIAL_TARGET_PLAN.md:1)다. 안정성 기준은 완료 또는 판정되지 않았다.

## 81. Initial arm target comparison with stored finger targets

2026-10-08. Two new native runs completed 1200 physics steps / 5.0 s each (2 initializations, 2400 new steps total). In both, the left arm 12-joint target was set to actual initial angles. `arm_initial_saved_fingers` retained the 21 saved finger targets; `arm_and_fingers_initial` set those 21 targets to actual initial angles. The other 48 targets, initial actual 81-joint q, guitar pose/velocity, PD, solver and passive strap law were held the same. The dashed stored reference in Figure 116 is prior saved data, not a third new run.

Both trials began with a 15.0137668072902 mm strap slack. The passive strap submitted 0 N for all 1200 controls in each run; law reconstruction error was 0. This records no tension in these runs and does not establish strap deactivation or a sole cause of guitar motion. Both initial source-approach checks passed, but neither condition was adopted: maximum guitar position errors were 159.799114 mm and 157.516483 mm, with end errors 159.795174 mm and 157.510653 mm. The stored reference had maximum/end position errors 25.229274 / 21.912505 mm. The maximum rotation errors were 25.272466° and 25.623971° (stored reference 7.770624°). Joint target coordinate errors are scalar DOF coordinates, not SO(3) rotation error.

Palm positive raw-lambda samples ended at step 90 and 99; index3 ended at step 11 in both. The right-thigh-side body group (raw key `human/R_Hip`) recorded 1191 and 1190 unique positive steps, respectively. These counts do not establish continuous contact through all 1200 steps, hand contact, or support on any guitar face. Body positive-lambda rows do not certify force in N, cooked clearance, anatomical thumb facet, or continuous support.

### Figure 116 — guitar error curves and positive raw-lambda body timeline

![New arm-target native runs with stored reference curves and body positive-lambda sample times](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/artifacts/three_face_arm_initial_target_curves.png)

The solid curves show the two new runs; the dashed gray curve is stored reference data, not a new run. The top panels plot 240 Hz guitar position error (mm) and world SO(3) rotation error (degrees) over 0–5 s. The lower panel places each positive body raw-lambda row at `physics_step/240 s` for LH thumb3, index3, middle3, and palm. Marks are samples, not force magnitude or continuous-contact intervals.

### Figure 117 — native hands camera at start and end

![Actual native hands camera frames at step 0 and step 1200 for both arm initial target runs](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/artifacts/three_face_arm_initial_target_hands.png)

The 2×2 montage uses actual Isaac Gym native camera frames: top row step 0, bottom row step 1200 / 5.0 s; columns are saved fingers and arm-and-fingers initial. No synthetic contact marks are drawn. Each of the four native videos contains 151 frames at 30 fps and is 5.033333 s encoded: [saved-finger hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/native/arm_initial_saved_fingers/hands.mp4>) · [saved-finger whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/native/arm_initial_saved_fingers/whole_body.mp4>) · [initial-finger hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/native/arm_and_fingers_initial/hands.mp4>) · [initial-finger whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/native/arm_and_fingers_initial/whole_body.mp4>).

The artifacts were produced from saved data with exit code 0, 0.7822753069922328 s elapsed, and `native_calls: 0`. Input/output hashes are in [artifact_manifest.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/artifacts/artifact_manifest.json>); the actual initial settings and limitations are documented in [phase README](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_arm_initial_target_v1/README.md>). The next unexecuted experiment is the [half-slack comparison plan](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_HALF_STRAP_SLACK_PLAN.md).

## 82. Half-pose strap-slack comparison with stored reference

2026-10-08. Two new native runs completed 1200 physics steps / 5.0 s each (2 initializations, 2400 new steps total). Both use the same saved half-pose actual initial 81-joint state and old absolute 81-joint PD targets; only fixed strap rest length changed. Root/lower body remain fixed, torso 9 targets remain held, and the final 66 bilateral arm/hand joints remain available. The guitar is free. The stored `three_face_support_loss_v1` curve is prior data, not a third new run.

| Condition | LA rest length (m) | Max position / rotation error | End position / rotation error |
|---|---:|---:|---:|
| Stored support-loss reference | — | 25.229274 mm / 7.770624° | 21.912505 mm / 7.091529° |
| Half slack | 1.0943400885564325 | 30.696048 mm / 7.727219° | 30.695007 mm / 7.622948° |
| Zero slack | 1.0868332051527874 | 32.861798 mm / 7.103582° | 32.860232 mm / 7.103303° |

The first 0.1 s maximum errors were 4.718710 mm / 0.936405° for half slack and 3.567710 mm / 0.511048° for zero slack. Both new runs reduce maximum rotation error relative to the stored reference but increase maximum and end position error and end rotation error. Neither LA is adopted. Common guitar goal: world position `[-0.1972053649442413, 0.11878119221286644, 0.8277786273204872] m`, xyzw quaternion `[-0.3412600918621295, 0.5816458777723966, 0.5857788413284049, 0.44954729631550555]`. Initial 81 actual angles, 81 absolute targets, and guitar state are preserved in each `initial_values.json` linked from the [phase README](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/README.md>).

Palm positive body raw-lambda records reach step 1200 in both runs. Thumb3 positive raw-lambda records end at step 35 for half slack and step 96 for zero slack. These sampled body records do not certify a requested guitar face, force in N, substep-continuous contact, or continuous three-face support. The passive strap-law submitted series is calculated from the recorded law, not a native force sensor: maximum/end values were 12.894182/1.063010 N for half slack and 5.119047/2.677263 N for zero slack; reconstruction error was 0 and the 300 N cap was never reached.

### Figure 118 — guitar errors, submitted passive strap law, and body raw-lambda times

![Half-slack and zero-slack guitar error curves, calculated strap-law output, and positive body raw-lambda sample times](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/artifacts_v2/three_face_half_strap_slack_curves.png)

The upper panels show guitar position error in millimeters and world SO(3) rotation error in degrees over saved samples at 240 Hz; gray dashed curves are stored reference data. The lower-left panel plots submitted passive strap-law N at interval-start times `step/240 s`, 0–1199. The lower-right panel marks positive raw-lambda samples at post-step times `step/240 s` for LH thumb3, index3, middle3, and palm. Marks are samples, not force magnitudes or continuous-contact intervals.

### Figure 119 — actual native hands-camera start and end frames

![Actual native hands-camera frames at step 0 and step 1200 for the half-slack and zero-slack conditions](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/artifacts_v2/three_face_half_strap_slack_hands.png)

The 2×2 montage uses actual Isaac Gym camera frames: columns are half slack and zero slack; rows are t=0.0 s / step 0 and t=5.0 s / step 1200. No synthetic contact marks are drawn. Each native video contains 151 frames at 30 fps and encodes 5.033333 s: [half-slack hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/half_slack/hands.mp4>) · [half-slack whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/half_slack/whole_body.mp4>) · [zero-slack hands](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/zero_slack/hands.mp4>) · [zero-slack whole body](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/zero_slack/whole_body.mp4>).

![실제 native hands 카메라 영상, half slack](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/half_slack/hands.mp4)

The first artifact producer succeeded with `native_calls: 0`; its outputs and execution are preserved in [artifact_layout_v1](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/artifact_layout_v1/>). Visual review found its timeline legend covered late palm marks. The canonical v2 producer moved that legend to the lower right and wrote a fresh output directory. V2 exited 0 with `native_calls: 0`; no native run was repeated. Its [execution record](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/artifact_execution_v2.json>) and [14-input/output manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/artifacts_v2/artifact_manifest.json>) record the saved-data provenance. Full initial values, captions, limitations, and video links are in the [phase README](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/README.md>); changed source references are indexed in [CHANGED_FILES.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/CHANGED_FILES.md>). The next unexecuted diagnostic is the [native contact-feature location plan](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_NATIVE_FEATURE_MAP_PLAN.md:1). Overall guitar restoration, persistent three-face support, and playing stability remain unfinished.

## 83. 저장된 세 면 접촉 feature map

2026-10-08. 기준·half slack·zero slack의 저장된 접촉/pose 분석 15,511행을 시각화했다. 새 native 초기화와 physics step은 0이다. 기준 4,346행, half slack 5,556행, zero slack 5,609행을 사용했다. 점 색은 LH body를 나타내며 neck face 분류를 뜻하지 않는다. feature 좌표는 저장된 G-root frame이다.

![양의 raw lambda feature 점과 유한 patch/source geometry proxy](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1/feature_map.png)

![양의 raw lambda 행의 유한 desired-patch 거리, 결측 구간은 연결하지 않음](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1/patch_distance.png)

![저장 Isaac Gym hands frame: 기준/half/zero 열, 0/0.5/5초 행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1/native_hands.png)

post-step body-origin feature pair 최대 잔차는 기준/half/zero 순서로 0.00004974/0.00006753/0.00005328 mm였다. 이는 깊이 또는 연속 접촉 보증이 아니다. palm의 finite desired-patch 거리는 21.105–22.783/24.390–29.806/25.996–28.382 mm이고 원하는 palm patch 내부 표본은 전 조건 0이다. thumb rear patch 투영 내부 표본도 기준 41, half 10, zero 2건이며 경계 분류에 머문다. index/middle의 fret 4/5 인근 점은 기하 proxy 호환 관찰이며 해부학적 누름/힘 지지 증거가 아니다. ring/pinky 접촉 행은 없다. 현재 세 면 grip은 달성되지 않았다.

재사용한 실제 5초 native 전체 영상:

![기준 저장 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/native/saved_finger_targets/whole_body.mp4)

![half slack 저장 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/half_slack/whole_body.mp4)

![zero slack 저장 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/native/zero_slack/whole_body.mp4)

분석 원자료와 source producer는 수정하지 않았다. figure의 source mesh/fret 표시는 형상 proxy이며 native render가 아니다. 다음 검토는 gain을 유지한 contact-point/facet footprint 중심 조정이며, 이 단계에서 새 trial은 하지 않았다. 세부 설정·SHA·재현 명령은 [결과 README](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1/README.md>)와 [변경 파일 색인](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_native_feature_map_v1/CHANGED_FILES.md>)에 있다.

세PNG는저장입력으로9.619365초/exit0/native0 생성했고root가원자료와실제이미지를대조했다. SDKnormal부호미확인·configuredsubsteps1/nativeSimParams미조회·source/cooked한계를유지한다. Canonicalv2/그림최종독립검수는재호출도구의agent thread limit오류로보류이며부분검수를최종승인으로표시하지않는다. 다음 [접촉footprint 계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_CONTACT_FOOTPRINT_PLAN.md:1)은FK민감도와source후보부터시작하는미실행계획이다.

## 84. 저장 source geometry의 엄지 후면·손바닥 옆면 footprint 후보

2026-10-08. V1/V2의 source-only 후보 네 개(각각 rear patch 0.3/0.7 mm)를 비교했다. 네 후보 모두 거절됐고 이번 phase에서 native 초기화와 physics step은 0이다. 엄지 V2 점은 rear patch 경계 바깥 0.200727/0.395092 mm이며 목표점 오차는 3.200398/3.412930 mm다. Palm 대표점은 finite side patch 안쪽 4.721738/4.960842 mm지만 triangle 일부 vertex는 patch 밖으로 뻗는다. 이는 source geometry 관찰이며 native 접촉·힘·cooked 형상 검증이 아니다.

![V1/V2 엄지 후면 patch 후보와 V2 손바닥 finite side patch·source triangle](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/artifacts_v2/source_candidate_comparison.png)

이번 후보를 위한 native 영상은 없다. 아래 5초 영상은 기존 saved-finger-target reference 실행이며 후보의 경과가 아니다.

![기존 reference 실행의 실제 native whole-body 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/native/saved_finger_targets/whole_body.mp4)

분석 결과와 입력 조건은 [phase README](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/README.md:1>) 및 [변경 파일 색인](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_contact_footprint_v2/CHANGED_FILES.md:1>)에 있다. [다음 미실행 계획](</home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_REAR_FACET_PLAN.md:13>)은 다른 rear-facing source facet을 검토한다. 이전 feature-map 자료의 독립 검수는 v1 review에서 완료됐고, 이 새 그림의 독립 검수는 아직 대기 중이다.

Canonical 그림은 explicit input 봉인을 사용하는 새v2 producer로10.895391초/exit0/native0 생성했다. 분석v1 stdout의self-input 불일치와 첫wrapper의경로보호 실패는원문/로그/metadata로보존했고후보수치는exact같다. 왼쪽점선은기울어진패치왼쪽변에서수직거리2mm의inset이며국소확대다. 오른쪽은모든trianglevertex를포함한다. root가원자료와실제PNG를대조했으며새summary/그림최종독립검수는도구threadlimit재호출실패로보류다. source V1/V2·직전featuremapv2/PNG3개독립검수와구분한다.

## 85. 엄지 후면 source facet 네 후보 비교

2026-10-08. 초기 outward G·+Z 조건을 만족한 source triangle 367개 중 가장 넓은 면(index 323, 4.433117 mm², outward G z=0.827536)을 기준으로 완료 후보 네 개를 비교했다. 선택 면은 해부학적 패드나 cooked PhysX 형상 인증이 아니다. 목표 인근 대표점은 유한 patch 경계 바깥에 있고, 후보별 엄지 목표 오차는 14.047475/13.682516/14.499266/12.609899 mm, 손바닥 목표 오차는 5.701879/4.772728/4.270202/1.810477 mm다. source intersection 수는 3/4/2/1이며 네 후보 모두 거절됐다. 승인 후보 0, native 초기화 0, physics step 0이다.

![엄지 후면 source facet 점·목표와 네 조건의 paired target-error 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/artifacts/rear_facet_source_comparison.png)

source common radius는 물리적 깊이가 아니며 λ는 힘이 아니다. 기록된 한 QP status=false 사례도 feasible bound 구간으로 판정됐으며 최적해로 표현하지 않는다. 이는 CPU source geometry 비교이며 Gym/PhysX 접촉, cooked 형상 또는 해부학적 지지 인증이 아니다. 이번 후보 영상은 새로 만들지 않았다. summary/실제PNG 최종 독립 검수는 C/W/S 없음으로 완료했고, V1 source-pre·recovery 검수와 이전 후처리 검수는 완료됐다. 자세한 수치·입력 봉인·재현 정보는 [phase README](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/README.md:1>)와 [변경 파일 색인](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/CHANGED_FILES.md:1>)을 참조한다.

검색9.785139초/그림5.638161초exit0/native0이며소스보존/실제source거리/그림정합을확인했다. [최종독립검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/review.md)와 [다음미실행catalog계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_REAR_FACET_CATALOG_PLAN.md:1)을남긴다.

## 86. 후면 facet catalog와 near-rear source 후보

저장된 source catalog에서 rear-facing 조건을 만족한 점은 368행 중 367개다. triangle 786은 적격점이 아니라 기존 native 관측 source triangle 위치를 함께 표시하는 참조다. 선택 facet 303과 1462의 필요 이동은 각각 11.677484672/11.698917250 mm이며, 이전 가장 큰 triangle 323은 17.136177920 mm다. 이 선형 fit은 물리적 또는 실제 FK 성공이 아니다.

![후면 source catalog의 G XY 점, patch, inset과 선택 facet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/artifacts/rear_facet_catalog_Gxy.png)

near-rear search의 네 순서 후보는 모두 거절됐고 accepted 0, native 초기화 0, physics step 0이다. 엄지 목표 오차는 8.076657061/8.565519264/7.524248157/8.078905497 mm, 손바닥 목표 오차는 3.407506669/3.797805320/1.985672776/3.715975688 mm, source 교차 수는 2/3/1/3이다. 가장 낮은 엄지 오차의 triangle 1462·0.3 mm 행도 middle3–fret4 common radius 0.040322319 mm와 엄지 patch margin −2.969092 mm를 보인다. 이 common radius는 물리적 깊이가 아니며 해당 witness의 rearward patch dot은 0.267591이다.

![네 거절 source 후보의 엄지·손바닥 오차와 source 교차 수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/artifacts/near_rear_rejected_candidates.png)

그림은 source mesh의 정적 분석이며 PhysX cooked 형상, 실제 접촉이나 힘을 인증하지 않는다. 사용자 목표인 엄지 후면·손가락 전면·손바닥 옆면 접촉은 달성되지 않았다. 이번 후보의 native 영상은 없다. 다음 미실행 계획은 검지·중지8 초기각도 ±0.10rad와 손가락/모델/목표 차이 한계 안에서 조정한다. 상세 입력과 producer는 [phase README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/README.md) 및 [변경 파일 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/CHANGED_FILES.md)에 있다. 그림 독립 최종 검수 경로는 [예정 review](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/review.md)다.

그림2개는6.020186초/exit0/native0으로 생성해 실제PNG와 원자료를 root가 확인했다. catalog 독립 검수/검색 사전 독립 검수는 완료했다. 검색결과·그림의 최종 독립 검수 재호출은 도구의 agent thread limit 오류로 보류됐으며 완료로 표시하지 않는다. [범위 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_rear_anchor_v1/review_status.json)과 [다음 미실행 계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_FRONT_FINGER_INITIAL_PLAN.md:1)을 남긴다.


## 87. 검지·중지 초기각과 전면 이동 허용의 source 검색

25좌표의 source 초기검색을 두batch에서 각각3개 완료했다. 모든6후보는source겹침/엄지·손바닥 지지조건으로 거절됐고 새native/physics0이다. 다른56초기각·기존절대81목표·G p·q/LA/gain을 유지했다. 앞단계는전면초기XY목표, 다음단계는전면유한영역 안의 XY이동을 허용한다. near/linear 추정값이달라 단일항 인과비교로표현하지않는다.

![source후보6개의 목표오차·교차행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_front_sliding_v1/artifacts/six_source_candidates.png)

![sliding후보의 source 지점과목표 GY–GZ투영](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_front_sliding_v1/artifacts/source_points_Gyz.png)

그림은 실제Gym렌더가아니며 대표source지점을표시한다. source교차는physicaldepth/force인증이아니다. root가12실제거리witness와전체human–guitar교차/초기각·81목표를재계산했고 두PNG를원자료와대조했다. Solverfalse1개도feasiblewitness의상한과supportplane하한으로판정했으며최적해로인증하지않는다. 검색11.165761/11.432675초, 그림6.707739초exit0/native0이다. 독립검수도구한도로root검증/산출물만완료했다. [상세결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_front_sliding_v1/README.md:1), [변경파일](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_front_sliding_v1/CHANGED_FILES.md:1), [다음미실행계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_WIDER_HAND_INITIAL_PLAN.md:1)에기록한다. 전체초기복원·지속세면지지·연주안정화는계속진행한다.


## 88. 전체왼손source초기배치와실제5초근접진단

엄지후면·네손가락전면·손바닥옆면을목표로wide33 12/whole-tip support-plane3의source15후보를검사했다. 모두source support미달이며30거리witness·전체형상교차/81목표를재계산했다. 겹침0인근접후보로새native두조건을각5초1200step/151frame·30fps실행했다. source거절을지지성공으로바꾸지않았다.

![15개source대표점오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/artifacts/source_fifteen_candidates.png)

Source정적proxy오차mm이며Gymrender/기타drift가아니다. 서로다른seed·목적함수이므로인과비교로해석하지않는다.

![실제Gym0초·5초장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/artifacts/native_initial_and_end.png)

위기존목표/아래새초기finger21목표,왼쪽0초/오른쪽5초다. 녹색왼손/자홍색오른손/파란기타의실제카메라장면이다. 같은초기81/G/PD/LA1.1018469719600776m에서21손가락PD목표만다르다.

![원자료기타오차곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/artifacts/native_guitar_motion.png)

기존최대25.779645mm/7.800837°,초기finger37.615076mm/8.587915°로새finger전체목표는악화해채택하지않는다. 기존thumb3후면source patch근접양λ고유30step/last260과middle3전면1082/last1200은있지만palm옆면근접은0이다. 기존palmbody양λfeature는요청patch에서19.323948~20.518808mm멀다. Body명/rawλ/2mmsource근접은면정체성·힘N·연속지지·cooked관통인증이아니다. SDKfeature6715행을post-pose로대조했다.

![기존목표실제손0~5초영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/native/original_targets/hands.mp4)

[나머지전신/손영상·초기값·실패보존과설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/README.md:1)에있다. 두조건상향proxy위반0/양손contact고유step0/root하체exact고정이나몸통실제좌표drift4.228004/4.255594°는다. Sol/root가그림과문서를만들었고Luna/독립검수는thread limit으로불가했다. 첫후처리live로그SHA오류를원본보존후v2로수정했고새physics0이다. [다음미실행계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_PATCH_PRIORITY_INITIAL_PLAN.md:1)은요청손바닥옆면을우선맞추고작은개별손가락목표를비교한다. 전체초기복원·연주중안정화목표는계속진행한다.


## 89. 스트랩 경로를 포함한 실제 Isaac Gym 5초 영상

사용자요청으로새영상에실제passive route를주황표시했다. 실선은native depth기준보이는구간,옅은점선은몸·기타에가려진구간이다. 선두께는픽셀표시용이며천너비/처짐/새충돌mesh를뜻하지않는다. Camera rawPNG는그대로보존했다.

![초기전신/스트랩경로](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/native/frames/whole_body/00000.png)

기타버튼→어깨/몸통guide→다른버튼의실제13지점/12구간을표시한다. 절대LA1.1018469719600776m를화면에보인다. 점선은깊이가려짐표현으로몸표면접촉인증이아니다.

![5초손근접/스트랩경로](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/native/frames/hands/00150.png)

기타/상체이동에맞춰경로도갱신된다. 모든151프레임의route는동일step trace와exact같고query/render는human·guitar상태를유지했다.

![스트랩포함실제손5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/native/hands.mp4)

새actual1회1200step·두카메라151frame/30fps·5.033333초다. 기존 original_targets와초기값/목표/물리가같고5배열/raw camera302PNG가exact같았다. 최대25.779645mm/7.800837°이며시각화추가가안정화성공을뜻하지않는다. [전신영상·초기/종료이미지설명·검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/README.md:1)에저장했다. 앞으로기본녹화는StrapTrialRecording이며oldsource/영상은보존한다. Root가산출물·실제PNG/수치QA를수행했고독립검수는thread limit으로보류했다.


## 90. 손바닥 옆면 우선 초기 자세와 스트랩 포함 실제5초

새 source두후보는 세면지지기준 미달이다. 겹침없는 근접후보로 실제1회1200step/5초를 실행했다. 왼손33초기각만 조정하고 old81목표·other48·G p/q·LA/gain은 유지했다.

![초기 실제Gym 전신과 스트랩](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/native/frames/whole_body/00000.png)

주황실선은 보이는 actual13지점/12구간 route, 옅은점선은native depth기준 가려짐이다. 선은 천mesh/접촉인증이 아니다. 절대LA1.1018469719600776m·초기여유16.013697mm다.

![실제Gym 손·스트랩0~5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/native/hands.mp4)

두카메라 각151frame/30fps·인코딩5.033333초이며 새 초기값을 포함한다. 실제G 최대26.091583mm/7.937143°로 직전보다 조금 커 새자세를 채택하지 않는다.

![기타오차와 손바닥source 유한patch거리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/artifacts/actual_G_and_palm_gap.png)

기타곡선은actualworld상태, 아래점10개는source거리 상한/하한이다. 서로다른 증거다. 초기0.421670mm→step4 0.151185mm 근접이어도 첫palm body양λ는step125/0.520833초다. 요청palm옆면근접은0이며 thumb후면793step/middle전면1052step 근접기록을 grip성공으로 표시하지 않는다.

![Chest와 팔chain의 실제anchor XYZ변위 분해](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/artifacts/early_Chest_arm_vectors.png)

축별vector합을검증했으며 norm의합/인과검증으로해석하지않는다. Body9최대좌표drift4.231250°다. [초기값·전신영상·상세설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_diagnostic_v1/README.md:1), [다음미실행단위](/home/ajou/yigyu/3/stability_adapter_2/TORSO_HOLD_AND_NATIVE_COLLISION_PLAN.md:1)에 남긴다. 원자료·형상/feature 재계산·실제PNG QA는 root수행, 독립검수는 도구한도로 보류다. 전체 기타 초기복원·유지/연주안정화는 계속 진행한다.


## 91. 몸통9 PD 유지 강도 비교와실제스트랩영상

Torso/Spine/Chest9 stiffness600→1200·damping150→212.1320343만변경한한5초와initial조회physics0한회를분리했다. 나머지72properties/초기81/G/기존81목표/LA는같다.

![실제body9 PD×2 손과스트랩0~5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/native/hands.mp4)

한actual1200step·두카메라각151frame/30fps·5.033333초영상이다. 주황실선/옅은점선은actualpassive route의보임/가려짐이며천mesh/표면접촉인증이아니다.

![실제G오차와body9좌표변화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/artifacts_v2/G_and_body9_comparison.png)

최대G이동26.091583→14.052228mm/회전7.937143→2.884291°,body좌표4.231250→3.536898°로줄었다.첫0.1초는조금커져전시간개선을주장하지않는다.

![source간격과요청SDKpatch근접시점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/artifacts_v2/palm_gap_and_patch_features.png)

source거리10표본과SDK조건을구분한다. 요청palm0·실제palm bodycontact0이고thumb후면793→3step/middle전면1052→12step으로줄어세면grip성공이아니다.기타오차만줄어도전체목표완료로보지않는다.

![nativecollision요청 초기카메라](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/initial_collision/hands_collision.png)

Rawnormal/collisionpixel은exact같다. 초기black해석은실제PNG재열기후정정했다. shape55/28와filter/offsetquery성공은cooked거리인증이아니다. [초기값·전신영상·표·실패보존설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/README.md:1), [후속offline계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_SUPPORT_RESIDUAL_AT_BODY9_PLAN.md:1)에기록한다. Root수치/실제PNG QA완료,독립검수는도구한도로보류다. 전체기타초기복원·지지/연주안정화는계속진행한다.


## 92. 현재actualq의FK대조와palm잔차 방향 준비

완료된body9×2 actual5초의저장자료만읽어새native/physics0이다. t0-onlycalibration/actualChest이동을포함한FK를4진단+20heldout시점에대조했다.

![네두축회전가설의전체왼팔손오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_two_axis_fk_v2/artifacts/whole_hand_FK_hypotheses.png)

전체손gate0.1mm/1mrad는모두미달했다. 표본연결이며원인/전체importer계약을확정하지않는다. Exp(sum) heldout최대1.222811mm/0.017266rad,XMLproduct0.835770mm/0.010405rad다.

![palm미분과미실행기하dq](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_two_axis_fk_v2/artifacts/palm_J_and_geometric_proposals.png)

Palmarticulation24시점최대origin0.000312034mm/rotation6.38e-7rad는잘맞았다. 위미분mm/rad·아래dqrad는source기하계산이지PD/접촉응답이아니다. 전체손실패를통과로바꾸지않는다.

![분석대상의기존실제Gym손·strap0~5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/native/hands.mp4)

이영상은새실행이아니며최대G14.052228mm/2.884291°·palmcontact0인직전물리실행이다. [상세설명/initial값/원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_support_two_axis_fk_v2/README.md:1), [다음actual손pose기반안전성계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_MEASURED_POSE_RESIDUAL_PLAN.md:1)에기록한다. Physicsposeoverwrite는없으며최종66권한·기타초기복원/유지/연주안정화목표를유지한다. Root그림QA완료,독립검수는도구한도로보류다.


## 93. 손바닥 단독 접근의 손가락 형상 교차와 연동 준비

직전 body9×2 실제5초의 저장 상태를 사용했다. 이번 새 native/physics 실행은0이다.

![손바닥 접근과 손가락 source 교차 증가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_measured_geometry_v1/artifacts_v2/palm_gap_and_finger_overlap.png)

16배치 중4개는 기준0, 신규12개 중 초기 quarter만 source 선별을 통과했다. 5초 상태에서 quarter도 검지3/중지3–기타 common radius 증가0.920751/0.767056mm가 있어 실제 ON은 실행하지 않았다. 위 거리는 source witness 상한, 아래는 baseline 대비 source radius 증가이며 native 관통 깊이가 아니다.

![조건부 단일 축 손가락 pose 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_measured_geometry_v1/artifacts_v2/conditional_single_hinge_errors.png)

실제 부모 pose를 제공한6관절×24시점의 최대 원점 오차0.130835µm/회전오차0.187805µrad다. 전체손 FK/PD/접촉 인증이 아니며 이전 finger1 모델 실패를 유지한다.

![분석 기준인 기존 실제 Isaac Gym 손·스트랩 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/native/hands.mp4)

이 영상은 기존 actual1200step/151frame이며 이번 추가 실행이 아니다. 실제 passive strap의 보이는 경로는 주황 실선, 가려진 경로는 옅은 점선이다. [전체 설명/원자료/초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_measured_geometry_v1/README.md:1), [다음 미실행 연동 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_FINGER_COUPLED_SOURCE_PLAN.md:1)에 기록한다. Root 실제PNG QA 완료, 독립검수는 도구 thread 한도로 보류다. 최종66권한과 기타 초기복원·유지/연주 안정화 목표는 계속 진행한다.

추가 거리 감사: 네 SLSQP success=False를 보존했다. 독립 feasible witness의 상한/하한으로 보고하며 exact optimum/solver 전체 성공을 주장하지 않는다. [거리 solver 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_measured_geometry_v1/DISTANCE_SOLVER_NOTE.md:1)에 root 감사 가정의 보완을 남긴다. 추가 물리 실행은 없다.


## 94. 작은 왼손목 움직임 중 자유 기타 유지

같은초기81/G/PD/LA의actual한5초/1200step을새로진행했다. 목표L_Wrist_x만±.005rad/1Hz·60Hz이고나머지80targetexact다.

![실제손목응답과기타초기오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_wrist_motion_v1/artifacts_v2/wrist_motion_and_guitar_errors.png)

실제좌표minusstatic의1Hz진폭은.146929°다. 2~5초G변화0.481766mm/.091929°이고전체최대초기오차14.132608mm/2.894328°다. 정지유지에서작은동작검증으로진행했으며큰/여러연주동작·초기오차복원은아직이다. Scalar관절각과actualpalmworld회전은구별한다.

![이번실제Gym손·기타·스트랩0~5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_wrist_motion_v1/native/hands.mp4)

![이번실제5초종료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_wrist_motion_v1/native/frames/hands/00150.png)

151frame/30fps로원nativePNG와actual13routeoverlay를보존했다. Root그림/초기·종료PNGQA완료,독립검수는도구threadlimit으로보류다. [상세결과/초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/small_wrist_motion_v1/README.md:1), [새122개영상모음](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v2.md:1), [다음미실행strap비교](/home/ajou/yigyu/3/stability_adapter_2/BODY9_STRAP_FINE_COMPARISON_PLAN.md:1)에기록한다.


## 95. 같은초기자세·손목동작의strap−2mm

새actual한5초/1200step이다. LA만2mm줄였고native t0/PD/목표파형1200개는기준과exact다.

![초기오차와제출cable법칙T](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/artifacts/guitar_errors_and_strap_tension.png)

최대초기오차14.132608mm/2.894328°→14.010556mm/2.607665°,2~5초범위.481766mm/.091929°→.363488mm/.070089°다. 실제손목좌표진폭은.147836°로유지됐다. Peak법칙T는24.129230→28.152161N이며rawcontact force인증과구별한다.

![새실제Gym손·기타·strap0~5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/native/hands.mp4)

![새실제5초종료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/native/frames/hands/00150.png)

두151frame영상·원nativePNG와actual13route를보존했다. RootactualPNGQA/자료검사완료,독립검수는도구threadlimit으로보류다. [초기값/전체결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/README.md:1), [124개영상목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v3.md:1), [다음미실행−4mm계획](/home/ajou/yigyu/3/stability_adapter_2/BODY9_STRAP_MINUS4MM_PLAN.md:1)에남긴다. Grip/연주/초기p/q복원완료로확대하지않고전체목표를계속진행한다.


## 96. 자유 기타 연주 prior 전이 설계 — 신규 물리 실행 없음

현재 G frame 관측의 기존 fret·strike prior와 66관절 공동 residual을 하나의 최종 목표로 합성하는 계획을 추가했다. 대표 두 checkpoint의 CPU 계약/정규화/이름매핑/입력보존4검사를 통과했으나 source선정·연주성능·actuator동등성을 인증하지 않았다. [설계](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_PRIOR_ADAPTATION_PLAN.md:1), [조사 결과와 기존 이미지/영상 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_prior_adaptation_v1/README.md:1)에 저장했다. README의 이미지와 영상은 이전LA−2mm 작은손목시험을 명시하여 인용하며 이번연주/학습결과로 표시하지 않는다. 신규native/physics/학습/actor추론0, 기존영상모음124개 유지. Luna/독립검수는 도구thread한도로 미완료이며 root가 자체검토했다.


## 97. Strap total−4mm — 같은 손목 동작의 실제5초 비교

−4mm는−2mm보다회전최대2.607665→2.335921°로줄었지만위치최대14.010556→14.023529mm,2s기준후기위치.363488→.404326mm/회전.070089→.079347°로늘었다. Peak법칙장력28.152161→28.097309N이며actual손목진폭은.147836→.149523°다. 손바닥양λ0은유지,검지끝/오른허벅지는5초말접촉기록이남고엄지양λstep수194→163이다. [새실제영상/초기값/3조건그림설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/README.md:1), [후속결정](/home/ajou/yigyu/3/stability_adapter_2/STRAP_MINUS4MM_DECISION.md:1)에남겼다. Actual한1200step/두151frame,분석13검사와독립검수완료. Luna산출물v1의중복범례는원본보존후v2에서보완한다. 영상모음은새v4목록126개이며기존124원본/목록보존. Checkpoint조사schema표시오류도새v2출력으로보완했다. 기타초기p/q복원/그립/연주학습완료를뜻하지않는다.

최종그림은v1/v2를보존한v3로caption/x축겹침까지보완하고root실제PNGQA를통과했다. [최종그림과검증설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/ROOT_VERIFICATION_NOTES.md:1)에범례·단위·미검증범위/후속결정을추가했다. 그림수정에따른추가native실행은0이다.


## 98. 팔·손가락 source 제안과 연주 보정 학습 평가 계획

이번 그림은 LA−2mm의 **기존 Isaac Gym 저장 상태**0/0.1/0.5/5초에서 팔12+hinge6을 조정한 source 형상 계산이다. 새로운 물리 실행이나 실제 candidate 렌더가 아니다. 점은 시계열로 연결하지 않은16배치(4개 baseline+12개 제안)이고, 세로축은 전체 LH:palm과 지정 neck side patch 사이의 거리 상한mm다.

![팔·손가락 제안별 source 손바닥–넥 옆면 간격](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_support_source_v1/artifacts/coupled_support_palm_gap_by_fraction.png)

별표는0.5초의1/4제안 하나만 source 방향 screen을 통과했다는 뜻이다. 간격은9.994144851→9.972901669mm로 약21.243µm 감소했으며 실제 접촉·지지력·안정화 성공은 아니다. t0와5초의 제안은 통과하지 못해 실제 PD 실행으로 채택하지 않는다. 같은 왼손 비인접110쌍도 검사한 v3를 사용했고, v1/v2 문제·소스·출력·로그는 보존했다. [그림과 계산 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_support_source_v1/README.md:1)에 저장했다.

사용자 추가 목표에 맞춘 [학습 평가 계획](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_RESIDUAL_EVALUATION.md:1)은 동결 fret/strike 기준 목표에 하나의66관절 공동 residual을 합성한다. 현재 G 기준 운지·타현 정확도와 초기 world 기타 p/q 유지 성능을 따로 평가하고, 무학습 연결/baseline 검증 뒤 단일 이벤트→전환→짧은 phrase 학습으로 확장한다. 이번 단위의 physics/actor 추론/학습은0이다. 기존 실제 영상126개는 유지한다.


## 99. 손바닥 초기 접근 후보의 실제5초 비교

이번 시험은 초기18각과 대응 PD 유지 목표를 바꾼 **새 실제 Isaac Gym 실행**이다. 기타 초기p/q·LA−2mm·몸통PD×2·고정하체/root와 손목±0.005rad1Hz파형을 유지했다. 초기 최대 변경은 약0.15°다.

![이번 실제 Isaac Gym 초기 손·기타·스트랩](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/native/frames/hands/00000.png)

초기 source 전체palm–neck patch 거리 상한은0.421669522→0.109523083mm다. 이미지에서 가까워 보이는 배치는 native접촉·지지력 증명이 아니며 실제 palm 양의 raw lambda는0이었다. 비인접1188쌍 source검사와 fresh초기14검사를 통과한 뒤1200step을 실행했다.

![이번 실제 Isaac Gym 손·기타·스트랩0~5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/native/hands.mp4)

![실제5초 종료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/native/frames/hands/00150.png)

초기 최대오차14.010556→14.085148mm/2.607665→2.616525°와2초기준 후기변화0.363488→0.373544mm/0.070089→0.072412°로 소폭 늘었다. 새초기각은 미채택하며 기존−2mm를 비교 기준으로 유지한다. 두151frame영상·원nativePNG와13route overlay를 보존했다. [초기값/수치표/그래프설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/README.md:1), [미채택 결정/연주 연결 순서](/home/ajou/yigyu/3/stability_adapter_2/PALM_WITNESS_INITIAL_DECISION.md:1), [영상128개 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v5.md:1)에 기록한다.

현재G 기준 연주 정확도와 초기world G 유지 성능을 함께 개선하는 공동 residual 설계는 유지한다. 완전 palm고정접촉을 선행조건으로 두지 않으며 다음은 checkpoint 선별/무학습 연결계약이다. 이번 actor추론/학습은0이고 source거리 감소를 연주 또는 초기p/q복원 성공으로 해석하지 않는다.


## 100. Fret·Strike 후보 평가와 target/history CPU 계약

자유 기타 연주에는 현재 G frame의 운지/피크 목표와 초기 world G p/q 유지 오차를 함께 관측하는 공동 residual을 권장한다. 기존 source는 동결하고60source+Thorax6을 하나의81D PD목표로 합성한다. 이번에는 target/history 하위계약10검사를 통과했으며 전체관측/후처리/actor/physics 연결은 아직 없다. 새 native/physics/학습0, 영상 모음128개 그대로다.

![저장된 Fret F1과 초기손 자세 profile 간격](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/artifacts/playing_bridge_summary.png)

왼쪽은 기존 Fret 전체곡 F1 .100098/.073486으로 낮은 prior 성능을 별도 드러낸다. 오른쪽은 현재 초기q/유지PD가 유효profile까지 필요한 최소 각도차다. 선택된 보정각이나 실제 응답이 아니며 thumb1_y 초기값의 최대차는.661269rad다. 원본 AST와 residual0 차이는 최대2.384e−7rad로 bitwise 동일이 아니다. 네 source의 strictG0 자격은 모두false다. [평가 연결·표·실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/README.md:1)을 참조한다.

![이전 LA−2mm trial의 실제 Gym hands 초기 프레임 재사용](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/native/frames/hands/00000.png)

위 이미지는 이전 −2mm trial의 실제 Gym 초기값으로 이번 CPU phase의 새 렌더가 아니다. 아래도 동일한 이전 actual0~5초 스트랩 영상이다.

![이전 LA−2mm trial의 hands 스트랩 영상 재사용](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/native/hands.mp4)

[후속 결정](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_TARGET_BRIDGE_DECISION.md:1)에 따라 현재 범위 밖6손관절의 초기각/유지목표를 새 후보로 준비하고 fresh native 직접형상 gate와 actual5초를 별도 검증한다. 기존 안정화 결과/체크포인트를 보존하며 학습 시작·연주 성공으로 표시하지 않는다.


## 101. 스트랩 길이 고정·왼팔/손가락18각만 변경한 실제5초

Recent original LA1.1018469719600776m를모든비교에서고정했다. 기존small_wrist_motion_v1와같은기타초기p/q·body9PD×2·root하체fixed·손목±.005rad1Hz조건에서왼팔12+손가락hinge6 초기각/대응PD목표만최대.002616495rad변경했다. Freshnative14게이트와분석17검사를통과했고actual한초기화/1200step/두151frame스트랩영상을남겼다.

![동일 고정LA의 초기world 기타오차 시간곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/artifacts/v2/joint_only_fixed_strap_timeseries.png)

곡선은초기worldG를기준으로한위치norm(mm)/회전각(°)이다. 회색2~5초에서별도계산한2초자세기준실제변위/상대회전은.481766500→.257785610mm/.091929111→.051002962°로각46.49/44.52%줄었다. 초기최대이동14.132608→14.084223mm지만최대회전2.894328→2.920042°로조금늘었다. 작은한후보의후기유지개선이며초기p/q복원·전반연주·반복재현완료는아니다.

![같은LA 새관절후보 실제Gym t0 hands](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/frames/hands/00000.png)

![같은후보 실제Gym t5 hands](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/frames/hands/00150.png)

두이미지는이번실제Isaac Gym초기/종료다. 주황실선/가려진점선은실제13지점passive route이며LA를늘이거나줄이지않았다. 관절이바뀌어route/장력이바뀌는물리효과는유지한다. 두조건palm양의rawλ0/selfcontact0이며시각상접근을지속palm지지/전체동적관통0으로인증하지않는다.

![이번 고정LA·관절조절 실제0~5초 스트랩 hands영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/hands.mp4)

[초기값·두영상·표·그림설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/README.md:1),[결정과다음고정LA방향](/home/ajou/yigyu/3/stability_adapter_2/JOINT_ONLY_FIXED_STRAP_DECISION.md:1),[영상모음130개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v6.md:1)에정리했다. 첫그림검산실패source/로그는보존하고원본metrics를재사용하는v2로보완했으며물리·분석재실행은없다.


## 102. 고정 스트랩에서 어깨 목표만 양방향 조절한 실제5초

초기81각·기타world p/q·LA1.1018469719600776m·몸통PD·고정root/하체를 동일하게 두고 L_Shoulder_y의 유지 목표만±0.008rad 바꿨다. 실제 두 환경을 각각0~5초/1200step 실행하고 초기값·전신/손 영상4개를 저장했다. 기준은 직전 joint_only_fixed_strap_v1의 관절18 초기 후보다.

![고정 LA 어깨 목표 비교의 실제 로그 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/artifacts/fixed_strap_shoulder_response.png)

그림은 실제 trace의 position_error_m×1000(mm)·rotation_error_deg(°)를 초기 world 기타 자세 기준으로 표시한다. 회색은2~5초 평가 구간이며 곡선의 초기오차와 아래 표의2초 기준 후기변화는 서로 다른 지표다. 범례의 Current18은 동일 고정LA의 직전 관절 후보를 뜻한다.

| 조건 | 최대 초기 위치 이탈 mm | 최대 초기 회전 이탈 ° | 후기 위치 변화 mm | 후기 회전 변화 ° |
|---|---:|---:|---:|---:|
| 기준 | 14.084223 | 2.920042 | 0.257786 | 0.051003 |
| −0.008rad | 15.989064 | 2.862553 | 0.794536 | 0.136579 |
| +0.008rad | 11.926351 | 3.169993 | 0.286206 | 0.052761 |

+방향은 위치 이탈을 줄였지만 회전이 늘었고, −방향은 회전 개선이 작으며 위치/후기가 악화됐다. 두 조건을 공동 개선으로 채택하지 않고 기준을 유지한다. 4~5초 단일열 응답의 양·음 불일치가 central norm 대비50.75%여서 범위 밖 최소제곱 목표+.02768rad를 적용하지 않는다. 다음은 다른 손목 축의 응답 비교이며 아직 미실행이다. 이번 결과를 기타 초기p/q복원·최종66 연주 안정화 완료로 해석하지 않는다.

![plus 조건 실제 Isaac Gym t0](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/frames/hands/00000.png)

![plus 조건 실제 Isaac Gym 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/frames/hands/00150.png)

초기q는 두 조건에서 동일하며 목표각만 바뀐다. 주황 실선과 가려진 옅은 점선은 실제13지점 passive 스트랩 경로다. LA는 고정해도 경로·장력은 물리적으로 바뀐다. Palm 양의 raw lambda0/self접촉 기록0이며 완전 손바닥 지지나 모든 동적 관통0을 인증하지 않는다.

![plus 조건 실제0~5초 스트랩 손 근접 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/hands.mp4)

[결과·초기값·4영상·이미지 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/README.md:1), [결정/후속 계획](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SHOULDER_RESPONSE_DECISION.md:1), [영상 모음134개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v7.md:1). 신규actor/학습0, 그림은 저장자료 후처리다.


## 103. 중지의 큰 굽힘은 지속 접촉과 다른 상태

아래는 최근 고정LA·어깨+0.008rad 실행의 저장5초 손 카메라다. 이번 조사에서 새 시뮬레이션이나영상녹화는하지않았다. 손가락이름/허용접촉영역/실제접촉점overlay는아직추가하지않았으며, 이이미지만으로닿는손가락을판정하지않는다.

![기존 actual5초 손카메라 — 중지굽힘 조사에 재사용](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/frames/hands/00150.png)

중지2/3 유지목표는각64.343/60.684°로고정되어있다. 특히중지3은초기60.146°→5초60.684°이며검지/약지/소지3 목표7.991/2.954/33.027°와차이가크다. 모두scalar관절좌표이며전체손가락의해부학적회전각으로합산하지않는다. 현재runner는손가락길이로각도를자동최적화하지않는다. 중지3 양의rawλ기록은.108~.183초의18step(G:fret4)이고2초이후0이다. 반면검지3은1145step으로지속접촉기록의비중이크다. 양의λ부재만으로표면간격이나무접촉을인증하지않는다.

[관절/접촉표와원자료설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_curl_diagnosis_v1/README.md:1),[접촉영역표시/자세평가계획](/home/ajou/yigyu/3/stability_adapter_2/FINGER_CONTACT_REGION_PLAN.md:1). 손가락별표시는진단에도움이되지만자세가바뀌려면허용영역·접근방향·분포기반자세선호를실제검색/제어평가에연결해야한다. 길어서중지를이만큼굽혀야만닿는지의반사실실험은아직하지않았다.


## 104. 손가락 원점과 실제 접촉을 구별하는 지도

![기타 local 손가락 연결도와 현재 접촉점](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/artifacts/finger_contact_map_snapshots.png)

기존 어깨+0.008rad 실행의 저장자료로 만든 별도 과학 도표다. 색 선은 손가락1→2→3→top body 원점, 빈 삼각형은top 원점, 검은 테두리 점은 해당step의 양의SDK 접촉 feature다. 현재 접촉 수는0/2/0/1이며 과거 접촉을 현재로 표시하지 않는다. 반투명 front9.3mm/front_outer11.230006mm·후면·옆면은 유한 참조영역이며 실제 cooked 표면/접촉 제약은 아니다.

![동일 저장 실행의 실제 Isaac Gym 5초 손 카메라](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/frames/hands/00150.png)

이 원본 native 이미지의 픽셀은 변경하지 않았다. 위 도표는 카메라 영상 위에 투영한 overlay가 아니며 가림을 새로 판정하지 않았다. 중지3 접촉은초기18step뿐이고5초에는검지3 feature가있다. 큰굽힘을지속지지로해석하지않는다. 손끝원점과실제접촉이약5.8mm차이나므로 실제패드영역확인후목표를만들어야한다.

[그림·좌표·관절분포 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/README.md:1),[후속 한관절시험 결정](/home/ajou/yigyu/3/stability_adapter_2/FINGER_CONTACT_MAP_DECISION.md:1). 중지길이가더길다는모델원점기하와필수굽힘각은구분한다. 자연성은표시만으로달성되지않으며분포기반soft선호와실제접촉평가에연결한다. 다음middle3−.05rad시험은미실행이며이번새물리/학습0이다.


## 105. 자연스러운 연주를 우선하는 허용 범위 제안

사용자 변경에 따라 초기 기타p/q를정확히복원하는목표를완화한다. 첫작업기준은초기위치대비30mm/상대회전5°이고후기연속1초변화5mm/1°다. 이값은영상검토용제안이며검증된자연자세/연주성공기준이아니다. 구역안에서는초기점으로복원하는비용을0으로두는설계를제안하되연주오차·drift·부자연스러운손가락/손목자세는별도평가한다. 새reward/controller/물리실행은없다.

![기존 고정LA관절18 후보의 실제Isaac Gym5초 장면 재사용](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/frames/hands/00150.png)

위이미지는새실행이아닌기존저장프레임이다. 기존최대초기이동14.084223mm/회전2.920042°는제안된30mm/5°구역안에들어간다. 그러나손자세/연주가능성은별도이고후기연속1초지표도아직재계산하지않았으므로자연스러운연주성공으로표시하지않는다. 기존2초기준후기변화값을새1초지표로바꾸어부르지않는다.

[새메인설계](/home/ajou/yigyu/3/stability_adapter_2/NATURAL_PLAYING_ENVELOPE.md:1),[설명·변경파일](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/natural_pose_criteria_v1/README.md:1). 스트랩은확인된현재값1.1018469719600776m를고정하고사용자가말한다른환경출처는확인중이다. 길이탐색/route기반자동재설정은하지않는다. 기존기록은보존하며기타자유물리·고정root하체·몸통목표·최종66권한은유지한다.


## 106. 고정 스트랩 네 기록의 허용 구역·연속1초 유지 재평가

![초기오차와 후기1초창 변화를 임시허용치로 나눈 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/natural_envelope_assessment_v1/artifacts/natural_envelope_limits.png)

저장자료로만그린별도그래프다. 가로축은임시허용치에대한비율이며점선1이각30mm/5°/5mm/1°다. 막대끝은실제최댓값의단위다. 후기창은시작2~4초/60Hz121개각241표본의시작자세대비최대변화이며이전2초단일기준변화와다르다. 네기록각초기구역밖0/1201표본·후기구역안121/121창이다. 임시범위내관측이지자연자세/실제연주성공인증은아니다.

관절18의후기1초최대.455912mm/.084049°,어깨+는.292116mm/.052998°다. 따라서미세초기오차축소보다손가락자세/연주접근성시험을우선한다. 어깨+기록도후보로보존하되다음중지3−.05rad는관절18기준에서단독변경하며아직미실행이다.

![재사용하는관절18실제Gym5초손프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1/native/frames/hands/00150.png)

이프레임과기존영상은새녹화가아니다. 손자세·palm접촉·손6 source-profile호환·fret/strike기능과학습은여전히별도검증대상이다. [재평가표·그림설명·기존영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/natural_envelope_assessment_v1/README.md:1),[후속결정](/home/ajou/yigyu/3/stability_adapter_2/NATURAL_ENVELOPE_ASSESSMENT_DECISION.md:1). Rawpose/trace·독립SO(3)26검사완료,이번새물리/actor/학습0. 절대LA1.1018469719600776m는고정하고다른환경출처는pending이다.


## 107. 고정 스트랩에서 중지3 유지목표를 조금 펴는 실제5초 비교

초기81각/기타p·q/LA1.1018469719600776m/몸통PD·손목파형은기준과같고중지3유지목표만−.05rad바꿨다. 초기손모양변경은아니다. 아래별도그래프의왼쪽은실제scalar중지3각과점선유지목표,오른쪽은후기1초최대변화를임시5mm/1°로나눈비율과점선한계1이다.

![중지3 실제각과 기타 후기1초 유지 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/artifacts/middle_relax_native_summary.png)

중지3은5초실제60.684291→57.820850°로펴졌고후기1초창최대위치.455912→.437298mm/회전.084049→.081147°다. 두조건모두임시초기30mm/5°밖0/1201표본·후기5mm/1°안121/121창이다. 이전2초단일기준변화는.257786→.298139mm/.051003→.058458°로늘었다. 서로다른지표이며모든값개선이나자연스러운연주성공으로판정하지않는다.

![새실행 실제Isaac Gym 시작 손장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/native/frames/hands/00000.png)

![새실행 실제Isaac Gym 5초 손장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/native/frames/hands/00150.png)

원본native프레임은보존하고실제13지점스트랩경로만표시했다. 실선/가려진점선은표시이며천mesh추가가아니다. 시뮬레이션마지막은5.000초이고두151frame/30fps영상의파일길이는5.033333초다. 이번actual은CPU PhysX이며로그의CUDA/visual geometry경고도보존한다.

![중지3완화 실제0~5초 스트랩 손영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/native/hands.mp4)

중지3양의rawλ step15→14/검지3 1154→1154이며palm양의λ는없다. 초기source검사통과와self-contact기록0을모든동적cooked관통0/완전palm지지로해석하지않는다. [초기값·결과표·두영상·이미지설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v1/README.md:1),[후속결정](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_MIDDLE_RELAX_DECISION.md:1),[영상모음136개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v8.md:1). 작은완화에서유지가무너지지않은후보로보존하며다음total−.15rad는미실행이다. 자연성/연주기능/학습은남아있고길이조절은하지않는다.


## 108. 중지3 목표 총−0.15rad — 더 펴도 기타 유지는 비슷한 범위

![세조건 중지3 실제각과 후기1초 유지 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/artifacts/middle_relax_v2_native_summary.png)

저장raw자료의별도과학도표다. 왼쪽실선은scalar중지3실제각,같은색점선은유지목표이고오른쪽점선1은후기1초5mm/1°임시한계다. 새목표52.089980°/5초실제52.090865°로직전57.820850°보다펴졌다. 후기완전1초최대는기준/−.05/−.15에서.455912/.437298/.437387mm 및.084049/.081147/.080289°다. 직전보다새위치변화가0.000089mm커모든값단조개선이라고하지않는다. 이전2초단일참조값은별도로결과표에남겼다.

![이번실제Isaac Gym 시작 손장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/native/frames/hands/00000.png)

![이번실제Isaac Gym 5초 손장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/native/frames/hands/00150.png)

이번에도초기81각/G p·q/LA1.1018469719600776m/다른80목표·PD는같고유지목표만바꿨다. 그림생성은native픽셀을수정하지않았으며주황선은실제13route스트랩표시다. CPU PhysX/로그경고보존·새1초기화1200step5.000초·두151frame30fps영상이며파일길이는5.033333초다.

![중지3 총−0.15rad 실제0~5초 손영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/native/hands.mp4)

새중지3양의rawλ50step과약지3 19step은초기.333초이내에만있고2초이후0이므로후기지지개선이라고하지않는다. 각조건임시초기구역밖0/1201·후기1초안121/121이며자연성/연주성공인증은아니다. 중지2약64.34°는관측soft분포안이므로크기만으로펴지않는다. 다음은초기중지3각을현재52.09°목표에맞추되같은최종절대목표를제출하는한후보로,아직미실행이다. [세조건표·초기값·두영상·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/README.md:1),[후속결정](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_MIDDLE_RELAX_V2_DECISION.md:1),[영상모음138개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v9.md:1). 실제연주/손6호환/학습미완료,고정길이와최종66권한을유지한다.


## 109. 중지3 초기각 정렬 — 손 목표 오차와 기타 움직임의 차이

![초기각·초기 기타 변화·후기 유지의 두조건 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/artifacts/initial_middle3_alignment_summary.png)

저장 원자료로 만든 별도 과학도표다. 파랑은 기존 초기60.145874°에서 유지목표52.089980°로 움직이는 조건, 주황은 처음부터52.089980°로 배치한 조건이다. 모든81관절의1200개 최종 명령은 동일하다. 왼쪽 위 점선은 공통 유지목표이며 오른쪽 아래 점선1은 후기1초 변화의 임시5mm/1° 한계다. 초기 기타 위치·회전 패널은0~0.5초 양끝 포함121표본, 후기창은2~4초에서60Hz로 시작하는121개 각241표본이다.

초기 중지3 목표 오차는8.055894→0°로 줄었지만 기타의 최대 초기 이동은14.077232→14.608483mm, 후기1초 최대변화는.437387→.648625mm 및.080289→.115306°로 늘었다. 초기0~.5초 최대선속도.129085→.137609m/s와 각속도.527685→.557034rad/s도 늘었다. 따라서 기타 안정성 개선으로 채택하지 않고 기존 quiet 비교 기준과 새 초기자세 후보를 함께 보존한다. 두조건 모두 임시초기30mm/5°와 후기1초5mm/1° 안이지만 자연성·연주성공 인증은 아니다.

![새초기각 실제Isaac Gym 시작 손장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/frames/hands/00000.png)

![동일명령 실제Isaac Gym 5초 손장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/frames/hands/00150.png)

중지3 초기q와 대응offset만 바꾸고 다른80초기q/G p·q/PD/절대LA1.1018469719600776m/몸통목표/root하체고정은 유지했다. 원native PNG와 실제13route 스트랩 표시 PNG를 각각 보존했으며 주황 스트랩 표시는 천mesh 모델이 아니다. 이번actual은 CPU PhysX 한초기화1200step5.000초다. 두151frame/30fps 영상의 파일길이는5.033333초이고 CUDA/visual geometry 경고는 로그에 남겼다.

![초기중지3정렬 실제0~5초 스트랩 손영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/hands.mp4)

새중지3 양의rawλ91step은.133~.508초, 약지3 38step은.150~.304초에 있으며 두관절 모두2초이상0이다. 접촉행수를 힘N/지지품질로 해석하지 않는다. Palm 양의λ없음/self접촉기록0과source gate통과도 모든 동적 cooked관통0을 증명하지 않는다. [결과표·초기값·두영상·그림설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/README.md:1), [후속결정](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_MIDDLE3_ALIGNMENT_DECISION.md:1), [영상모음140개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v10.md:1). 다음은 현재 두후보의 fret·strike source/native/normalized 범위 CPU재조사이며 아직 미실행이다. 최종66권한·고정길이·자유기타를 유지하고 실제연주/학습은 계속 검증할 대상이다.


## 110. 현재 고정LA 손자세와 연주source 범위의 차이

![현재두초기자세·공통유지목표의범위까지최소변경](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/artifacts/fixed_strap_source_range_changes.png)

이번저장자료의별도과학도표다. 파랑은기존held-only실제초기각,주황은처음부터middle3를52.09°로맞춘실제초기각,초록은두조건의공통유지목표다. 각막대는source/native/normalized 교집합까지의signed 최소변경rad를도로바꾼값이다. 양수는관절값증가,음수는감소이며0의빈원은현재값이이범위안이라는뜻이다. 실제로적용한보정이나필요한해부학bone회전·접촉/관통예측이아니다.

원본fret47,000/strike10,000 계약·MJCF·fretprofile을재계산하고기존bridge float32mapping과exact대조했다. 두조건각5종류×81개총810행에서기존실제초기6개/정렬초기5개가범위밖이고유지/명령최소·최대는양쪽각5개다. 남은LH thumb1_x/y,thumb3,index1_x,ring1_x중최대차는thumb1_y초기37.887910°/유지35.388621°다. Thumb3초기차34.524578°는이전LA−2mm조사의숫자를승계한것이아니다. 중지3의기존초기차−4.789270°는새초기/held에서0이됐다.

![이번계산에사용한이전초기52.09도후보의실제Gym프레임재사용](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/frames/hands/00000.png)

이Gym프레임은직전actual실험에서저장한이미지를재사용했으며새로운5손관절후보렌더가아니다. 이번작업은CPU34검사/48입력·48사본/그림14직접입력·14사본이고새native/physics/actor추론/학습은0이다. 기존140개영상모음도그대로다. 현재held를bridge에넣으면두조건모두거절했고원본strictG0자격false를그대로보존했다. Source범위차이는해부학적잘못판정이아니며Strikepickgrip/Fretstage후처리·전체관측runtime·연주기능은별도검증한다.

[결과표·그림설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_compatibility_v1/README.md:1), [결정](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SOURCE_COMPATIBILITY_DECISION.md:1), [다음초기배치계획](/home/ajou/yigyu/3/stability_adapter_2/FIXED_STRAP_SOURCE_HAND_INITIAL_PLAN.md:1)에남긴다. 다음은다른76관절/목표·G p/q·LA/PD/root하체를보존하고위5손관절의초기/유지각만가까운유효경계안쪽으로바꾼한후보의fresh native 직접gate다. Gate실패는0step실제초기이미지로,통과는같은초기화5초/두스트랩영상으로기록할계획이며아직미실행이다. 기존18조건부FK를finger1다축인증에확대하지않는다.

§110의 기존초기 middle3 최소변경을 소수6자리로 표시하면 **−4.789271°**다. 위문단의−4.789270° 표시는 이값으로 정정한다. 원자료는−0.08358854055404663rad이며 그래프/원자료 파일은 변경하지 않았다.


## 111. 같은 시작 자세에서 스트랩 cable force를 끈 실제 5초

이번 separate trial은 초기20개 공통필드와 81×1200 command를 앞선 strap-on 기준과 exact 유지했다. 분석기의 `all21_initial_fields_exact`는 legacy check 이름이며 실제 비교목록은20개다. CPU PhysX에서 1200step/5.000초를 실행했고, 스트랩 힘과 주황 route overlay를 끄고 explicit force API 호출0회, applied tension은1201개 모두0이다. Raw native PNG302개를 hash exact 확인했다. Nominal LA/route metadata는 비활성 진단값으로 남는다.

| 측정 | Strap-on 기준 | Strap-force off |
|---|---:|---:|
| 최대 초기자세 기준 위치/회전 오차 | 14.608483 mm / 2.918412° | 20.584004 mm / 12.152977° |
| 종료 위치/회전 오차 | 13.819696 mm / 2.918277° | 20.525764 mm / 12.145216° |
| 후기 완전 1초 최대 위치/회전 변화 | 0.648625 mm / 0.115306° | 0.335897 mm / 0.064720° |
| 초기 임시 30 mm/5° 범위 밖 | 0/1201 | 1145/1201 (회전초과) |
| 후기 임시 5 mm/1° 창 안 | 121/121 | 121/121 |

스트랩이 없을 때 후기 변동은 더 작지만 기타는 초기 기준에서 크게 돌아간 다른 자세에 머문다. 이 run에서는 strap-on이 초기 회전 억제에 도움을 보였으며, no-strap 후기 창 통과를 초기 자세 유지나 안정화 성공이라고 부르지 않는다. Source14/1188 통과는 cooked geometry의 동적 침투 cert가 아니며 임시 기준은 자연스러움/연주 성공을 인증하지 않는다. 저장자료 대조는 초기20필드와 전체 81×1200 명령을 exact 확인했다.

![스트랩 힘을 끈 실제 t=5초 손 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/frames/hands/00150.png)

![스트랩 힘이 없는 실제 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/hands.mp4)

![스트랩 힘이 없는 실제 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/whole_body.mp4)

[한국어 수치·초기/종료 프레임·영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/README.md:1), [영상모음 v11·142개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v11.md:1)에 정리한다. 새 actor inference/학습은 없다.


## 112. 고정 스트랩 손 초기값 후보의 fresh native 형상 거절

![초기 손자세 fresh native t=0 손 카메라](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/frames/hands/00000.png)

![초기 손자세 fresh native t=0 전신 카메라](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/frames/whole_body/00000.png)

다섯 손 관절 초기값·유지목표를 source/native/normalized 범위 안으로 옮긴 뒤 준비 검사 9개는 통과했지만, fresh native 직접 검사 15개 중 `source_human_guitar_clear`가 실패했다. LH:thumb2–기타의 LP 공통 내접 반경은 4.288365 mm이며 PhysX 관통 깊이가 아니다. 나머지 14개 검사와 self-screen 1,188쌍은 통과했다.

실행은 초기화 1회, physics 0 step에서 의도된 형상 gate 거절로 끝났다. 두 MP4는 각 1프레임·30fps·0.033333초 partial이므로 5초 기록이 아니다. 후보를 채택하지 않았고 5초 기타 안정성이나 자연스러운 연주 여부는 미측정이다. [상세 결과와 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/README.md:1) · [다음 엄지2 clearance 계획(미실행)](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_THUMB2_CLEARANCE_PLAN.md:1).


## 113. 엄지2 단일축 source sweep의 교집합 잔류

![저장된 일곱 scalar source 조건의 thumb2–기타 LP 공통 내접반경](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2/artifacts/thumb2_source_radius_sweep.png)

이 도표는 saved source LP 값만 나타내며 native 렌더나 동적 PhysX 결과가 아니다. x축은 실제 float32 thumb2 scalar 변화, y축은 thumb2–기타의 LP 공통 내접반경이다. 0/±0.05/±0.1/±0.2 rad 일곱 표본 모두 source intersection이 남았다. 기준 4.288365 mm에서 −0.2 rad의 3.054824 mm까지 줄었지만 0이 되지 않았고, 이 표본 구간만으로 전체 관절범위의 불가능성을 증명하지 않는다. 이 반경은 PhysX 관통 깊이가 아니다.

![직전 source-hand phase의 실제 Gym t=0 손 프레임 재사용](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/frames/hands/00000.png)

두번째 이미지는 직전 실행에서 저장된 장면의 재사용이며 이번 7개 source 조건의 렌더가 아니다. 새 native/physics/actor/학습은 0회, 5초 안정성 측정은 없다. [수치표·실행 범위·다음 미실행 계획](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2/README.md:1).


## 114. 엄지 기저부 네 실제 초기 pose의 source 반경

![기준 및 네 fresh native t=0 pose의 thumb2–기타 LP 공통 내접반경](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb_base_native_v1/artifacts/thumb1_base_native_source_radius.png)

기준 반경 4.288365 mm보다 네 조건의 값은 모두 커졌다. 네 fresh native 검사 모두 source human–guitar gate만 거절했고, 나머지 14개 검사는 통과했다. 각 실행은 1회 초기화 후 0 physics step에서 끝났다. LP 공통 내접반경은 PhysX 관통 깊이나 실제 동적 접촉 측정이 아니다. 후보 선택이나 5초 안정성·자연스러움·연주성 평가는 하지 않았다.

![thumb1_y +0.05 조건의 실제 native t=0 raw 손 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb_base_native_v1/native/thumb1_y_plus005/raw/frames/hands/00000.png)

이 raw frame은 이번 후보 초기화에서 저장한 t=0 카메라 이미지다. 총 8개 저장 video는 한 프레임짜리 partial로 5초 녹화가 아니다. [수치와 이미지 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb_base_native_v1/README.md:1) · [다음 손목 조사 계획(미실행)](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_WRIST_CLEARANCE_PLAN.md:1).


## 115. 손목 13 source 조건의 교차 반경과 추가 손–기타 쌍

![기준 및 12개 손목 offset의 thumb2/기타와 나머지 HG 쌍 반경](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_wrist_clearance_v1/artifacts/wrist_source_clearance_radii.png)

도표는 13개 conditional source 조건의 정적 LP 보고만 나타낸다. 13개 모두 thumb2–기타 쌍이 남았다. Wrist_y −0.10 rad에서 thumb2 반경은 0.815476 mm로 줄었지만 palm–기타 반경 2.076522 mm와 손가락/fret 교차를 포함해 HG 쌍은 총 6개다. 주황색 ‘none’은 추가 쌍이 1e−7 m 보고 임계값을 넘지 않았다는 뜻이지 실제 거리가 0이라는 뜻이 아니다. LP 공통 내접반경은 PhysX 관통 깊이나 contact certificate가 아니다.

![이전 fixed-strap 실행의 실제 t=0 손 프레임 재사용](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/frames/hands/00000.png)

이번 source sweep은 새 native 실행·동역학·영상 없이 끝났으며 안정성은 측정하지 않았다. 위 프레임은 기존 실제 Gym 장면을 설명용으로 재사용했다. [전체 수치 및 다음 팔 위치 계획(미실행)](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_wrist_clearance_v1/README.md:1) · [152개 기존 영상 모음(v13)](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v13.md:1).

## 116. 단일축 팔 변경 74제안의 source 형상 반경

두 손목 seed(0, −0.1 rad)의 기준행 2개와 숫자 범위 안 66개 제안, 총68개 source 형상 행을 공통 축 범위로 그렸다. Thorax_x −0.05/−0.025와 Thorax_y +0.05 rad는 각 seed에서 숫자 범위를 벗어나 geometry 전에 제외되어 선의 빈 점으로 남겼다. 이 여섯 공백은 0이 아닌 범위 제외다. 공유 x축 formatter 때문에 dagger 문자가 tick에 표시되지는 않으며 README에 제외 위치를 적었다.

![두 wrist seed의 팔 단일축 HG 최대 LP 반경](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_position_v1/artifacts/arm_source_geometry.png)

원 seed의 최소 행은 Thorax_y +0.025 rad, 최대 HG 반경 2.212093 mm다. Wrist_y −0.1 rad seed의 최소 행은 Thorax_z +0.025 rad로 최대 1.231576 mm/palm–G 1.079516 mm이며 다섯 HG 교차쌍이 남았다. 68개 전부 source HG 교차가 있고 양손 간 형상 검사와 self 1,188쌍 검사는 clear였다. Source LP 공통내접반경은 PhysX 관통깊이·실제 접촉·안정성 인증이 아니다. 선택 후보 및 새 native/physics/actor/training은 없고 5초 안정성도 측정하지 않았다.

## 117. 팔 연속 source 탐색 800평가의 현재값과 running minimum

두 독립 seed를 각 400회 평가했다. 두 번째 seed 시작점은 Wrist_y −0.1 rad에 Thorax_z +0.025 rad를 포함한 이전 row47 source 가설이다. 옅은 점은 각 평가의 최대 HG 공통내접반경, 굵은 선은 그 값의 seed별 누적 최솟값이다. Seed 0은 weighted objective 최저가 row398, 최대 HG 반경 최저가 row260으로 서로 다르다. Seed 1은 두 값의 최저 행이 row798로 같다.

![두 bounded Powell seed의 HG 반경 progress plot](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_arm_continuous_v1/artifacts/arm_continuous_progress.png)

두 실행은 모두 400 평가 상한에 도달했으며 수렴 성공이 아니다. 800행 모두 HG 교차가 남았다. 양손 간 형상 검사와 self 1,188쌍 검사는 이번 800개에서 미측정이다. Source-only 진행도이며 clear 후보·native/physics 실행·5초 안정성 측정은 없다. LP 값은 PhysX 관통 깊이가 아니다. 저장 분석 첫 시도의 목적값 산술 허용치 문제는 보존된 source를 수정하지 않고 v2 분석에서 다시 계산했다.

## 118. Quiet LH:index3 양방향 목표 보정의 두 완료 5초 응답

기존 quiet 초기값과 strap 조건을 유지하고 LH:index3 목표만 2.0~2.5초에 ±0.005 rad ramp한 뒤 5초까지 유지했다. 첫 minus는 step152에서 SIGSEGV(−11)였고, 152 observed step 및 완성 19frame(t0..0.6초) partial은 완료 trial과 분리 보존했다. 동일 minus 재시도와 plus는 각1200step/151frame의 실제5초를 완료했다. 총3회 초기화에서 완료 physics2400step과 실패 관측152step을 따로 센다. 원인 미확인인 첫 SIGSEGV를 제어 실패로 해석하지 않는다.

47개 저장분석 검사가 통과했다. 두 완료 trial 모두 20공통초기필드, 0~2초 native state/trace, 다른80개의 1200개 목표, 첫484개 전체81목표가 기준과 exact이며 step485에서 처음 분기했다. 종료오차 baseline은13.819696mm/2.918277°, plus13.750278mm/2.921428°, minus13.887982mm/2.916812°다. Plus는 종료 위치가 약0.069418mm 줄고 회전오차는0.003151° 늘었다. Minus는 위치오차가 약0.068286mm 늘고 회전오차가0.001465° 줄었다. 끝점 위치와 회전이 동시에 줄지 않았다. 후기 완전1초창 최대변화 baseline .648625mm/.115306°, plus .685555mm/.124373°, minus .604995mm/.106007°다. 이는 작은 index3 축응답이며 자연스러운 연주·전역 Jacobian·feedback gain의 인증이 아니다.

![baseline과 두 완료 trial의 기타 초기오차, index3 실제각/PD 목표, baseline 대비 world 위치 차이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/artifacts/v2/quiet_index_support_response.png)

그림은 실제 state 1201개(t=k/240초)와 post-step 목표 1200개(step 1..1200)를 정렬해 보인다. 목표 갱신은60Hz held control이다. 최초 plot의 범례가 plus plateau를 가려서, 소비된 v1 파일을 보존하고 계산·데이터를 유지한 별도 v2 plot에서 범례 위치만 옮겼다. 가로축·시계열과 raw lambda 접촉 기록은 analysis/series에서 감사할 수 있다. [phase 결과와 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_index_support_authority_v1/README.md:1), [v14 영상 모음(158개)](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v14.md:1)에 t0/t5 실제 Gym frame, 4개 완료 영상, 2개 crash partial을 구분해 기록했다. Native 관절한계 초과는 세 완료 기록 모두 약0.000099950rad이며 목표 범위 통과와 실제각의 완전 준수는 구분한다. Palm 양의접촉은 없고 raw lambda는 힘·force closure 증명이 아니다.

## 119. Quiet L_Wrist_y 목표 양방향 보정 — 저장 baseline과 두 실제 5초 응답

![기존 기준선과 새 Wrist_y 양·음 목표 변화의 기타 오차, 실제각·PD 목표 및 기준선 대비 위치](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/artifacts/quiet_wrist_support_response.png)

기준은 기존 저장 native이며 이번 세 번째 물리 실행이 아니다. 두 새 조건은 L_Wrist_y 유지 목표에 2.0~2.5초 ±0.005 rad ramp를 더하고 5초까지 유지했다. 각 1200step/151frame을 완료했고 저장 분석42검사가 통과했다. 종료 위치·회전 오차는 기준13.819696mm/2.918277°, plus14.026170/2.931572°, minus13.634644/2.907466°다. Minus 종료값은 작지만 후기1초 최대변화 .676770mm/.124564°가 기준 .648625/.115306°보다 크며, plus의 종료 오차도 커졌다. 이 축의 작은 접촉 의존 응답은 전역 Jacobian·자연 연주·feedback gain 또는 정책 호환성을 인증하지 않는다.

2초 전 quiet 공통구간은 응답 비교용 진단 구간이지, 연주에 WAIT→REACH→GRIP→TRANSPORT를 필수 선행 단계로 추가한 것이 아니다. 주요66관절 권한은 환경에 유지되고 이번 trial만 L_Wrist_y 목표를 별도로 held했다. Actual각은1201상태(t=k/240초), post-step PD 목표는1200표본(t=1..1200/240초)이며 명령은60Hz로 held된다. 4개 영상은 두 조건의 손·전신 카메라 실제 스트랩 장면이고각151frame/30fps/5.033333초 재생, 마지막 시뮬레이션 표본은5.000초다. [결과·초기값·t0/t5 frame 및 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_support_authority_v1/README.md:1)과 [162개 영상 index v15](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v15.md:1)을 추가했다. 저장 raw lambda는 힘N/force closure가 아니며, root·하체 고정과 body9 held PD 목표를 actual 몸통 고정으로 혼동하지 않는다.

## 120. Quiet L_Wrist_z 목표 변화 — 저장 baseline과 두 실제 5초 응답

![기존 저장 baseline과 두 새 Z 조건의 기타 초기 world 위치·회전 오차, L_Wrist_z actual/PD 목표, baseline 대비 기타 world 위치 거리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/artifacts/quiet_wrist_z_support_response.png)

이번 native 실행은 plus/minus 각각 ONE initialization, 1200 physics step/151 frame으로 총 2 initialization/2400 step이며 constraint violation 0, actor 추론·학습 0이다. baseline은 기존 quiet trial의 저장자료여서 새 세 번째 실행이 아니다. 시작 L_Wrist_z actual −0.2735629 rad, held PD target −0.4212334 rad에서 Z 목표만 2.0~2.5초 동안 ±0.005 rad ramp하고 5초까지 유지했다. 42개 결과 검사와 body9 별도 7개 검사가 모두 통과했다. 20개 공통 초기 필드, 0~2초 상태 trace, 나머지 80관절의 전체 1200 목표 및 첫 484개 전체81관절 명령은 exact이며 처음 달라지는 상태는 step485다. 이 공통구간은 비교 진단용이다. WAIT→REACH→GRIP→TRANSPORT를 연주 전제에 추가하지 않았고 기존 66관절 권한을 유지했다.

| 조건 | 종료 위치 오차 (mm) | 종료 회전 오차 (°) | 후기 완전1초 최대 위치 변화 (mm) | 후기 완전1초 최대 회전 변화 (°) |
|---|---:|---:|---:|---:|
| 기존 저장 baseline | 13.819696 | 2.918277 | 0.648625 | 0.115306 |
| L_Wrist_z +0.005 rad | 13.817638 | 2.895722 | 0.572182 | 0.104704 |
| L_Wrist_z −0.005 rad | 13.829543 | 2.946758 | 1.056584 | 0.171364 |

Plus의 위치 오차 개선은 0.002058 mm에 불과하지만 종료 회전오차와 후기변화도 조금 낮았다. Minus는 종료오차와 후기변화가 악화했다. 실제각 한계 초과 최대 0.000099949539 rad는 모든 조건에서 같았다. raw lambda는 힘(N)이나 force closure 증거가 아니며 palm의 양의 raw 접촉은 없었다. index3는 각1156 step, thumb3는 587/597/547 step, R_Hip은 1200 step에서 양의 raw lambda가 보고됐다. 몸통9 목표는 held됐어도 실제 Spine_z 변화 최대는 baseline/plus/minus 0.061757788/0.061759546/0.061762825 rad(약3.54°)이며 이는 세계 몸통 SO(3) 각도가 아니다.

그림은 저장 `series.json`의 기타 초기 world 위치오차(mm), 초기 world 회전오차(deg), L_Wrist_z actual(rad)과 post-step PD target(rad), 그리고 plus/minus와 저장 baseline 기타 world 위치의 동시점 거리(mm)를 2×2로 표시한다. Actual 1201점은 t=k/240 s, post-step 목표 1200점은 t=1..1200/240 s이고 명령은 60 Hz held다. 캡션과 선은 원자료를 표시하며, 그림은 실제 Isaac Gym 렌더가 아니다. [결과 README와 t0/t5 실제 PNG·4개 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/README.md:1), [166개 영상 index v16](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v16.md:1)에 실제 native 자료를 정리했다. 네 영상은 각151 frame/30 fps/5.033333초 재생이며 마지막 simulation 표본은5.000초다. 주황 경로 overlay는 strap route이며 천 mesh가 아니다.

저장 Y/Z 응답을 합친 v2 비교 6개 검사는 통과했다. 비교스케일 0.03 m/5°를 적용한 6×2 행렬은 rank2, cosine −0.728127296, condition 2.719646212였고, 이는 두 저장 local 응답의 수학적 관계이지 제어기 인증이 아니다. bounded least-squares δY=−0.005, δZ=+0.005 rad의 종료오차 13.635786789 mm/2.882135324°는 아직 측정되지 않은 모델 예측이다. 이전 v1 계산은 baseline inventory를 잘못 가정해 KeyError로 중단했으며, 실행 소스 사본, 입력 전후 SHA 기록과 failure 기록을 보존했다. 다음 계획은 기타 world 오류에서 Y/Z 목표 delta를 60Hz로 적분하고 ±0.005rad 및 0.002rad/s로 제한하는 것이다. κ=0.00242502989755426 rad²/s는 baseline t2g_ref에서 고정한다. OFF/ON 두 실제 실행은 아직 구현·실행하지 않았고 자연 연주·policy 호환성·폐루프 안정성도 인증되지 않았다. 상세 자료는 [저장 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/analysis.json:1), [body9 진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/body_motion.json:1), [비교 계산](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/comparison_v2.json:1), [Root 검수 노트](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/ROOT_VERIFICATION_NOTES.md:1)에 있다.

## 121. 기타 world 오차 feedback Y/Z 보정 — OFF/ON 두 실제 5초 응답

![기존 저장 baseline, 기타 오차 feedback OFF/ON의 초기 오차, Y/Z 보정 delta와 baseline 대비 world 위치 거리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/artifacts/quiet_wrist_yz_feedback_response.png)

기존 baseline을 저장자료로 재사용했고 새 물리 초기화는 OFF/ON 두 번뿐이며 각각 1200 step/151 frame, 총2400 step이다. constraint violation·actor inference·training은 0이고 analysis 56 checks가 모두 통과했다. 두 새 trial은 root/하체 고정, 자유 기타, 동일한 기타 world 목표·PD·절대 LA `1.1018469719600776 m`, body9 KP×2/KD×√2, 원래 Wrist_x 사인 목표와 손가락 목표를 유지했다. ON은 현재 기타 world 위치/방향 오차에서 Y/Z 손목 목표를 60Hz로 보정했다.

| 지표 | OFF | ON |
|---|---:|---:|
| 종료 기타 위치 오차 (mm) | 13.819696226 | 13.665215004 |
| 종료 기타 회전 오차 (°) | 2.918276977 | 2.889312725 |
| 후기 완전1초 최대 위치 변화 (mm) | 0.648624665739 | 0.693968455 |
| 후기 완전1초 최대 회전 변화 (°) | 0.115306041 | 0.124492483 |

ON은 종료 위치·회전 오차가 소폭 줄었고 후기 변화량은 미세하게 커졌다. 최대 초기 위치 오차는 14.608483313 mm로 동일하며, ON 최대 초기 회전 오차는 2.897193091°였다. ON 최종 delta는 `[-0.005,+0.003548712221559195] rad`, 최대 유효 rate `0.002000000000000014 rad/s`(부동소수점 roundoff)였다. 이 한 조건만으로 성공 또는 폐루프 안정성을 인증하지 않는다.

OFF 전체 native states/trace/81개 목표는 기존 baseline과 exact하게 같았다. ON은 첫484개 전체명령, 앞2초상태/trace, 다른79개 목표 및 모든 손가락 목표가 baseline과 exact하며 첫 다른 상태는 step485다. OFF와 ON은 각각 fresh 15-check direct-source gate 및 1188 self-screen pair 검사를 통과했다. Palm 양의 raw lambda 접촉은 0, thumb3 양의 접촉 step은 587→603, index3는 양쪽 1156이며 raw lambda는 힘(N)이나 force closure 증명이 아니다. native 실제 관절 제한 초과 최대는 양쪽 `0.000099949539 rad`로 같다. body9 PD 목표는 held됐지만 actual `Spine_z` 좌표 변화는 OFF/ON `0.061757788/0.061760515 rad`였으며 세계 몸통 회전각이 아니다. 66관절 권한은 환경에 유지된다.

Plot은 baseline/OFF/ON의 기타 초기 world 위치 오차(mm)·회전 오차(deg), ON/OFF Y/Z 보정 delta(rad), 두 trial과 동시점 저장 baseline의 기타 world 위치 거리(mm)를 네 패널에 표시한다. 오류와 위치 거리는 각1201점 `t=k/240 s`, feedback target/delta는 1200 post-step 점 `t=1..1200/240 s`이며 60Hz held command를 표시한다. 이 이미지는 저장자료 과학 도표이지 Gym 장면 렌더가 아니다. Root는 실제 PNG와 네 영상의 단위·캡션·곡선/범례·ffprobe 결과를 확인했다. [결과와 실제 t0/t5 손·전신 프레임 및 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/README.md:1), [영상 index v17·총170개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v17.md:1)에 담았다.

Collection wrapper는 네 영상과 index v17/update v16을 만든 뒤 마지막 metadata Python 인자 unpack 오류로 terminal exit1이 됐다. 이는 artifact metadata 단계 오류이며 물리 trial 실패가 아니다. collector process의 exit status/wall 값은 저장되지 않았고 collection_execution.json은 존재하지 않는다. 원 wrapper 및 산출물을 유지한 별도 recovery 검사 9개/2178개 입력 SHA가 통과했고, 기존 166개·index와 네 복사본, 총170개와 새 index 이전내용 보존을 exact 대조했다. [wrapper failure와 recovery 상세](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/README.md:1), [회수 감사 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_yz_feedback_v1/collection_recovery.json:1)에 원 wrapper 사건과 이후 검증을 분리해 기록했다.

다음 계획은 동일 각도 bound ±0.005 rad에서 feedback을 0초부터 시작하고 기존 rate의 slow/5배 fast 두 조건을 비교하는 것이다. 아직 구현·실행되지 않았으며 후기 국소 응답만으로 startup 응답을 예측하지 않는다. 자유 기타 연주, 자연스러움, 정책 호환성 및 전체 폐루프 안정성은 미검증이다. [startup feedback 계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_YZ_STARTUP_FEEDBACK_PLAN.md:1).

## 122. 직접 기타 초기 배치 선택 도구

사용자가 키보드로 기타 위치·회전을 고르고 여러 후보를 저장한다. [도구 실행 가이드](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_POSE_EDITOR_GUIDE.md:1)와 [결과 문서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/README.md:1)에 조작법과 검증을 정리했다. 아래는 실제 Isaac Gym native 카메라의 시간0 정적 편집 장면이다. 위쪽 주황색 경로는 고정 길이 스트랩 표시이며 접촉/clearance 검증을 의미하지 않는다.

![기준 배치 — 실제 Isaac Gym 정적 전체 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/native_verification/session/candidate_000/images/frames/whole_body/00000.png)

![6축 기능 확인용 편집 배치 — 실제 Isaac Gym 손 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/native_verification/session/candidate_001/images/frames/hands/00000.png)

편집 후보는 world XYZ에 각각+2mm, world XYZ 회전 각각+1°와 local Z 추가+0.25°를 적용한 기능 검사용 배치이며 권장 자세가 아니다. 편집 중 humanoid 상태와 물리시간0은 유지된다. 실제 Xvfb F3/L 이벤트와 6축·복원·저장/load를 확인했다. 이후 자유 기타의5초 경과는 아래 실제 연속 영상에 남았다. 일정 관절 목표이며 이전 손목 파형/feedback/정책은 실행하지 않는다.

![편집 후보에서 실제0~5초 자유 물리 — 전체](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos/interactive_guitar_pose_v1__preview_000__whole_body.mp4)

![편집 후보에서 실제0~5초 자유 물리 — 손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/videos/interactive_guitar_pose_v1__preview_000__hands.mp4)

1200step·151frame/30fps·영상 약5.033초이며 끝 sim 시간은5초다. 도구는5초 뒤 PREVIEW COMPLETE로 시간이 멈추므로 이를 평형 도달과 구분한다. 원 검증 스크립트 끝 요약 저장에서 np.bool_ 오류/exit1이 났고 원본을 보존했다. 물리·영상은 완료됐으며 별도 정적v2 27검사가 통과했다(추가 물리0). 시작 후 state writes0, 의도된 setter 차단검사1이다. 스트랩 OFF는 정적 표시/raw 녹화 분기만 확인했으며 새 OFF5초 실험은 없다. 자연스러움·관통/접촉·연주 가능성은 이후 사용자 선택과 별도 검증 대상이다.

## 123. 자연스러움 판단용 정적 편집 — 물리 상호작용 없음

사용자정정에따라물리preview를제거한새 [정적도구](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_POSE_STATIC_GUIDE.md:1)를사용한다. 아래는실제IsaacGym native카메라의수동편집기능확인장면이며물리시간0이다. 사람은초기자세그대로이고기타의입력p/q만바뀐다. 그림의주황색선은참고스트랩route표시이며힘을가하지않는다.

![물리없는정적편집전체장면 — 스트랩참고선표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/native/session/candidate_000/images/frames/whole_body/00000.png)

![같은정적배치 — 스트랩참고선숨김](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/native/session/candidate_001/images/frames/whole_body/00000.png)

실제키입력·Space/E무효·gravity0·물리API차단·save/load등18검사를통과했고물리step/trial/새영상0이다. 이기능검사용후보는자연스러운최종선택이나접촉/지지가능성인증이아니다. [결과와이미지설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/README.md:1)을따른다. 이전v1의5초물리영상과혼동하지않으며기존자동실험은중단상태다.

위원OFFharness사진에는viewer의이전주황선이남았다. 원본은보존하며같은입력batch의T/S도안전하게촬영하도록새정적entry에서capture직전선을지운다. 아래는새entry의실제정적OFF사진이다. 중간draw없는T/S저장두시점에서잔류주황pixel0/상태불변/시간0을확인했다.

![최종정적entry에서스트랩참고선OFF저장 — 물리시간0](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/snapshot_verified/candidate_000/images/frames/whole_body/00000.png)

## 2026-10-08 기타 배치 자연스러움의 정적 native30개 비교

물리 스텝0에서 humanoid 자세를 유지하고 기타의 world 이동과 semantic 회전을 비교했다. 기준25개와 조합5개 모두 human body/DOF 상태 동일·추가 렌더 상태 보존을 통과했다. 스트랩은 표시 OFF이며 길이 변경·물리 실행은 없다.
권장 중심은 기존 바디 중심에서 넥22°/관객 방위5°/앞판 눕힘+3°다. 넓은 시각 탐색 구간은 좌우±20mm, 앞뒤·높이-10~+20mm, 넥17~27°/방위0~10°/눕힘0~+5°이며 팔·손 재배치를 전제로 한다. 완전한 조합 영역·접촉·관통·물리적 지지 또는 연주 가능성을 인증하지 않는다.

![정적 추천 기타 배치 — Isaac Gym](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/combined/scene/candidate_000/front.png)

추천 preferred_recline3의 정면 native 이미지. 바디 중심과 넥 방향을 유지하고 앞판을 기준보다3° 눕혔다. 실제 앞판 법선 상승각은약7.97°다. [설명·전체 비교 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/static_guitar_natural_range_v1/README.md:1)와 [설계 권장안](/home/ajou/yigyu/3/stability_adapter_2/STATIC_GUITAR_NATURAL_RANGE_PROPOSAL.md:16)을 따른다.

## 2026-10-08 연주 흔들림 외곽의 최소·중심·최대 native 이미지

world XYZ±50mm, 넥10/22/40°와관객방위-10/5/20°절대각, 앞판눕힘기존기준보정-5/+3/+15°를13정적배치로촬영했다. 물리0·사람상태동일이며팔/손이움직여따라가는장면은아니다. 가운데열은선호중심,양끝열은각축단독끝점이다.

![회전 범위 끝지점 — 실제 Isaac Gym 정면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/artifacts_v2/contact_sheet_rotation_front.png)

[전체6비교표·원본끝점·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_playing_sway_envelope_v1/README.md:1). 연주흔들림을허용할시각적여유제안이며모든조합·동적안정성·접촉/관통검증은아니다. 최초비교표/source의보존누락을결과문서에명시했고,원본native를유지한채현재버전동결후신규v2경로에서6PNG일치를검증했다.

## 2026-10-09 넥 수평·앞판 정면 실제 Isaac Gym 후보

![수평 넥0°·앞판 정면 — Isaac Gym native](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/native/scene/candidate_001/front.png)

사용자원하는넥수평과줄이있는앞판정면방향을0°후보로구현했다. 바디중심과humanoid상태를유지한static캡처이며물리0이다. 넥-10/0/+10°[비교이미지·실제p/q](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/README.md:1)에남긴다. 높은현재왼손은이후팔손초기각재배치가필요하며접촉/관통/지지/자유기타유지는이번이미지로검증하지않는다.

## 2026-10-09 넓은 기타 범위 안에서 연주하는 기준

사용자 범위 안에서는 초기점 정밀 복원보다 연주를 우선한다. 수평 넥 후보의 이미지와 범위/제어 설계 설명은 [이번 결과 문서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playable_envelope_contract_v1/README.md:1)에 저장한다. 기존 t=0 이미지를 재사용하며 새 물리/영상은 없다. 위치는 기타 actor-root 기준, 회전은 허용 Euler 상자가 만드는 회전 집합으로 해석한다.


## 124. 현재 기타 Strike 정책 종료와 passive continuation

원본 Strike 체크포인트의 실제 정책 연결은 49개 control step/196개 physics step에서 `wrong_crossing_count_termination`으로 끝났다. source episode 성능은 TP 0, FP 4, FN 1, F1 0이고 종료 피크-목표 거리는 152.024 mm였다. 새 native_v2는 같은 정책 prefix를 재현한 뒤 actor·PI·노래·detector를 멈추고 마지막 81개 PD 목표를 고정해 총 1200 physics steps까지 기록했다. 정책 종료 뒤 5초 기록의 위치·회전 곡선은 수동 후속 물리 구간이며 정책 연주 평가나 안정 성공이 아니다.

![정책 구간과 수동 후속 물리 기록의 기타 변화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/figures/policy_timeline_v3/policy_passive_timeline_v3.png)

빨간 세로선은 정책 종료 step 196 (0.816667 s)이며 저장 표본 step 192와 200 사이에 있다. 종료 step의 native 기타 p/q는 trace에 없어 보간하지 않았다. 음영 구간은 마지막 81개 관절 PD 목표를 유지한 자유 물리 continuation이다. 최대 기타 위치/회전 변화는 63.386 mm/14.883°, 끝점 변화는 44.061 mm/11.768°다. 종료 뒤 검사는 q/qd/G 유한성, qd<50, root·하체 고정 및 상수 목표 유지에 한정되며 source geometry 안전이나 상체 pose 유한성을 연속 감시하지 않았다.

두 번째 native 결과에는 실제 Isaac Gym 카메라 전신·손 영상(각 151 frames, 30 fps, ffprobe stream duration 5.033333 s)이 있다: [전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/trial/images/whole_body.mp4), [손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/native_v2/trial/images/hands.mp4). 그래프는 저장 trace에서 계산한 값이며 native render는 아니다. 세부 수치, 실행 제한, 실패 이력 및 입력 보존은 [phase README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/README.md:1), [변경 파일·원자료 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/CHANGED_FILES.md:1), [그림 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/figures/policy_timeline_v3/manifest.json:1)에 있다.


## 125. 현재 기타 기준 양손 준비 gate — 5초 진단

v4는 기본 RH IK를 복원한 native preparation 기준이다. 네 5초 실행에서 초기 native 상태와 PD 설정은 exact 일치했다. v4의 300개 control 표본에서는 왼손 palm underside contact 1회, finger-neck contact 298회가 따로 기록됐지만 동시 참인 표본은 0이었다. 오른손 외부 50 mm 근접 조건은 9/300, 전체 preparation gate는 0/300이었다. 원본 READY의 10 mm 및 6 연속 프레임 조건은 외부 50 mm 근접 gate와 구별한다.

![v4 RH 거리, LH contact 조건 및 전체 readiness gate의 저장 표본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/figures/v4_readiness_v2/readiness_v4.png)

실선은 native control sample의 오른손 준비점 거리, 점선은 외부 50 mm 조건, 점선형 회색 선은 원본 10 mm READY 거리 맥락이다. 전체 gate에는 왼손 palm/finger, palm-up, RH 앞면/grip/noncontact를 포함한 모든 조건이 필요하고 6 control frame 연속 만족해야 한다. v4에서 actor 실행·PLAY handoff는 없었다. 이 그림은 saved readiness/control 자료의 시계열이지 native 렌더가 아니다.

v4 실제 Isaac Gym native 카메라의 전신 시작/종료 및 왼손 근접 시작/종료 이미지는 [phase README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/README.md:1)에 삽입했다. [네 trial의 초기값 JSON 및 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_relative_ready_v1/README.md:1)도 같은 문서에 색인되어 있다. 후속으로 왼손 지지와 RH 준비점 잔여 오차를 분리해 검토할 필요가 있으나, 이 절은 후속 실행을 선택하지 않는다.

## 126. 준비 진단에서 Strike 정책으로의 명시적 연결 — 5초 기록

기존 prepared candidate 1을 0–2초 준비한 뒤 별도의 진단 predicate로 frozen Strike checkpoint를 연결했다. 이는 기존 strict 50 mm/palm·6연속 표본 gate를 통과한 연결이 아니며 strict 조건은 계속 false였다. 연결 직전 오른손 ready 거리 57.003 mm는 별도 80 mm 진단 기준 아래였고, 왼손 palm-under-neck 조건은 false였다. 따라서 정책 모드 진입을 palm 지지나 정식 연주 준비 인증으로 해석하지 않는다.

![2초 진단 연결 시점의 실제 native 전신 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/native/data/images/frames/whole_body/00060.png)

![2초 진단 연결 시점의 실제 native 왼손 근접 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/native/data/images/frames/hands/00060.png)

정책은 2–5초 180 control sample 동안 실행됐으나 READY motor phase 0을 벗어나지 않았고, target hit·accepted release는 0이었다. 현재 기타 범위 monitor는 64/180 표본만 참이었으며, 3.066667초부터 벗어난 표본이 관찰됐지만 정지나 경계복귀 제어는 하지 않았다. 전체 episode는 완료되지 않았다. 실제 카메라 전신 영상과 왼손 근접 영상은 각 151 frames/30 fps로 저장됐다(왼손 근접 장면에는 오른손이 일부만 보임).

![실제 native 전신 영상, 0–5초 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/native/data/images/whole_body.mp4)

![실제 native 왼손 근접 영상, 0–5초 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/native/data/images/hands.mp4)

[전체 결과·0/2/5초 이미지·실행 제한](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/README.md:1)과 [실행·자료 파일 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/prepared_strike_connection_v1/CHANGED_FILES.md:1)을 따른다. 정책 연결은 진단상 실행됐지만 인정 타현, strict palm 지원 또는 연주 성공은 확인되지 않았다.

## 2026-10-10 연주 자세·현재 프렛 목표 진단

저장된 스트랩 ON native 실행의2초 전환과3.716667초 실제 종료를 비교했다. 넥 기울기는−5.47→+11.33°, 앞판과 고정 몸통 정면의 각도는3.68→51.49°다. 종료 actor-root 위치는 위치 범위 안이지만 활성 손끝–프렛 목표 오차는 검지106.88/약지78.74mm이며 기존 실행은 압현 성공0%로 실패했다. 프렛·활성 손가락이 바뀌므로 같은 음의 오차 증가로 단정하지 않는다.

![실제 Isaac Gym의2초 전환과 종료, 현재 기타 기준 목표 참고선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/comparison.png)

노랑은 넥 local +Y, 청록은 앞판 법선 +Z, 흰색은 활성 손끝 marker, 분홍은 현재 할당 목표다. 새 선은 접촉·가림 인증이 아니며 기존 오렌지 스트랩 경로 표시를 보존했다. [초기·중간·종료 전신/손 확대와 지표 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/README.md:1). 이번은 저장113표본 후처리로 새 물리 실행·학습은0회이며 자연스러움 문턱·허용 회전 집합 판정은 미설정/미구현이다.

## 2026-10-10 팀원 자세 판정표의 후보와 검증 범위

![팀원 기준의 바디 중심 위치·회전 후보 개념도](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/analysis_v2/pose_candidates.png)

노란 상자는 보고서의 축별 위치 후보를 곱한 바디 중심 영역이고 보라 점은 중앙값 조합 후보다. 실제 기타 형상·인체·접촉이 계산된 Isaac Gym 장면이 아니다. 넥 고도는 팀원 기준22°와 우리 수평 후보0°가 서로 다른 기준임을 표시하고, 방위±2°는 미검증, roll은 두 자연 후보 구간 사이의 빨강 실측점을 분리한다.

![CSV96개 판정 표본과 제안 목표 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/analysis_v2/judgment_samples.png)

원은 눈 판정 기록39개, 삼각형은 눈 판정 미기록57개다. 색은 원 CSV의 final 판정이며 원자료가 추정한 관통을 새로 인증하지 않는다. 보라색 선분은 제안 목표±오차, 빈 사각형은 dy+2cm 이상치다. 점 사이와6축 동시 변경은 미검증이다. [그림 설명·원자료·변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_visualization_v1/README.md:1). 새 물리 실행·학습·환경 설정 변경은 없다.

## 2026-10-10 팀원 후보의 실제 초기 배치·5초 유지 비교

![같은 humanoid 초기각에서 수평 대조·보고 기준·중앙 후보 재구성의 실제 native0초와5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/analysis/native_comparison.png)

실제 Isaac Gym 전신 카메라다. 보고 기준22°·중앙19.5°는 기존 수평용 손 초기각을 그대로 두어 왼손 raw contact가 관측되지 않았다. 각각 0.8833/0.5875초에 기타 바디가 ground에 접촉한 뒤 낙하했다. 원 팀원의 정확한 초기 상태·pivot이 없는 재구성이며 원 판정 오류로 일반화하지 않는다. 고정 카메라에서 낙하 후 기타 일부가 화면 밖으로 이동할 수 있다.

![30Hz151저장 표본의 초기 기타 actor-root 대비 이동과 최단 회전 차이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/analysis/pose_changes.png)

세 조건은 각각 1,200 physics step/5초, 두 카메라 각각151 frame이다. 초기 convex 기타–인체/의자 교집합은0건이나 cooked 관통 인증이 아니다. 수평 대조 표본 최대62.438mm/15.540°, 보고 기준1381.178mm/122.985°, 중앙1306.791mm/154.357°다. 두 낙하 조건의 후기 평탄함은 연주 위치 유지가 아니다. 위치는 world actor-root, 회전은 초기q 대비 최단각이며 240Hz 전체 step 최대값을 인증하지 않는다. raw 접촉수를 지지력·연주 성공으로 해석하지 않는다. [설명·초기값·6개5초영상·변경색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/README.md:1). 현재 허용범위 변경·policy·학습은 없다.


## 2026-10-10 실제 장면 위의 두 위치 후보

![현재 수평 배치에서 사용자·팀원 위치 후보를 같은 바디 중심 좌표로 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/front.png)

파랑 선 상자는 사용자 위치범위를 이 장면의 실제 기타 회전에서 바디 중심 좌표로 변환한 것이다. 노랑 선 상자는 팀원 바디 중심 후보(right17..23/front24.5..34.5/up8..10cm)를 현재 Pelvis에 적용한 것이다. 분홍은 실제 바디 중심, 회색은 기타 actor 원점, 초록은 실제 넥 방향이다. 파랑 box는 회전마다 달라지며 두 상자가 단순 포함 관계를 이루지 않는다.

![팀원 기준22도 배치의 측면, 조건부 사용자 범위와 팀원 후보](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/side.png)

같은 humanoid 초기각에서 보고 기준 자세를 재구성한 실제 Isaac Gym0초 장면이다. 선은 실제 depth와 camera행렬로 후처리한 설명표시이고 가려진 선은 점선이다. raw frame도 따로 저장했다. 물리 적분을 끈 정적 장면으로 손지지·관통·유지 성공을 뜻하지 않으며 원팀원 초기각/회전중심이 없어 원장면 재현도 아니다. native초기화3회/physics0step/학습0, 상태 exact/렌더불변/inputSHA통과. [세 자세의 정면/측면·원본·변경 실제 줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/README.md:1).


## 2026-10-11 사용자 범위의 바디 중심 표시

![골반 상대 바디 중심 수치와 사용자·팀원 위치 범위, 저장 native 프레임 후처리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/current_control/front.png)

원점 marker를 제거하고 분홍 바디 중심만 표시했다. footer의 실제 위치/하늘색 사용자/노랑 팀원은 모두 골반 기준 오른쪽·앞·위 cm다. 현재 실제 바디 중심은16.9585/24.5012/10.8973cm, 사용자 수평q 조건부 범위는[-10,25]/[0.83,30.83]/[5.80,29.17]cm다. 기타가 회전하면 사용자 body-center box도 이동하며 모든 회전의 공통box/안전영역은 아니다. 초록은 실제 넥 방향을 바디 중심에서 옮겨 표시한 방향선이며 접촉선이 아니다. 저장된 Isaac Gym t0 프레임과depth행렬을 활용한 새 후처리6PNG, 새native/physics/학습0회다. [세 자세 정면/측면과수치표·변환 가정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/README.md:1).


## 2026-10-11 동일 장면에서 범위 분리 비교

![같은 수평 기타에서 왼쪽 사용자 범위와 오른쪽 팀원 후보를 별도표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_side_by_side_v1/analysis/front.png)

양쪽은 같은카메라·같은기타/인체초기배치·같은crop/배율이다. 하늘색 사용자 범위의 폭35/30/23.37cm, 노란 팀원 후보의 폭6/10/2cm로 위치영역 크기를 비교한다. 분홍 실제 바디중심RFU는양쪽16.96/24.50/10.90cm다. 실제기타를각범위중심으로옮긴장면이아니며, 표시선은저장native프레임의후처리다. 현재수평q조건부범위,새native/physics/학습0이며접촉·안전영역인증이아니다. [측면확대·설명·파일색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_side_by_side_v1/README.md:1).

## 저장된 전체 Fret 진단 (2026-10-11)

기존실제Isaac Gym원본389frame/12.916667초·준비2초~첫원본done에바디중심·조건부사용자위치범위·현재기타기준checkpoint손끝목표·실제접촉body를표시했다. 저장420관측과native손끝의같은step정렬1µm이하·고정camera sourceSHA·31frame×2view raw RGBA exact·입력불변을검증했다. 새물리실행없음,full live진단시도3개는native카메라API중단으로부분영상만남았다. 선은depth없는투시선·초록은접촉body원점이므로표면접촉점/관통인증이아니다. 준비목표와마지막접촉은미측정이다.

2초약지87.6mm/손목벡터155.2mm,8초다른goal약지46.7mm. 위치box밖53표본/최대15.0mm·회전최대50.25°,원본검지finger_back실패/지속0/27이다. [전체이미지·영상·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/README.md:1).

![2초 양손·현재 프렛 목표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/analysis/frames/hands/00060.png)

![시작부터 원본 종료까지 전신 진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/saved_fret_diagnostic_v1/analysis/whole_body.mp4)


## 현재 기타 기준 왼팔9 지지 추종 — 2026-10-11

동일초기조건의OFF/ON 실제IsaacGym카메라그림이다. 2초준비뒤손가락21정책을유지하고왼팔9의준비지지관계를현재기타p/q로갱신했다. 아래11.133초그림에서위치/회전차이를볼수있지만압현·관통·접촉을그림만으로판정하지않는다. 공통구간최대회전은47.863→19.408°,이동은73.190→126.888mm로서회전개선과이동악화가함께나타났다. ON은wrong_press실패로종료했다.

![왼쪽 OFF·오른쪽 지지 추종 ON, 같은11.133초 실제 손 카메라](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/analysis_verified/hands_2672.png)

![지지 추종 ON, 시작부터11.133초 원본종료까지 실제전신영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/ON/data/images/whole_body.mp4)

[초기값·손영상·전체비교·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_support_v2/README.md:1). 다음은허용범위밖에서복원하는팔보정과source손목/운지목표에맞춘준비자세다.


## 손바닥·엄지 지지 네 조건 — 2026-10-11

아래는 같은 native Isaac Gym 카메라의 실제5초 프레임을 조건별로 나열한 그림이다. 위부터 기존,초기자세만변경,접촉점추종,팔자세유지+접촉점추종이다. 손바닥/엄지 동시 rawsolver응답은0/22/73.67/44.33%지만 최대기타이동/회전은62.96mm/13.63°,62.80mm/13.70°,96.22mm/16.24°,63.30mm/13.76°다. 접촉 증가와 안정화 성공은 별개다. 그림은 source기하·정확접촉면·뉴턴힘·미끄럼/관통안전을 인증하지 않는다.

![5초 양손 네 조건 실제 native 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/analysis_final/hands_t5.png)

![실제시간별 위치·회전·동시 solver 응답 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/analysis_final/timeline.png)

아래 자세유지 결합 조건은 실제환경0~5초 영상이다.5초는 관찰시간 종료이며 연주완주/물리평형 판정이 아니다. Fret/학습0,root/하체고정·몸통PD·무스트랩·self-collision이며 기타는 자유물리다.

![팔자세유지+접촉점추종, 시작부터5초 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/posture_on_retry/data/images/whole_body.mp4)

[모든 조건 양손/전신 영상·초기값·그림 설명·보존 이력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/README.md:1).


## 왼손 공동 학습 정책 구조 제안 — 2026-10-11

아래 그림은 왼손33관절이 지지와 압현을 함께 제어하는 설계 제안이다. Actor/Critic은 별도 두 층 MLP이며 입력 차원D는 미확정이다. 실제 native81 관절 상태와 현재 기타·음악·접촉 정보를 관측 후보로 두고, 왼손33 목표와 held48 목표를 단일81D PD 명령으로 합친다. Critic/PPO는 학습 전용이다.

![왼손 공동 정책 설계 제안, 구현·학습 결과 아님](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_hand_learning_design_v1/architecture.png)

이 그림은 새 시뮬레이션이나 검증된 성능을 나타내지 않는다. 자유 기타·무스트랩 조건과 최종 양측66 사용 범위를 보존하며, 범위 안에서는 초기점 복원 비용0, 손바닥 지속 접촉은 불필요하다. [그림 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_hand_learning_design_v1/README.md:1) · [제안과 다음 검사](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_JOINT_POLICY_DESIGN_V1.md:23).


## 전체 상체81 공동 정책 설계v2 — 2026-10-11

아래는 최신 설계 제안이다. Actor는 몸통9·목/머리6·양측66의81관절 목표를 모두 소유하고, native 한계/변화율 제한을 거친 단일81D PD 명령을 제출한다. 별도 held 상체 채널은 없다. Actor/Critic은 각각512→256 은닉층을 사용한다.

![전체 상체81·512→256 설계 제안, 구현·학습 결과 아님](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_learning_design_v2/architecture.png)

root/하체 고정과 자유 기타 조건을 유지한다. 몸통·목/머리의 작은 움직임은 soft 선호이며 실제각 고정이 아니다. 이번 그림은 새 물리 실행을 나타내지 않는다. [그림 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_learning_design_v2/README.md:1) · [제어권 설계](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_JOINT_POLICY_DESIGN_V2.md:15).


## 몸통·시선·기타 이탈 비용의 함수 그래프 — 2026-10-11

아래는v3.1 설계 수식의 그래프이며 native물리실행화면/학습성능이아니다. 몸통은9개actual 관절오차가같다고가정한C_joint만 표시하고Chest회전항은별도다. 목표±5° 후보한도와 실제각비용을구분한다. 시선최대보상은0.01/초다. 기타곡선은허용범위바깥위치거리만변화시키고회전집합거리는0으로가정했다.

![몸통·머리시선·기타범위이탈 설계함수, 시뮬레이션 아님](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/reward_profiles.png)

각y축은초당가중값이며실제연속보상에는Δt를곱한다. 실제신호연결/행동한도/회전집합과학습효과는미검증이다. [그래프조건·원자료·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_design_v3/README.md:1) · [수식](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V3_1.md:53).


## 보상 정리 v4 — 수식 비교, 실제 시뮬레이션 결과 아님

프로젝트 Fret/Strike/clock/평가 계획을 반영한 [보상 설계](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_REWARD_DESIGN_V4.md:14)다. 유지 최대값의 길이 정규화, 다른1차 음악/기타항이 동일할 때의 보상 역전 방지, 유효 영역까지의 넓은 선형 접근을 비교한다. v3 초당 hold와 v4 전체구간 예산은 단위가 다르며 최적 가중치나 학습 향상을 증명하지 않는다. 실제 환경/물리/학습0, 산술검사42개 pass다.

![보상 정리 v4 수식 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/reward_refinement.png)

이미지와 설명은 예정 산출물이며 최종 마감에서 존재·원자료 대조를 확인한다. 기타 범위/현재G/sounding-state 신호와 종료 계약을 검증하기 전 실제 학습에 적용하지 않는다.


보상v4 최종 이미지·설명 존재와 원자료 대조를 확인했다. β=1/N_F=1 단일event 유지 예시 및 정음 하한1.826/실패 상한1.609를 표시했고, 수정 전 발표본을 보존했다. 독립 검수 완료이며 수식 비교를 실제 Isaac Gym 렌더/학습 결과로 해석하지 않는다. [상세 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_reward_refinement_v4/README.md:7).


### 보상 v4 학습 유인 감사 — 합성 계산과 CPU tracker

![유지 dropout·기타 cap·합성 할인 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4/audit_signals.png)

같은54/60 유지율에 대해 source CPU tracker의 최장dropout1은성공,6은실패다. O1/E1가정 조건부 F+U−E는둘다2.04이며 실제 v4 reward 실행값이 아니다. 순수 위치 외부거리30mm부터 C_g가포화한다.60Hz 가정 γ.95/.99/.995의2초·5초 할인 비교는 현재 adapter 설정 인증이나 추천이 아니다. Isaac Gym 렌더/새물리/학습0. [설명과 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/reward_design_audit_v4/README.md:1), [상세 감사](/home/ajou/yigyu/3/stability_adapter_2/REWARD_DESIGN_AUDIT_V4.md:1).


### 환경 기본층 v1 — native 시작과5초 종료

![두 조건의 Isaac Gym 시작·종료 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/initial_final_montage.png)

실제 CPU PhysX+native Isaac Gym 카메라 영상이며 스트랩OFF,자유기타,root/하체fixed다. 중립 초기목표 유지와준비2초 뒤작은 상체목표 움직임을 비교했다. 원시상태/548D관측/81목표 경로 검증은 통과했지만 기타최대111.790/113.778mm·19.486/19.888° 이탈로초기지지는실패했다. q_request/final/실제q와접촉body-pair를별도로기록했다.151frames/30fps=영상5.0333초,물리는5.0초다. 음악평가/학습결과가아니다. [설명·전체 영상과원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/README.md:1).


### 양손 연결 runtime: 초기 지지 개선과 PLAY 중 실패 — 2026-10-12

![초기 지지 보정의5초 경과 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload_comparison_v2.png)

같은native초기상태에서neutral/정적preload0.5/1.0을비교했다. t0/2/5초 실제Isaac Gym 프레임이며 CPU PhysX/softwareVulkan이다. 기타free/root·하체fixed/스트랩OFF/self-collision을유지한다. 최대이동111.790/75.331/46.306mm, 최대회전19.486/13.910/9.179°. 위치상자0/301초과였던1.0을선택했지만 전체SO(3)/접촉/음악 인증은아니다. v1 레이아웃시도도보존하고가독성보완v2를표시한다.

![동시 체크포인트 실행의 전체 경과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair100_v4/media/whole_body.mp4)

2초준비뒤 Fret035000+Strike010000을같은시계/한81목표제출자로연결했다. 실제환경3.85초(연주1.85)에Fret 기타-local손목X위치안전조건으로종료했다. 마지막924step 장면을30fps격자밖에서도추가해117frame/영상3.9초이며 실제시간과구분한다. 기타는최대403.605mm/63.992°로움직였고공동4event성공0이다. 영상의멈춤은평형/곡완주가아닌종료다. [원자료·손확대·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/README.md:1).


#### 입력 계약 검증 마감 — 2026-10-12

현재 entry는 [run_dual_music_v5.py](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v5.py:26)이다. Strike checkpoint document/goal·grip SHA 및 원본 action/observation 순서 검사를 추가했다. 추가4CPU검사와같은조건native재실행에서v4/v5 controls·trace·초기값·240Hz음악판정이exact일치해같은3.85초Fret 실패를재현했다. 이전v4도실제입력SHA가일치했으며원본은보존한다. 마감집계는고유CPU16검사/새native4회/4248물리step/8영상/두pair각111추론tick/학습0이다. [집계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/execution_summary_v2.json:1) · [guard검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/contract_guard_v5_verification.json:1) · [후처리보존예외공개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/PROVENANCE_NOTE_V2.md:1).


### 상체 공동 학습 구조 1차 구현 — 2026-10-12

Actor739→512→256→81과 별도 Critic739→512→256→1, 원 latent 행동을 기록하는 tanh Gaussian/PPO, terminated·truncated를 분리한 GAE, rollout 곡 진행 연결, model/Adam/RMS/RNG/ABI 불변 저장을 구현했다. body9/head6/arm24/finger42 모두 출력하며 기존 PD와 목표 변화율/몸통±5°/root·하체 고정/기타 자유/strapOFF를 유지한다. 평균0 행동을 검증된 preload1.0 절대 목표에 대응하는 anchor codec으로 초기화했다. 기존 Actor 가중치/행동 복사는 없다. 관측에는 현재 기타 기준 손 상태, 원본 압현 셀, pick detector/rearm 메모리와 양손 음악 목표를 넣는다.

- [x] CPU22반례: Actor/Critic 실제 갱신, 끝점·경계 codec, 포화 likelihood, 종료/절단 bootstrap, checkpoint 복원/덮어쓰기 거절, 재무장0/7frame과 미종료 rollout 연결 검증.
- [x] native 평균5초+같은checkpoint복원·탐색5초, 총2400physics/4영상. 평균 trace는 preload100_v2와 exact, 최대46.306mm/9.179°. 탐색81전채널 표본, 최대57.114mm/9.960°. 각9event 성공0이며 학습·연주 성공이 아니다.
- [x] 실제 초기상태·고정 하체·관측·목표/rate·금지 API0·SHA 보존 대조와 독립 코드 검수.
- [ ] 실환경 PPO 최적화는0회. SO(3)허용집합, 연속 유지/dropout, fatal 일정 정산/할인, distal press pad, reward v5 측정/mask를 닫은 뒤 scalar reward 환경 API를 연결한다. 현재 --train은 장면 생성 전에 막는다. 739D는 이번 버전의 계약이며 보상 ledger 추가 때 새 ABI가 필요하다.

[이번 계획](/home/ajou/yigyu/3/stability_adapter_2/JOINT_LEARNING_IMPLEMENTATION_V1.md:1) · [정책](/home/ajou/yigyu/3/stability_adapter_2/joint_policy_v1.py:50) · [PPO](/home/ajou/yigyu/3/stability_adapter_2/joint_ppo_v1.py:60) · [실제 entry](/home/ajou/yigyu/3/stability_adapter_2/run_joint_policy_v2.py:18) · [이미지·영상·결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/README.md:1).

실제 정의 위치: [JointPPO](/home/ajou/yigyu/3/stability_adapter_2/joint_ppo_v1.py:64), [native main](/home/ajou/yigyu/3/stability_adapter_2/run_joint_policy_v2.py:17).


### GPU 재확인과 정오 마감 시험 학습 — 2026-10-12

GPU 드라이버580.178.04/RTX4070Ti12GB는 정상이며,격리실행의장치접근불가를드라이버고장으로해석한설명을정정한다. CUDA실제연산과독립GPUPhysX검사를통과했고사용자재설치/재부팅은필요없다. 이번native는기존CPUPhysX를유지하고정책/PPO만CUDA로실행한다.

등록된Fret035000·Strike010000은동결해실제로목표를요청하며820D관측/81D상체정책/512→256 Actor·Critic/단일PD owner를사용한다. 실제1PPO갱신256transition과두전체평가(각16.3667초/3928physics/42event/성공0) 검증을완료했다. 한회갱신은품질개선증거가아니다.이번은명시적deadline_pilot이며정식rewardv4/v5 인증이아니다.

[실행과한계](/home/ajou/yigyu/3/stability_adapter_2/DEADLINE_EXECUTION_V3.md:1) · [이미지·4영상·비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/artifacts_smoke_v2/README.md:1).30분간격저장/전체평가및11:40이후새제어진입차단을구현했으며,장기실제실행상태는[진행로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/live_progress.jsonl:1)에서확인한다. native 입력closure가읽는동안main4를변경하지않는다.


### 기타 이탈 대응과 스트랩 비교 계획 — 2026-10-12

무스트랩 평가의 위치 허용범위 이탈은 약84.6–84.7%, 최장 약12.8초였다. long_run_v3는9PPO갱신/2304transition 뒤 관절상태 안전검사로 중단됐으며 입력SHA와 기존 체크포인트·영상은 보존했다. 기존 보고서에 실패관절의 수치가 없어 정확 원인은 새 진단에서 구분한다.

원본 스트랩 길이1.1018469719600776m를 고정한ON/OFF825관측 비교, 유한 관절속도 초과 시 실제 earlytermination/reset과 할인된 안전실패 비용,820정책의 검증된825warm start를 새버전으로 구현한다. 새Adam/ABI이며 exactresume나 정식rewardv4/v5 인증으로 설명하지 않는다. [소단계 계획](/home/ajou/yigyu/3/stability_adapter_2/STRAP_FALLBACK_TRAINING_V1.md:1). 결과는 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/`에 저장한다. 이후 실제 실행상태는 별도progress로 추가하고 native 입력이 읽히는 동안 이 main문서를 수정하지 않는다.


### 기타 안정성 비중 강화 학습 — 2026-10-12

사용자 요청으로 위치 이탈 초당 계수−2→−8, 회전 upper proxy 계수−1→−4로 각각4배 강화한다. 범위 내 비용0/음악 항/상체81/원본 스트랩 ON·OFF/실제 초기값은 유지한다. floor는−8, 안전 tail은 같은 하한으로 정산한다. 이전825 Actor·RMS만 상속하고 새 Critic·Adam으로 시작하며 보상 ABI를 분리한다. [새 계획](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_PRIORITY_TRAINING_V1.md:1). 결과는 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/`에 저장한다. 이전 ON 프로세스 종료 원인은 미확인으로 기록하고, 저장된ON92/OFF127에서 전환한다. 아직 실행/안정화 성공을 의미하지 않는다.


### 학습 갱신 폭과 안정화 보정 수정 — 2026-10-12

직전 ON54갱신/완료35에피소드가 모두 유한 관절속도 안전 종료됐고, OFF40갱신/완료11에피소드는 완주했으나 공동 음악 성공0이다. 첫 optimizer step와 후속 RMS 변화가 최종 정책 KL 검사를 벗어나는 문제를 분석했다. 새버전은 전체 rollout analytic KL 후보 승인/모델·Adam rollback, RMS 고정, 학습률3e−5, 부위별 작은 radian residual와 평균0 Actor로 시험한다. 원본 스트랩·두 baseline·초기 물리·안전 검사는 유지한다. [계획](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_UPDATE_CORRECTION_V1.md:1) · [원자료 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/previous_analysis_v1.json:1). CPU v1의 Adam 복원 alias 실패는 보존하고 v2의6검사 통과 후 별도 검수와 실제 영상으로 검증한다. 실행 중 A/main4를 변경하지 않는다. 아직 품질 개선을 선언하지 않는다.


갱신 전 원자료 재대조: 직전 OFF의 완료11회는 **완주8회·관절속도 안전 종료3회**다. 앞 기록의11회 완주 표현을 정정한다. ON 완료35회 안전 종료는 동일하다. 최종 구현은 guarded PPO v3/CPU7검사 통과 버전이며 비유한 후보·KL 계산 예외도 모델/Adam 복원 후 거절한다. [정정 계획](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_UPDATE_CORRECTION_V2.md:1). 기존 문서·실행 증거는 보존한다.


### 팔·왼엄지 baseline 기준 목표 제한 시험 — 2026-10-12

직전 actual CUDA3갱신에서KL/RMS계약을확인하고세16.3667초평가를안전중단없이완료했지만위치범위밖84.6–86.0%·음악0이남았다. 팔 baseline nominal의preload대비최대2.716rad 이탈은±.3residual로상쇄할수없는요청공간문제를보였다. 새버전은팔nominal±.15/왼엄지nominal±.10rad를resetpreload기준으로제한하고상체81residual/다른fingerprior/원본물리/기타안정성보상/두baseline추론을유지한다. 이는원본행동재현이나실제손위치고정이아니다. [계획](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_SUPPORT_NOMINAL_V1.md:1) · [직전영상·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/artifacts_native_v1/README.md:1). 사전검수와실제1갱신·초기/갱신전체영상을검증한뒤장기학습을이어간다.


## 2026-10-12 지지 nominal readiness 재시도 v2

초기 평가는 full horizon 완료했지만 새 profile 검사 불일치로 학습이 갱신 전에 중단됐다. 종료 상태 문제는 아니며 실패 기록은 보존한다. 물리·제어·보상은 유지하고 readiness만 수정한 [재시도 계획](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_SUPPORT_NOMINAL_V2.md:1)에 따라 새 runner v8 / smoke_on_v2에서 검증한다.


## 2026-10-12 학습 그래픽 분리

long_on_v1의 EGL SIGSEGV(-11) 뒤 long_on_v2의 CP241 전체 평가를 완료하고 원본을 보존했다. 학습 graphics−1/별도 영상 평가 graphics0과 5분 복구 저장을 새 버전으로 검증한다. 물리·제어·보상과 기존 checkpoint 수치는 유지하며, 코드 ABI의 추가6소스만 허용하는 명시적 이행이다. [계획](/home/ajou/yigyu/3/stability_adapter_2/GRAPHICS_ISOLATION_PLAN_V1.md:1). 결과는 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/`에 저장한다. 아직 재발 방지·학습 재개를 검증한 상태는 아니다. native 실행 동안 A/main 문서를 다시 동결한다.


## 2026-10-12 그래픽 분리 실제 검증 완료

CPU9검사, graphics−1 60회 초기화와CP241의16.3667초 결정론적전체궤적/controls exact비교, CUDA1갱신(CP241→242/256transition),초기·갱신전체평가4영상을완료했다. checkpoint model/Adam/RMS/RNG/counters 이행은 exact이며 정책KL .01990470476448536≤.02/RMS고정을확인했다. physics/PD/81제어/두baseline/원본strap 계약은유지한다. 첫probe의진단JSON을학습ABI에넣은오류는이행단계에서거절됐고원본을보존했으며,새D 진단v2에서입력을분리해통과했다. [실제검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/verification_v1.json:1) · [결과설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/README.md:1).

CP242는음악0/42·위치box밖46.64%/최대47.11cm여서학습품질개선·기타안정화성공이아니다. 기존CP86/241대비일관된개선은없다. 오류예방검증과성능평가를구분한다. 검증된CP242에서같은학습조건으로재개하고,5분복구checkpoint 실제생성과30분공식영상/11:40cutoff를확인한다. 새 supervisor는완료/부분종료가구분되는 실제영상을 `/home/ajou/yigyu/3/docs/2026-10-12/video/graphics_long_v1/`에 자동복사·SHA검사한다. native 실행동안A/main을다시동결한다.


## 2026-10-12 병렬 환경 수집 전환

사용자 요청으로 독립 spawn CPU 물리환경4개와 CUDA batched정책 추론을 구현한다. 초기 관절/기타/스트랩 무작위화는0이며 행동Gaussian탐색만유지한다. 기존single환경의마지막복구CP315/80640transition과종료전로그319회까지보존했으며미저장316–319는이행하지않는다. 기존source/asset/물리·제어·보상/Adam/RMS/RNG/counters를유지하고새6소스만허용하는ABI이행이다. CPU7검사를통과했으며 N2의독립5초물리→N4/T64(256transition)CUDA1갱신·전체영상→N4/T256(1024transition)학습으로검증한다. [계획](/home/ajou/yigyu/3/stability_adapter_2/PARALLEL_COLLECTION_PLAN_V1.md:1). 결과는 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/`에저장한다. 아직실제병렬학습과속도개선을인증하지않는다. native실행동안A/main을다시동결한다.
