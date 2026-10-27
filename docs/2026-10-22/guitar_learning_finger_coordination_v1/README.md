# 왼손의 관절 분담과 비사용 손가락 자세 개선

이전 최종 영상의 중간 관절 펴짐·끝관절 쏠림은 실제 저장 자세에서도 확인됐다. GPU 왼손 보상v5에 실제 회전 기반의 부드러운 관절 분담·대기 자세 항을 추가하고, 표면 추종 보상의 다른 손가락 요청 결합을 분리했다. 전체 관절 범위와 독립 굽힘·펴짐, 기존 물리·성공/안전 기준을 유지한다. 이번 짧은 학습과 고정 명령 검증은 자연스러운 곡 연주 학습의 완료를 뜻하지 않는다. 새 장기 학습은 수행하지 않았다.

## 실제 영상의 문제

[기준 자세 분석](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_coordination_v1/baseline_report.md)은 이전 보상v4 최종 모델의 저장된 실제 몸체 회전을 분석한다. env0의10초 이후1370개 endpoint에서 평균 중간(PIP)/끝(DIP) 굽힘각은 검지 약0/90도, 중지 약0/6.74도, 약지0.59/85.15도, 소지 약0/71.34도였다. 저장8환경에서 같은 경향을 확인했다. 약지·중지의 기저(MCP)는 역방향으로 펴졌지만 검지·소지 MCP는 굽혀져 있으므로 모든 기저 관절이 펴진 것으로 일반화하지 않는다.

기존 정책은 비목표 구간에도 PIP를 펴는 한방향 요청을 지속했다. 기존 보상은 표면 위치·접근/정지와 접촉을 평가하지만 대기 자세와 실제 관절별 굽힘 분담을 보지 않았다. 또한21축 요청의 합을 각 손가락의 추종 품질에 공통 적용해 다른 손가락·엄지의 요청도 해당 손가락 보상을 낮췄다. 이 구조가 관찰된 자세를 허용한다. 특정 항만이 학습 결과의 유일한 원인이라는 인과 실험은 아니다. 단계0에서도 손가락 제어·추종·접촉 보상은 활성화돼 있다.

## 구현

[보상 helper](/home/ajou/yigyu/3/guitar_learning/gpu/finger_reward.py), [환경 적분](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py), [단계 저장](/home/ajou/yigyu/3/guitar_learning/song/curriculum_runtime.py)를 변경했다.

- 실제 palm→finger1→finger2→finger3 상대 회전이 source−y 방향을 옮긴 결과의 yz 투영각을 MCP/PIP/DIP 굽힘으로 정의한다. source XML의 부모체인·identity rest rotation·+x 굽힘축·자식 방향을 검증하고 경로/SHA를 계약에 저장한다. native 구면 DOF 좌표나 인간 정상 관절각의 인증이 아니다. 투영 퇴화·비유한 회전은 해당 손가락의 두 자세 품질을0으로 한다.
- 관절 분담 품질은 `exp(-sum(위반각²)/30도²)`다. 위반은 `relu(DIP-PIP-20도)`, `relu(DIP-MCP-60도)`, `relu(-MCP-20도)*clamp((DIP-30도)/15도,0,1)`다. 끝관절이 급격히 크게 굽혀지고 근위 관절이 펴진 자세를 낮게 평가하되 비율을 강제로 묶지 않는다. 시간에 대한 jerk나 가속도 제한은 추가하지 않았다.
- 대기 품질은 MCP[-15,110]·PIP[15,105]·DIP[-10,45]도의 넓은 영역 안에서1이며 밖으로 벗어난 각의 제곱합에 같은30도 지수 감쇠를 적용한다. 정확한 고정 자세가 아닌 실험적 soft prior다. 엄지는 이 자세 항의 대상에 포함하지 않는다.
- 담당 음의 준비 시작(`press-2초`)부터 끝까지 대기 가중치0, 양끝 밖0.25초에 선형 전환한다. 겹친 음은 busy 최댓값, 곡에 없는 손가락과 빈 곡은 대기1이다. 관절 분담은 역할과 무관하게 적용한다.
- 관절 분담과 대기는 각각 `.05/s × 네 손가락 품질 평균`이다. 대기는 품질에 해당 idle 가중치를 곱한다. 두 항 합계 상한.1/s,240Hz 실제 표본마다 적분하고 모든 단계의 approach 가중치1을 적용한다. 실패tick의 두 양성 항은 전체0이며 H32·선택reset에서 다른 환경의 누적값은 유지한다. `reward_component_means`와 종료곡의 `reward_components`에 두 항을 기록한다.
- 표면 추종의 요청 비용은 자기 손가락4축 요청 제곱합/21이다. 기존 축당 계수는 유지하고 다른 손가락/엄지 요청의 영향을 제거한다. 압현 목표 선택·거리/속도식과 추종률 상한4/s는 유지한다.

관측512·음토큰24·행동39·단계3331값·제어·가동범위·PD·원물리·기존 접촉/성공·실패 비용·PPO·탐색폭은 같다. GPU 왼손 보상은v5, 추종률 계약은v2, 자세율은v1이다. 이전v4 모델은 의미가 달라 strict resume를 거부하며 새 모델로 시작한다. CPU 왼손/오른손/전문 경로는 기존 계약을 유지한다.

## 검증

관련 CPU4모듈52개 검사를 통과했다. 실제4물리 표본 적분, 실패tick 양성 억제, 부분reset·H32·오른손 격리, 관절각/역할/전환/겹침/퇴화 처리와3331값 저장을 확인했다. 독립 검수는 helper의 회전 계산을 별도 SciPy oracle과 대조해 최대3.11e−15rad 오차를 확인했다. [CPU 기록](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_coordination_v1/cpu_tests.log).

실제 GPU PhysX/CUDA에서 large/N16/H32/seed7로 fresh2업데이트·1024전이, 저장본을 이어1업데이트·512전이를 수행하고 모두 정상 종료했다. 원시64+32행의 CRC/EOF·전이 일치·입력 SHA·새 성분 적분·보상 성분 합·모델56/actor Adam54/value Adam57 유한 텐서를 확인했다. 실패0이며 첫 실행은 약1.067초, 재개는 새 초기 자세의 약.533초로 전곡 평가가 아니다. 새 두 성분은 이 준비 구간 각각 약.0008333334/control tick였다.

저장 final→재개 initial의 모델·양optimizer·Torch/NumPy/Python/CUDA RNG·3331 curriculum·업데이트 횟수는 정확히 같다. 실제 이전v4 최종 모델은 config를 맞춰도 새 보상 identity에서 거부됐고 모델·optimizer·host RNG는 변하지 않았다. 물리 상태는 재개 시 새 준비 에피소드로 시작한다. [검산 코드](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_coordination_v1/verify_training.py) · [검산 결과](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_coordination_v1/training_verification.json). 첫 CPU 검산은 fixture의 정수 count 대신 Tensor를 전달해 실패했고 정수 목록으로 바로잡았다(`training_verification_attempt1.log` 보존). 실제 GPU 학습 실패가 아니다.

## 실제 GPU의 관절 분담 명령 대조

같은035 준비 자세의4환경에16축(네 손가락의1x/1z/PIP/DIP)만 정상 누적 행동으로 명령했다. 엄지·팔 등 나머지23행동은0, 각 목표는 원 native 범위 안에 있다. 몸체/관절 상태 주입·직접 힘 변경·정책/학습 없이180control tick·720물리 표본(3초)을 진행해4환경 모두 종료 실패 없이 정상 닫혔다. 초기화1회, 추가reset0회, 명령 목표 누적식 최대오차0, 입력/소스 SHA 불변을 확인했다.

마지막30endpoint(.5초)의 실제 각도와 같은 자세를 모두 대기로 가정한 별도 raw helper 점수는 다음과 같다. 이 counterfactual은 곡 역할에 따른 실제 earned reward가 아니다.

| 고정 명령 | 실제 MCP/PIP/DIP | 분담률 (/s) | 전원 대기 가정 대기율 (/s) |
| --- | --- | ---: | ---: |
| 끝관절 집중:0/0/90도 | 네 손가락 약0/0/90도 | .0000794 | .0041044 |
| 관절 분담:40/55/35도 | 중지·약지·소지 약40/55/35도, 검지39.3/52.7/33.7도 | .05 | .05 |
| 대기:30/30/15도 | 네 손가락 약30/30/15도 | .05 | .05 |
| 펴짐:0/0/0도 | 네 손가락 약0/0/0도 | .05 | .0389400 |

따라서 이 고정 명령 조건에서 중간 관절 굽힘이 실제로 가능하고 새 점수는 끝관절 집중과 완전 펴짐을 구분한다. 끝관절 집중은 물리적으로 금지하지 않았다. 이4개 목표가 곡의 실제 압현 성공·최적 자세나 모든 조건의 추종을 보장하지 않는다. [GPU 원자료·결과](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_coordination_v1/probe_distribution/report.json) · [명령 대조 도구](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_coordination_v1/probe_joint_distribution.py).

[3초·60fps 비교 영상](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_coordination_v1/distribution_video/joint_distribution_60fps.mp4)과 아래 이미지는 실제 GPU 몸체 자세를 원본 메시로 재생했다. 4환경 동시·공통 카메라·원본180프레임이며 추가 물리/보간은0이다. 자세 readback·ffprobe·전후 입력 SHA 검사와 정상 native 종료를 확인했다. 루트가 최종 이미지의 손 전체·자막·네 가지 굽힘 차이를 확인했다.

![실제 GPU 고정 명령의 관절 분담 비교·정책 학습 아님](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_coordination_v1/distribution_video/joint_distribution_last_frame.png)

## 보존과 한계

[변경 전9파일 목록](/home/ajou/yigyu/3/guitar_learning/archive/20261022_before_finger_coordination_v1/manifest.json)과 [변경 전 소스·기준 seal](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_coordination_v1/before_manifest.json)을 보관했다. 검증 소스436개는 `source_tested/`에 복사하고 [SHA 목록](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_coordination_v1/tested_source_manifest.json)을 저장했다. 이전v4 장기 실행·모델·영상·2659파일 seal은 그대로 보존한다.

이 보상은 손가락을 직접 복귀시키지 않는다. 새로운 정책이 보상을 통해 대기와 압현 자세를 학습해야 한다. 새v5의 장기 곡 성능·손가락별 음 달성 유지·학습 후 움직임의 자연스러움은 아직 미확인이다. 소지의 굽힌 상태 벌림 추종 잔차와 native 구면 관절의 원인은 이 보상 수정으로 해결됐다고 주장하지 않는다. 숫자 priors는 비교 실험 대상이며 압현에 필요한 개별 굽힘·펴짐을 막는 hard limit가 아니다.
