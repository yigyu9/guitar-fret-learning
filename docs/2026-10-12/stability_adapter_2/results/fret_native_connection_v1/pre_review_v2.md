# Fret native 전이 연결 v2 사전 검수

요약 판정: **문제없음 — 사전 검수 PASS**. 현재 Critical / Warning / Suggestion 없음. 실제 native 물리 실행과 운지 성능은 이 판정에 포함하지 않는다.

범위: 새 `fret_native_view_v2.py`, `run_fret_native_connection_v2.py`, `fret_native_v2_preserved_run.py`, `FRET_NATIVE_CONNECTION_V2_PLAN.md` 및 보완 검증 `preflight_fret_native_connection_v3.py`. v1 정적 검수 이후 원본 asset SHA 불일치로 setup이 차단된 사실을 반영했다. v1 실행 성공을 주장하지 않는다. 검수자는 구현을 수정하지 않았다.

- [fret_native_view_v2.py:77](/home/ajou/yigyu/3/stability_adapter_2/fret_native_view_v2.py:77): checkpoint 문서·goal·hand target·profile/prior SHA와 저장된 설정을 확인한다. 원본 asset 동일성 검사를 적용하지 않는 것은 자유 기타 전이 진단의 명시된 변경이며, [run_fret_native_connection_v2.py:67](/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection_v2.py:67)에서 asset/implementation 차이를 기록한다. 원본 평가 환경과의 동등성 검증으로 설명해서는 안 된다.
- [fret_native_view_v2.py:23](/home/ajou/yigyu/3/stability_adapter_2/fret_native_view_v2.py:23): 원본 Fret SHA와 AST 경계를 고정한다. tensor-only action 처리와 물리 이후 평가 tail을 분리하고, 원본 shared step/apply/reset 금지는 유지한다. 평가 tail에서 물리를 전진시키는 호출은 없다.
- [fret_native_view_v2.py:58](/home/ajou/yigyu/3/stability_adapter_2/fret_native_view_v2.py:58): terminal reset은 표시만 하고 terminal 물리 상태와 관측을 보존한다. view 자체의 physics 전진은 차단된다.
- [fret_native_view_v2.py:92](/home/ajou/yigyu/3/stability_adapter_2/fret_native_view_v2.py:92): profile은 복사된 source view의 정규화·정책 목표 범위에 적용한다. native XML hard limit과의 차이는 audit에 명시되며 물리 관절 상태를 덮어쓰지 않는다.
- [run_fret_native_connection_v2.py:42](/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection_v2.py:42): checkpoint SHA, 420 관측 / 30 행동 / 6 value, 관절 순서, 관측 manifest, action scale/EMA 및 strict model state-dict 계약을 확인하고 actor를 동결한다.
- [run_fret_native_connection_v2.py:49](/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection_v2.py:49): PLAY의 Fret 30축, bounded hold 15축, 초기 유지 36축은 겹치지 않는다. policy 관절에 기존 L9 hold를 더하지 않는다. 오른손 Strike actor는 꺼 둔다.
- [run_fret_native_connection_v2.py:88](/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection_v2.py:88): 120 control step 준비 후 정확히 2초에 이관한다. source 준비 clock을 대체하고 실제 제출 목표에서 EMA history를 구성한다. 한 목표 제출 후 native 4 substep 전진과 원본 평가를 각각 한 번 수행한다.
- [run_fret_native_connection_v2.py:125](/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection_v2.py:125): 원본 첫 done에서 actor 호출을 중단하며 끝 상태를 기록한다. 5초 제한 또는 terminal 이후 정지 프레임이 없다. 예외 시 controls·trace를 finalization 전에 저장한다.
- [fret_native_v2_preserved_run.py:21](/home/ajou/yigyu/3/stability_adapter_2/fret_native_v2_preserved_run.py:21): native import 전 입력 SHA와 A 소스 snapshot을 보존하고 실행 후 변경 여부를 검사한다. 기존 출력 경로는 거부한다.

검수 중 발견한 검증 문제는 별도 v3 파일로 해결됐다. 보존된 preflight v2는 action cache로 바뀐 `O_history`와 기타 이동 효과를 함께 비교했으므로 해당 `moving_guitar_observation` 결과는 단독 근거로 쓰지 않는다. [preflight_fret_native_connection_v3.py:50](/home/ajou/yigyu/3/stability_adapter_2/preflight_fret_native_connection_v3.py:50)는 cache 이후 baseline을 다시 구해 기타 이동 효과만 비교하고, 이동을 복원하면 관측이 baseline과 완전히 같음을 확인한다.

[preflight_tensor_v3.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/preflight_tensor_v3.json)의 10개 검사는 모두 PASS다. 복사된 기타를 10mm 이동했을 때 관측 최대 변화는 `0.010000020265579224`다. 이는 보존된 native t=0 snapshot과 mock simulator·명시적 zero contact-force 입력에서 수행한 tensor 검증이며 실제 접촉력 측정이나 물리 rollout 결과가 아니다. 검수 대상 Python 파일 AST parse PASS.

검수 당시 SHA-256:

| 파일 | SHA-256 |
|---|---|
| `fret_native_view_v2.py` | `625b810734203c1441a2d71ac82b3a4fdcfa40acf97bd10c8e693dce5e523d71` |
| `run_fret_native_connection_v2.py` | `c244419a7bbf37b5bf79bca4e0139f5636cf8b0631f96c1c5e82e5a82995fa4c` |
| `fret_native_v2_preserved_run.py` | `c8516ca582123801795de1df821501cf453abb9d832be82bfbcd506ed27d8de1` |
| `preflight_fret_native_connection_v3.py` | `bb0d64ac3b4c859ffee93acd266722b3885461461ce3a62be5eeb262c85386fb` |
| `FRET_NATIVE_CONNECTION_V2_PLAN.md` | `5e4b310f2e4a4cc821d244ff5caae3fffab6c326a757a2839c8a7756fafb6865` |
