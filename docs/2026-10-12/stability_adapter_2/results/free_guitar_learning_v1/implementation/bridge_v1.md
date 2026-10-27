# 자유 기타 환경 연결 구현

검수 후보는 `environment_v3.py`, `test_environment_v3.py`, `run_smoke_v5.py`이다. 이전 초안은 보존했다. CPU 검증만 수행했으며 이 문서 작성 시점에 신규 native 물리 실행은 없다.

- `reset()`은 기존 0.035 baseline 설정으로 `runtime_v15.Scene`과 `runtime_v12.Controller`를 새로 만들고 실제 5,280 물리 스텝을 수행한다. 기록된 22초 상태를 체크포인트로 주입하지 않는다.
- 22초의 최종 제출 목표105를 기준으로 canonical `ACTIVE_NAMES`39의 정규화 액션을 해석한다. 범위는 필수 인수이며 smoke의 0.002rad는 작은 연결 검사 범위일 뿐 음악 동작에 최적화된 값이 아니다.
- 상체81에는 원 `JointTargetContract`의 비대칭 native 한계 교집합·평활·속도 제한을 재사용한다. 정책이 소유하지 않는 상체42의 목표는 준비 완료 목표를 유지한다. 하체24는 원 foot 유지 제어를 계속하므로 비정책66의 목표가 모두 고정이라고 설명하지 않는다.
- 정책 인계 뒤 원 LH IK·Motion·자세 증분 보정 체인을 다시 호출하지 않는다. foot 목표를 계산한 뒤 원 최종 `scene_v8.Scene.command`를 한 번 호출한다. 원 혼합 POSITION/effort 제어와 중력·유한 Chest 지지·Hip 보정·말단 SO(3) feedback 및 토크 상한은 그대로 사용한다.
- 한 정책 스텝은 240Hz 물리 네 스텝이며 각 실제 native 상태와 기타 좌표계 형상을 반환한다. 기타 루트는 자유 강체·중력 활성이고 strap 힘 및 매 스텝 기타 상태 덮어쓰기 경로는 호출하지 않는다.
- 초기 인체 Root 고정과 전체105/유효97/원 가동범위0인 하체8의 정확한 이름을 검사한다. 준비 완료 목표가 native 범위를 벗어나면 관절명·값·한계를 보고하고 중단하며, 한계를 완화하거나 조용히 자르지 않는다.

0 액션 인계는 원 baseline의 지속 LH IK와 다른 실험이다. 원 V3 안정성 통과를 승계하지 않는다. smoke는 각각 새로 준비한 원 baseline 연속1초와 0 액션 인계1초의 목표 차이를 기록하고, 별도로 0.25 정규화 액션1초를 수행하도록 준비했다. 보상·음악 성능 학습·기존 Fret/Strike 체크포인트 연결은 아직 구현하지 않았다. 기존 Fret의 0=DONT_CARE와 음악 입력의 개방현0은 구분한다.

CPU 테스트 8개가 통과했다. 확인 항목은 새 reset의 실제 스텝 수, 정책 단일 목표 소유권, 네 물리 표본 반환, 상체39 이외 목표 보존, 하체 유지 목표 변경 허용, 잘못된 액션의 무진행, reset 정리, 전체 관절/zero8 이름 거부, 물리 상태 덮어쓰기 거부, 원 codec 메타데이터 불변이다. native 결과나 안정성은 CPU fake backend 검사로 주장하지 않는다.

smoke runner는 trial별 0초 상태·원 PD 속성·K/D·자산·충돌·카메라, 22초 실제 native 상태와 형상, 이후 240Hz 상태·형상·effort를 보존한다. 원 native 카메라의 정면/손 영상을 5fps로 저장한다. 소비할 모델 XML의 모든 mesh 선언과 프로젝트 소스는 사전/사후 SHA를 대조하며 원 baseline의 expected SHA도 비교한다. 카메라 인코딩 오류는 원 물리 예외와 별도로 기록한다.

검증 명령: `python -m unittest stability_adapter_2.free_guitar_learning_v1.test_environment_v3 -v`

native 실행은 root 검수 및 승인 후 새 출력 경로에서만 수행한다.
