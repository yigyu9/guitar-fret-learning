# 자유 기타 환경 연결 사전 검수

검수 범위: `environment_v2.py`, `test_environment_v2.py`, `run_smoke_v4.py` 및 호출되는 기존 최종 목표 제출·유한 effort 경로. 원본 수정, native scene 생성, GPU 또는 물리 실행은 수행하지 않았다.

**판정: environment_v2의 CPU 계약 검수는 통과했으나 run_smoke_v4는 실행 전 수정 필요.** CPU 계약 검사는 독립 실행에서 7/7 통과했다. 이는 실제 준비 자세 재현이나 정책 안정성 통과 판정이 아니다. 최초 검수에서 놓친 runner의 실제 차단 문제를 root가 확인하여 실행 가능 판정을 철회했다.

## Critical — 새 codec 의존성을 과거 native 입력으로 오분류

`run_smoke_v4.py:61`은 새 bridge 디렉터리 밖의 모든 import를 원 native 입력으로 분류한다. 이번에 새로 재사용하는 `music_pipeline_v2/control.py`, `music_pipeline_v3/control.py`는 과거 native expected map에 없으므로 89–91행의 검사가 반드시 실패한다. 이 둘은 새 bridge 의존성으로 실행 전후 SHA를 보존하고, 실제 원 runtime/assets에는 기존 expected SHA 검사를 계속 적용해야 한다. 후속 runner v5에서 수정 예정이며 별도 검수가 필요하다.

- 실제 준비 22초의 최종 제출 목표를 기준으로 정규화39 행동을 해석한다. upper42는 유지하고 lower24는 원래 발 유지 제어가 조절한다.
- 정책 단계는 이전 음악 동작/LH IK/예약 목표 보정을 우회하여 `scene_v8.Scene.command`에 한 번 제출하고, 원래 effort 제어를 유지한다. 추가 PD를 중복 적용하지 않는다.
- 이름105, 비영범위97, 명목 영범위8, 고정 인간 root, 자유 기타와 중력, 목표 제출 중 물리 상태 비변경을 검사한다.
- 행동0 유지와 원 baseline 동작 목표는 구별하여 비교한다. 기존 V3 통과를 새 환경의 결과로 계승하지 않는다.
- runner v4는 실제0초 설정·상태와 준비22초 상태를 남기고, 원 manifest의 자산/코드 SHA와 비교한다. 실행 전 코드 pin 및 실행 후 실제 import 누락/불일치 검사를 수행한다. 영상 인코딩 오류도 결과 보고서에 남긴다.

## Warning — 메타데이터 범위

`environment_v2.py:136`의 `target_contract`는 기존 upper81 codec 메타데이터를 포함한다. `music_pipeline_v2/control.py:91`의 thigh.scope에는 “external fixed-lower asset contract”가 남아 있다. 이는 현재 환경 전체의 하체 제어 설명으로 인용하면 안 된다. 같은 reset 메타데이터의 `nonpolicy_target_scope`가 현재 finite lower24 역할을 명시한다. 후속 정리 시 원 codec은 보존하고 환경 범위에 맞는 별도 설명을 제공할 것을 권장한다. 제한된 물리 연결 시험을 차단하는 오류는 아니다.

## 확인 기록

명령: `PYTHONDONTWRITEBYTECODE=1 /home/ajou/miniconda3/envs/rl38/bin/python -m unittest stability_adapter_2.free_guitar_learning_v1.test_environment_v2 -v`

결과: 7 tests, OK. 테스트가 `.environment_v2`를 실제로 import하는 것을 확인했다. 테스트는 가짜 세션의 소유권·입력·reset 계약 검사이며 native 정확성 검사는 후속이다.

검수된 SHA256:

| 파일 | SHA256 |
| --- | --- |
| environment_v2.py | `30aa0ca879d6ca5675e692b33e4d8e7152a4a76ea920eaac83d551db81de55ea` |
| test_environment_v2.py | `4564acb44619ba946c6cd44479380173611380befccdc69e8c9fb6563a26e1f0` |
| run_smoke_v4.py | `d596ada6361858ef38963157c1da398c392fd1ad4fc9a568f3acba49e728cddb` |

후속 native 시험에서는 두 독립 초기화의 실제 설정/준비 상태, 제출 목표 및 원 effort, 행동0/작은 비영행동 연결, 기타 자유 상태와 금지 호출, 원입력 불변 여부를 실제 기록으로 판정해야 한다. 이번 사전 검수는 음악 보상·타현/압현 성공·PPO 학습 또는 장기 안정성을 인증하지 않는다.
