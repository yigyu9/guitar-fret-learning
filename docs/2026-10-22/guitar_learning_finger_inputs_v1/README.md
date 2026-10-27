# GPU 왼손의 손가락별 목표·실제 자세 입력과 거리별 요청 비용

추가 개선 제안의 우선순위1~3을 구현했다. GPU 왼손만 **544상태·전체64×24음토큰·손가락별8×24우선순위·보상v6**를 사용한다. 관련 CPU92개 검사와 실제large/1024환경/H32/seed7 fresh8업데이트·262,144전이 및8→9재개·32,768전이를 정상 완료했다. 새 정책의 장기 곡 성능·손가락 성과 보존·자연스러움 향상은 아직 평가하지 않았다.

## 입력과 보상

| 항목 | 현재 GPU 왼손 |
| --- | --- |
| 기존 상태 | 처음512열 순서/scale 그대로 유지 |
| 실제 자세 | 512~535열: index/middle/ring/pinky별 MCP/PIP/DIP sin/cos24 |
| 유효성 | 536~539열: 각finger 세 관절 투영 모두 유효하면1 |
| 대기 역할 | 540~543열: 각finger의 현재 idle 가중치 |
| 전체 음 토큰 | 기존64×24, 기존 일반 lookahead/capacity/mask 유지 |
| 우선순위 | index_tracking/index_next/.../pinky_tracking/pinky_next의8×24 |
| 정책 결합 폭 | state256+attention128+priority8×128=1408 |
| 단계·제어 | 3331값 curriculum, 기존39행동·전체native범위·독립 누적 제어 |

네 손가락마다 첫 슬롯은 기존 추종 보상과 같은 목표다. 현재 audible 음 중 end가 가장 빠른 음을 우선하고, 없으면 `press−2<=now<end` 준비창에서 onset이 가장 빠른 음을 선택한다. 둘째 슬롯은 같은 finger의 준비창 안 미래음(`onset>now`) 중 첫 슬롯과 다른 가장 빠른 onset이다. 현재음이 없으면 첫 슬롯 자체가 준비음이며 둘째는 그다음 준비음이다. 동률은 원악보 순서, 무효 index−1·maskFalse·토큰0이다.

[공통 선택기](/home/ajou/yigyu/3/guitar_learning/gpu/finger_reward.py)를 보상과 관측이 함께 사용한다. 우선순위는 일반 토큰의 lookahead보다 먼저 시작할 수 있는 보상 준비창을 정확히 따른다. 일반 토큰 밖에 있어도 담당 손가락의 준비 목표는 우선순위 슬롯으로 제공한다. 토큰24필드·기존source 넥 압현면·현/fret cell·목표 오차/실제 상대속도 의미는 유지한다.

새32상태는 [이전v5의 실제 자세 보상](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_coordination_v1/README.md)과 같은 full parent-child quaternion/source frame으로 구한다. native q/qd/target error는 기존 열에 이미 있다. 같은finger의 어느 관절이라도 투영이 퇴화하면 여섯 sin/cos를 모두0으로 하고 valid0으로 구분한다. idle은 자세 보상의 동일한 시간창/0.25초 전환 가중치다. 고정된 준비 자세·관절 목표를 새로 명령하지 않는다.

추종 보상의 자기4축 요청 비용은 기존 `sum((4*action/.2)^2)/21`에 다음 배율만 곱한다. candidate가 참이면 항상1, 비접촉 거리5mm 이하1·20mm 이상.25·사이 선형이다. 실제 속도오차·거리 지수·접근속도/추종률 상한·현재음 선택은 유지한다. 관절을 빠르게 움직이는 실제 능력을 제한하거나 늘리는 변경이 아니며, 먼 목표 접근의 요청 비용을 낮추는 실험적 보상 설계다. 자세 보상v1·손가락별 기존 양성 균형·성공/안전 기준·실패 비용·가동범위·PD·물리·PPO/std/H32/gamma는 유지한다.

[환경](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py) · [정책](/home/ajou/yigyu/3/guitar_learning/skills/specialist_policy.py) · [입력 encoder](/home/ajou/yigyu/3/guitar_learning/training/policy.py) · [기본 설정](/home/ajou/yigyu/3/guitar_learning/training/start.py).

## 호환성과 CPU 검증

SpecialistPolicy는 명시된GPU left·544상태·8slots·finger_targets schema/labels 계약에서만8슬롯을 허용한다. 기존 CPU 왼손512·오른손500·전문 경로와 일반 Policy는2슬롯을 유지한다. 수정 전 기존 shared/left/right 모델의 seed8721 전체 텐서 bytes와 초기화 RNG가 수정 후에도 정확히 같은지 검사했다. 기존 모델의 아키텍처/키/shape를 바꾸지 않는다.

보상v6/추종률v3/새 관측은 이전v5와 strict resume할 수 없어 fresh로 시작한다. 같은 새 계약끼리 모델·양optimizer·난수·3331상태를 복원한다. 물리 장면은 새035/v14 에피소드로 시작한다.

변경 전 관련59개 검사 PASS, 변경 후 관련8모듈92개 검사 PASS였다. [CPU 전](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_inputs_v1/cpu_before.log) · [CPU 후](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_inputs_v1/cpu_after.log). 검증은 목표 동률/창 경계/빈 곡/미래음/독립성, 일반 토큰 밖 준비음, 알려진 실제 회전의 sin/cos·전체finger 퇴화 마스크, 부분reset/H32,8슬롯 각각 gradient·masked NaN·비활성 오른손, 실제CPU PPO·저장/재개/identity 거부를 포함한다. source436개 전체 Python3.8 AST도 통과했다.

## 실제 GPU 검증

fresh8회는1024환경×32tick×8=262,144전이, 정상 종료까지 약101.53초다.256control tick은 환경당 최대4.2667초의 수집 예산이며 원곡1969tick보다 짧다. 64건의 물리 종료와 선택reset이 있었다. 남은 행은 부분곡이므로 안전완주960개나 전곡 성공률로 해석하지 않는다. 수치/실행 오류·OOM·무결성 위반으로 중단한 실행은 아니다.

같은 저장본의8→9 실제GPU 재개는32,768전이·약19.73초이며 새 준비 에피소드32tick(.5333초) 동안 물리 종료0이었다. 두 실행은 단일 GPU PhysX simulator·CUDA tensor pipeline·네 물리 표본/정책tick을 사용하고 정상 native 종료했다. fresh의 GPU 여유 실제 관측 최저는약6.65GiB이며,8회만으로 장기 메모리 plateau·무실패를 보장하지 않는다.

원시256+32행의 gzip CRC/EOF·sampled/logged/durable/committed·전이 수·실패 원장 대응·보상 성분 합·입력 SHA·모델/두Adam 유한값을 검산했다. 최종 fresh update의 평균 성분은 tracking .01037978, coordination .00083303, standby .00023471/control tick이었다. 준비 구간이 시작하며 목표 추종과 역할별 대기가 실제 수집·PPO에 연결됐지만 다른 버전보다 연주 성능이 좋다는 비교는 아니다.

saved final→resumed initial의 identity/model/두Adam/cost weight/업데이트 횟수/Torch·NumPy·Python·CUDA RNG/3331curriculum은 정확히 같고, 재개 후 모델과두Adam이 갱신됐다. 실제 이전v5 체크포인트는 PPO config를 맞춰도 새 identity에서 거부됐고 모델·optimizer·host RNG가 변하지 않았다. [검산기](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_inputs_v1/verify_training.py) · [결과](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_inputs_v1/training_verification.json) · [로그](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_inputs_v1/training_verification.log).

[실제 계약 대조](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_inputs_v1/contract_comparison.json)는 관측/보상만 달라졌고 action/termination/native backend/task는 이전v5와 정확히 같음을 확인한다. 정책 크기와 초기화 RNG 소비가 달라지므로 이전N16/v5와 이번N1024/v6의 물리 종료 건수를 성능 대조로 해석하지 않는다.

## 보존과 후속 범위

변경 전15파일을 [원래 경로/SHA/대체 경로](/home/ajou/yigyu/3/guitar_learning/archive/20261022_before_finger_inputs_v1/manifest.json)와 함께 보관했다. source436개 중11Python만 변경했고 전체 원문은 `source_tested/`와 [SHA 목록](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_inputs_v1/tested_source_manifest.json)에 동결했다. 기존v5의516파일 봉인과v4 장기 실행/영상은 보존한다.

이번 변경은 제안1~3을 연결한 기능 검증이며 각각의 독립 학습 효과를 증명하지 않는다. 제안4의출력 분리는 손가락별 성과 소실이 다시 관찰될 때,5의native 교정은 원인이 증명될 때,6의H64/할인율/탐색 변경은 분리 비교 후 선택할 후속 항목이다. 새 장기 학습·곡 평가·학습 결과 영상은 이번에 수행하지 않았다. 다음 장기 실행 전 출력 공간을 확보해야 하며 과거 봉인 결과를 덮어쓰지 않는다. 현재 실행 명령은 [learning flow](/home/ajou/yigyu/3/docs/2026-10-26/learning_flow/README.md)를 따른다.
