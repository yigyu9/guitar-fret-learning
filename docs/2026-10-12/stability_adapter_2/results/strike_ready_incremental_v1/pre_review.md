# READY 증분 목표 제어 — 독립 사전검수

요약 판정: **문제없음(PASS)**. Critical / Warning / Suggestion 없음. 기존 free-finger-curl runner와 새 runner/wrapper/계획의 차이만 검수했다. native 초기화·physics 실행은 하지 않았다.

- [run_strike_ready_incremental.py:187](/home/ajou/yigyu/3/stability_adapter_2/run_strike_ready_incremental.py:187): phase0 또는 닫힌 phase1은 이전 `env.target`+2δ, RECOVER도 기존 이전 목표+2δ다. 세 분기 모두 I를 보존한다. 열린 phase1만 기존 policy+bounded PI·최종 속도/관절 제한에 따른 적분 rollback을 사용한다. AST로 분기만 추출한 여섯 phase/open 조합의 순수 fixture에서 해당 목표와 I 유지가 일치했다. 목표 배열의 float32 반올림도 구분했다.
- [run_strike_ready_incremental.py:106](/home/ajou/yigyu/3/stability_adapter_2/run_strike_ready_incremental.py:106): 최종 제출 함수는 변경되지 않았다. 60Hz 속도 제한·native bounds·float32 제출·상태 불변 검사·source history 반영을 유지한다. δ±0.15rad 및 각 증분 2δ±0.3rad는 누적 목표의 초기각 대비 ±0.3rad 제한을 뜻하지 않는다. 누적 목표는 native bounds와 최종 속도 제한을 받는다.
- [run_strike_ready_incremental.py:298](/home/ajou/yigyu/3/stability_adapter_2/run_strike_ready_incremental.py:298): 연결/최종 report의 적분 갱신 phase 목록 `[1]` 및 `approach_open` gate가 실제 분기와 일치한다. READY/대기/회복 소유권 metadata도 실제 이전 제출 목표 기준과 맞는다. 열린 APPROACH·손가락21·네 M/R hinge +0.2rad·PREPARE·PD schedule·source 시간/감지기·기타 물리는 변경되지 않았다.
- [strike_ready_incremental_preserved_run.py:43](/home/ajou/yigyu/3/stability_adapter_2/strike_ready_incremental_preserved_run.py:43): 보수적 입력 SHA/원문 사본은 task import 전에 기록되고 종료 대조·argv 복원은 기존과 같다. trial module 연결만 새 runner로 바뀌었다. 두 Python 파일의 Python 3.8 AST 문법 및 정적 문자열 dict key 중복 검사를 통과했다.

검수 SHA256: runner `dbcb5923e0ba3740f81ceb7c359a3e8320eb3e3233ad2f02a46eff873ab46bd6`; wrapper `a0d438094c94ed5176d22ffd2969f1ddf9052c7d6a2ac10bef0fb9a89b1e6726`; 계획 `a6435009069874f864cd419944dab9c603c56da1b45661015b3b31c7cc196aff`.

사전 PASS는 실행 가능한 제어 분기·출처 구조에 대한 판정이다. 실제 READY 유지·타현·회복·안정성·성공 또는 새 물리 실행 완료를 인증하지 않는다.
