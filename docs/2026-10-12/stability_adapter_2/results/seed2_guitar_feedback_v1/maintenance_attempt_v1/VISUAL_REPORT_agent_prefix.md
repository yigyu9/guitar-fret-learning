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

2×3 배열은 세 신규 run의 실제 Isaac Gym 저장 이미지로, 윗행은 step 0, 아랫행은 step 1200/t=5초다. 초기 여섯 source 부위의 통합 접근 조건은 충족되지 않았다. 각 run에서 R_Hip의 positive contact가 1200개 고유 step 모두에 기록됐고 RH hand–guitar contact 행은 0개였다. named-body 접촉행과 raw lambda는 넥 면·연속 지지·힘을 인증하지 않으며, 모든 run의 기타 이탈은 남았다. 후처리 이력은 세 번이다. v1은 필드명 오류로 렌더 전에 종료했고, v2는 첫 성공 출력이지만 step 0–24 exactness boolean을 true여야 하는 그림 통과조건으로 사용했다. 현재 canonical은 세 번째 실행이며 boolean 형식만 검사해 false도 허용한다. 편집 전 v2 자료와 입력 SHA 확인은 [v2 archive](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifacts_attempt_v2>)에 보존됐고, 두 canonical PNG는 v2와 byte-identical이다. 표·제약·초기값·영상은 [phase README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/README.md), 입출력 SHA는 [artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_response_locality_v1/artifacts/artifact_manifest.json)에 있다.
