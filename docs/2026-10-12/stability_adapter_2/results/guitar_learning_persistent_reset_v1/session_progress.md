# Persistent native session 구현

- 소유 파일: `guitar_learning/persistent_session.py`, `guitar_learning/tests/test_persistent_session.py`.
- 기존 실행 중 소스·공용 Scene/Guard/Controller·자산·설정·원자료는 수정하지 않았다.
- `PersistentHeadlessPreparedSession`은 기존 headless 준비 세션을 최초 한 번 생성한다. 에피소드 경계에서만 기존 `_restore_once`의 검증·human DOF 및 guitar 강체 상태·속도·native target 복원을 재사용한다.
- reset 전에 원래 Guard를 거쳐 human105 유한 effort를 0으로 제출한다. 기타 외력 API는 호출하지 않는다. 이전 단계는 기존 동기 simulate/fetch 경로로 완료되어야 한다.
- Scene/Sim/Env/Controller/FK identity와 네이티브 PD·질량/관성/flags·형상 물성·SimParams를 유지/검사한다. 원래 controller anchor/FK는 재생성하지 않는다. target_rows 및 명시 controller history만 초기 원형으로 복원한다.
- 기존 Guard의 state/force/property 권한은 그대로다. 공용 Guard를 수정하지 않고 실제 create_sim/create_env/load_asset/destroy_sim 호출만 계수한다. 초기화 호출·금지 호출 원자료는 누적 보존하고 에피소드 시작 offset을 별도로 기록한다.
- 에피소드별 `persistent_reset.json`과 최종 `persistent_lifecycle.json`을 독점 생성한다. 로컬 physics step과 누적 native simulation time을 구분한다. 숨겨진 PhysX solver/contact cache 복원을 주장하지 않는다.
- CPU 검사 5개 통과: 상태/속도/target 복원과 identity/history 유지, 물성/config 변경 거부, 실패 후 close/gate 복구, 정상 integrate에서 setter 미호출 및 미완료 단계 reset 거부, lifecycle 계수와 기존 guard 권한 유지.
- 새 native 실행은 이 worker가 시작하지 않았다. 실제 접촉/반복 reset 비교와 성능 검증은 root의 별도 실행 결과를 따른다.
