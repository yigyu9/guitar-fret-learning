# Staging damping 사전 검수

요약 판정: **문제없음 / PASS**. Critical 없음, Warning 없음, Suggestion 없음. 소비된 postclearance-prestage와 새 runner/wrapper/leaf의 변경 부분을 읽었고 native 초기화·물리 실행·source 수정은 하지 않았다.

- [runner:153](/home/ajou/yigyu/3/stability_adapter_2/run_strike_staging_damping.py:153)의 기존 stage는 source phase1·원본 시간 열림·ENTRY 미도달·READY xy>4mm를 모두 요구한다. [161행](/home/ajou/yigyu/3/stability_adapter_2/run_strike_staging_damping.py:161)의 PD 선택은 이 stage에서만 R9 baseline damping 1을 유지하고, 닫힌 phase1 및 ENTRY/EXIT는 quarter 0.25다. phase0/2와 HOLD는 baseline이다. 다른 DOF properties 필드는 바꾸지 않는다.
- PD 블록은 실제 stage 계산 뒤, IK 최적화 전에 놓였다. setter bool, 전체 properties getter exact, native 상태 불변, 불일치 fail-fast, 성공 후 expected-properties 교체·record·파일 저장의 순서가 유지된다. record의 stage/scale과 checkpoint/report 두 metadata 조건도 구현과 같다.
- 이동·변경 PD 블록을 제외한 `advance` AST는 기준과 exact이며 `submit`과 HOLD AST도 exact다. 목표 합성·source geometry/clock/criteria·손가락21/free4·PREP·속도 보정·rate/bounds·회수 동작은 추가 변경되지 않았다. wrapper는 실행 모듈명만 바꿨고 입력 사전 SHA/snapshot 및 종료 대조는 그대로다.
- 실제 PD 선택 AST만 독립 실행한 36개 순수 phase/open/ENTRY/4mm 경계 조합에서 baseline/quarter 선택과 R9 이외 필드 보존을 대조했다. runner/wrapper의 Python 3.8 AST를 확인했다. 이 확인은 실제 native damping 응답 인증이 아니다.

검수 SHA256:

| 파일 | SHA256 |
|---|---|
| run_strike_staging_damping.py | `9daeed8eb4a5f41b3532fa1fd938f49358fb6d6b4d20f1bce19cc813b199338e` |
| strike_staging_damping_preserved_run.py | `3b0f6b40552c482c1ac681a90e254f168aeb78e9effa7b8ff10468d5ea56366b` |
| STRIKE_STAGING_DAMPING_PLAN.md | `86b95aff2d50e4f5d21c409c62d8c8e83d76f170f5de653bfdcb3cc9c817b0a0` |

예상 최초 분기 3.366667초와 이전 적시 hit 보존은 새 native 자료에서 별도 검증해야 한다. source physical 판정·시간창 안 crossing을 추가 target 성공으로 간주하지 않으며, 감쇠의 인과·안정성·완주 성공·학습은 이 사전 PASS로 인증하지 않는다.
