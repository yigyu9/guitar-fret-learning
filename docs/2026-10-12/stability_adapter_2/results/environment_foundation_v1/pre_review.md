# 환경 기본층 v1 실행 전 독립 검수

요약 판정: **수정 권장 — 현재 runner의 두 무학습 진단 실행에는 차단 사유 없음.** native 초기 상태·PD readback·카메라·실제 제어 동작은 아직 실행 전이므로 검증 완료로 판단하지 않는다. 검토자는 구현과 기존 파일을 수정하지 않았으며 이 검수 파일만 작성했다.

## Critical

현재 [진단 runner](/home/ajou/yigyu/3/stability_adapter_2/run_environment_foundation_v1.py:43) → [step(action81)](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v1.py:103) 경로에서 실행을 막을 코드 결함은 확인하지 않았다. 음악 보상·학습 API·안정성 성공 판정은 이번 범위에 없다.

## Warning

- [environment_guard_v1.py:8](/home/ajou/yigyu/3/stability_adapter_2/environment_guard_v1.py:8), [21행](/home/ajou/yigyu/3/stability_adapter_2/environment_guard_v1.py:21): 소유권 검사는 actor position-target setter, 상태쓰기 검사는 이름에 `state`가 있는 setter에 적용된다. 따라서 `set_rigid_transform`과 `set_dof_position_target_tensor(_indexed)`는 통과한다. 공식 로컬 API는 각각 body Transform 및 전체/선택 actor 목표를 쓰는 기능으로 명시한다([Transform API](/home/ajou/yigyu/3/isaacgym/docs/api/python/gym_py.html:5780), [tensor target API](/home/ajou/yigyu/3/isaacgym/docs/api/python/gym_py.html:5277)). reset 완료 뒤 fake Gym의 Transform setter까지 도달하는 것을 별도 CPU 확인했다. 현재 runner에는 이 호출이 없으므로 예정 진단을 막지 않지만, guard를 전체 native API 우회 차단으로 설명하면 안 된다. 동결본을 유지하고 확장 API/학습 연결 전 새 버전에서 해당 setter도 잠그고 검사할 것을 권장한다.
- [learning_scene_v1.py:30](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v1.py:30), [run_environment_foundation_v1.py:49](/home/ajou/yigyu/3/stability_adapter_2/run_environment_foundation_v1.py:49): 초기 이름·q·한계·PD·raw native state의 일치 조건은 코드에 있지만 CPU 검사만으로 native 결과를 입증하지 못한다. 실제 reset readback과 두 조건의 기록, 중단 시 실제 종료 시각을 최종 검수 근거로 남겨야 한다.

## Suggestion

추가 취향 변경은 제안하지 않는다. 공개 `gym` 객체를 악의적 호출에 대한 보안 경계로 취급하지 않고, 지정된 runner와 제어 경로의 계약으로 범위를 한정하면 충분하다.

## 확인한 계약과 검증 한계

- 초기 상태는 저장 candidate와 어깨 OFF 기준을 SHA로 고정한다. native float32 기준 초기 q를 사용하며 초기 위치를 한계로 조용히 잘라내지 않는다([contract:39](/home/ajou/yigyu/3/stability_adapter_2/environment_contract_v1.py:39)). 몸통 PD 배율은 장면 생성 중 한 번만 적용하고 초기 readback으로 기준과 비교한다([scene:68](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v1.py:68)).
- 81개 action에서 effective/native 범위의 절대 목표를 만든 뒤 제어 주기당 한 번 변화율을 제한한다. 목표 한 번 제출 후 4회 물리를 적분하며, 이전 66-offset API와 직접 `step_physics()`는 막는다([targets](/home/ajou/yigyu/3/stability_adapter_2/environment_contract_v1.py:86), [legacy 차단](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v1.py:57), [step](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v1.py:103)). neutral action은 초기 q를 보존하는 값이며 숫자 0과 다르다.
- 앞선 clock 불일치 지적은 60/240 literal 고정, inherited config 비교 및 native dt/backend readback으로 보완됐다([contract:77](/home/ajou/yigyu/3/stability_adapter_2/environment_contract_v1.py:77), [scene:25](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v1.py:25)). PREP/PLAY 경계는 480 physics steps이고 진단 종료는 1200 steps다. 두 초의 준비는 5초 관찰 안에 포함된다.
- COM 선속도를 body origin으로 변환한 뒤 기타 병진과 회전을 반영한 상대속도를 구성한다. 회전 6D와 16개 블록의 548차원 관측은 유한성·offset·단위를 명시하며 아직 최종 음악 정책 입력은 아니다([origin_motion](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v1.py:84), [encode](/home/ajou/yigyu/3/stability_adapter_2/environment_contract_v1.py:106)).
- [CPU 검사 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/cpu_checks.json)은 계약 검사 9개 및 Python3.8 구문 검사 5파일 통과를 기록한다. 검사 코드와 기록을 대조했고 [소비된 소스 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/consumed_sources.json) 7개가 현재 파일과 일치함을 독립 확인했다. 작은 움직임 4개 후보 진폭은 effective/native 한계 안에 있음을 CPU 산술로 확인했다.

실행 권고: 기존 소스를 동결한 채 neutral / small_motion 각각의 새 5초 native 관찰을 진행할 수 있다. GPU/Vulkan 통신 실패나 native 초기값 불일치 시 그 시도와 오류를 보존하며, 미실행·중단을 성공으로 설명하지 않는다. 최종 판정은 실제 결과와 산출물 대조 뒤 별도 `review.md`에 기록한다.
