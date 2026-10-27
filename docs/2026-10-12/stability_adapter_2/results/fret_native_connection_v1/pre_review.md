# Fret native 연결 사전 검수

요약 판정: **문제없음 — 사전 정적 검수 PASS**. Critical / Warning / Suggestion 없음. 실제 운지 성능과 native 실행 검증은 아직 수행 전이며 이 판정에 포함하지 않는다.

검수 범위는 이번에 추가된 `fret_native_view.py`, `run_fret_native_connection.py`, `fret_native_preserved_run.py`, `FRET_NATIVE_CONNECTION_PLAN.md`이다. 공용 Fret 구현은 연결부의 호출 계약을 확인하는 데만 읽었다. 코드 수정은 하지 않았다.

- [fret_native_view.py:22](/home/ajou/yigyu/3/stability_adapter_2/fret_native_view.py:22): 원본 Fret 소스 SHA와 AST 경계를 검사한 뒤 action의 tensor 처리와 물리 이후 평가 부분만 추출한다. 평가 tail에는 `apply_actions`, `step_physics`, `refresh` 호출이 없다. 원본 shared-view 금지 분기는 보존된다.
- [fret_native_view.py:57](/home/ajou/yigyu/3/stability_adapter_2/fret_native_view.py:57): terminal reset은 표시만 하고 물리 상태를 바꾸지 않는다. view의 `step_physics`는 예외를 발생시키며 실제 물리 전진은 native owner에 한정된다.
- [fret_native_view.py:76](/home/ajou/yigyu/3/stability_adapter_2/fret_native_view.py:76): checkpoint의 goal·hand target·asset·profile 계약을 원본 검증 함수로 확인한다. profile 범위는 복사된 view의 정규화와 목표 범위에만 적용되며 native XML hard limit을 변경했다고 주장하지 않는다.
- [run_fret_native_connection.py:42](/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection.py:42): checkpoint SHA, 420 관측 / 30 행동 / 6 value 계약, DOF 순서와 strict state-dict 로딩을 확인하고 actor를 동결한다.
- [run_fret_native_connection.py:49](/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection.py:49): Fret 30축, hold 15축, 초기 목표 유지 36축이 분리되어 있다. PLAY에서 기존 L9 hold 결과는 Fret 목표에 더해지지 않는다. 첫 독립 시험에서 Strike actor를 사용하지 않는다는 계획과 일치한다.
- [run_fret_native_connection.py:86](/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection.py:86): 준비 120 control step 동안 actor와 source clock을 사용하지 않고 2초에 이관한다. EMA history는 실제 제출한 목표에서 구성하며, 한 번의 목표 제출 뒤 native 4 substep을 전진시키고 원본 평가를 한 번 수행한다.
- [run_fret_native_connection.py:123](/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection.py:123): 원본 done을 유지하고 첫 terminal에 즉시 중단한다. 고정 5초 종료나 terminal 이후 HOLD 프레임을 추가하지 않는다. 마지막 실제 물리 상태가 camera 격자에 없으면 한 번 추가 기록한다.
- [run_fret_native_connection.py:136](/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection.py:136): 예외 발생 시에도 controls·trace를 close/encode 전에 저장하며 finalization 오류와 최초 실패를 분리해서 report에 남긴다.
- [fret_native_preserved_run.py:21](/home/ajou/yigyu/3/stability_adapter_2/fret_native_preserved_run.py:21): import 전에 소스·입력 SHA 및 A 소스 snapshot을 저장하고 실행 후 변경 여부를 검사한다. 새 출력 경로는 이미 존재하면 거부한다.

검증: 새 Python 3개 파일 AST parse PASS. 원본 Fret SHA 일치, step prefix 및 tail의 물리 호출 부재, action의 원본 base EMA/PD 연결을 확인했다. native 실행 결과·render 보존·실제 범위 초과·contact·종료 이유는 후속 검수에서 확인한다. CPU PhysX와 native XML 범위를 쓰는 이번 연결을 원본 고정 기타 GPU 학습 환경과 동등하다고 판정하지 않는다.

검수 당시 SHA-256:

| 파일 | SHA-256 |
|---|---|
| `fret_native_view.py` | `32ad86f88791cbaf6dc1872ac2d34a26434a2a1b3c57dc338e413fdc8599ae8c` |
| `run_fret_native_connection.py` | `69ff9929e16cd8302226517aed527887b822348f9b0ea6214cca8c5c3fa2ec4b` |
| `fret_native_preserved_run.py` | `76993320f40bec7db791698d56c4ed0fc13a5d117609dc1d2c5c6d39df71ffa1` |
| `tab2body/env/tasks/task_fret.py` (읽기 전용) | `095b1860058ebab5d89785a8a99b1fb97cf26a25308be90d48f8d7a3b5dcdd92` |
