# Postclearance prestage 사전 검수

요약 판정: **문제없음 / PASS**. Critical 없음, Warning 없음, Suggestion 없음. native 초기화·물리 실행 없이 현재 코드와 frozen lateral-staging 기준의 변경 부분을 검수했다.

- [runner:190](/home/ajou/yigyu/3/stability_adapter_2/run_strike_postclearance_prestage.py:190)의 S3/phase2 경계 안에서만 현재 musical event masks와 원 `strike_next_traversal_string` helper로 entry를 복원한다. 현재 방향·lane은 cached recovery target과 분리되며, [201행](/home/ajou/yigyu/3/stability_adapter_2/run_strike_postclearance_prestage.py:201)은 context valid, scheduled completion, 필요한 clearance reached, entry/direction/lane 불일치를 모두 요구한다.
- 새 READY의 xy는 원 lane/방향/ready-across 식이고 z는 string z + max(READY height, clearance height)다. [178행](/home/ajou/yigyu/3/stability_adapter_2/run_strike_postclearance_prestage.py:178)의 원 source waypoint는 복사·별도 로그로 보존한다. source phase/clock/flags/detector/geometry를 수정하지 않고 adapter waypoint만 IK 목표에 전달한다.
- 변경 gate/geometry AST만 추출해 S3·phase·context·completion·clearance·mismatch·DOWN/UP 256개 조합을 순수 fixture로 대조했다. 활성화 때만 새 좌표가 선택되고 비활성화 때 원 source 좌표가 유지됐다. 이는 실제 native trajectory 검증이 아니다.
- 기존 submit AST는 exact다. R9 이전 actuator target + 2δ, local ±0.15rad, velocity −0.1s/max5mm, rate/native bounds, I 유지, 손가락 policy/free4, PREP/native PD schedule/terminal HOLD 경계를 바꾸지 않았다. wrapper는 사전 입력 SHA 및 source snapshot 뒤 새 모듈을 실행하고 argv 복원·종료 입력 대조를 유지한다. 새 runner/wrapper의 Python 3.8 AST도 확인했다.

검수 SHA256:

| 파일 | SHA256 |
|---|---|
| run_strike_postclearance_prestage.py | `5ff37667bb34b03414f681da370e9c40fd5cabd8654a89ab876ac6a8ce8b020a` |
| strike_postclearance_prestage_preserved_run.py | `67f33cb1ff104bb6b989233d59a6ad4cbe34ade0cbf8f239321aaf1cb8b05711` |
| STRIKE_POSTCLEARANCE_PRESTAGE_PLAN.md | `af98cc56d082a7a4995f5896a58ac742d9f4d52a899e8dbb1c5510259b8c5214` |

저장된 이전 회복 완료 시각으로 예상한 첫 분기와 네 적시 hit 보존은 아직 새 native 결과로 검증하지 않았다. 제어 후보의 실제 타현·안전·완주 성공·학습·원인 판정은 이 사전 PASS에 포함되지 않는다.
