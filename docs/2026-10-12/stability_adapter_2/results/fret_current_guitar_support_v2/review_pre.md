# 준비 지지 관계 유지 v2 사전 검수

**요약 판정: 문제없음.** 이번 ON native 실행 전에 반드시 수정할 문제는 확인하지 못했다.

- Critical: 없음.
- Warning: 없음.
- Suggestion: 없음.

지정한 신규 5개 파일을 v1 구현과 직접 비교했다. 구현·기존 문서·v1/native/분석 결과를 수정하지 않았고 native trial을 실행하지 않았다. 기록한 파일은 이 검수 문서뿐이다.

## 확인한 근거

- [fret_current_guitar_support_v2.py:21](/home/ajou/yigyu/3/stability_adapter_2/fret_current_guitar_support_v2.py:21): handoff actual 손목의 기타 local 위치와 상대 회전을 고정한다. 매 solve의 현재 기타 p/q로 지지 목표를 world에 변환하며, source 손목 anchor는 solver 입력에서 제거됐다.
- [fret_current_guitar_support_v2.py:22](/home/ajou/yigyu/3/stability_adapter_2/fret_current_guitar_support_v2.py:22): 준비 마지막 목표 ±0.1rad를 기존 초기 ±0.3rad/native 교집합과 다시 교차한다. reference가 준비 제출 목표이며, actual q로 초기화한 FK와 actual Chest p/q 보정 및 매 solve의 FK/native 검사가 유지된다.
- [fret_current_guitar_support_v2.py:48](/home/ajou/yigyu/3/stability_adapter_2/fret_current_guitar_support_v2.py:48), [run_fret_current_guitar_support_v2.py:139](/home/ajou/yigyu/3/stability_adapter_2/run_fret_current_guitar_support_v2.py:139): 0.3rad/s가 solver bounds와 최종 ON left9 제출 제한에 모두 적용된다. 손가락21 및 support15의 기존 제한은 유지된다.
- [run_fret_current_guitar_support_v2.py:107](/home/ajou/yigyu/3/stability_adapter_2/run_fret_current_guitar_support_v2.py:107): 정확히 준비 2초의 native state로 support 기준을 만들고 handoff 파일에 저장한다. 2초 전의 목표·정책 미사용·source clock 고정 흐름은 v1과 같다.
- [run_fret_current_guitar_support_v2.py:125](/home/ajou/yigyu/3/stability_adapter_2/run_fret_current_guitar_support_v2.py:125): 보정은 left9만 교체하고 `source_wrist_error_m`는 측정에만 사용한다. frozen finger21 합성, 단일 목표 제출자, 실행된 목표에 대한 source pd_target/prev_action, other36/root/하체 고정 검사는 유지된다.
- [run_fret_current_guitar_support_v2.py:158](/home/ajou/yigyu/3/stability_adapter_2/run_fret_current_guitar_support_v2.py:158): source 평가·보상·실패·goal clock을 변경하지 않고 첫 done에서 즉시 종료한다. raw COLOR-only 녹화 helper와 보존 wrapper도 유지된다. 신규 상태/힘 제출은 없다.

## 독립 검증

rl38 Python에서 저장된 fret_fingers_arm_hold_v1 handoff 및 2/4/8/12초 native 상태를 읽는 별도 검사 20항목이 모두 통과했다. 실제 runtime와 같은 float32 초기/한계 배열을 사용했다.

- left9 정확한 이름/순서, prepared 값의 bounds 포함, prepared ±0.1rad 및 initial ±0.3rad envelope.
- handoff 시 지지 목표의 위치·회전 오차 각각 1e-12 미만, 입력 state 보존.
- 2/4/8/12초 FK/native 일치, 0.3/60rad 목표 변화율, 최종 envelope.
- 기타 p/q를 별도 입력 상태에서 이동·회전시켰을 때 저장한 wrist_G의 현재 기타→world 변환 일치.

저장 상태 검사의 최대 FK 위치 오차는 1.623e-7m, 회전 오차는 2.812e-7rad였다. 신규 Python 3개 AST parse와 shell wrapper `bash -n`도 통과했다. native trial은 0회다.

## 후속 결과를 읽을 때의 범위

v2 ON의 `arm_correction.wrist_error_m`는 지지관계 목표 오차다. v1 OFF의 동일 이름은 source anchor 오차이므로 두 값을 같은 지표로 직접 비교하지 않는다. source 목표 비교에는 v2 ON의 `source_wrist_error_m`와 v1 OFF의 source 오차를 사용하며, OFF 지지관계 오차는 raw state 및 handoff 관계로 별도 계산한다.

저장 자료 검사는 실제 ON에서 기타 이동이나 실패가 개선됨을 입증하지 않는다. 실제 준비 구간의 v1 OFF exact 일치, 동역학·기타 범위·운지 오차·첫 source terminal·전체 영상은 후속 native 자료로 확인해야 한다.

## 검수 SHA256

| 파일 | SHA256 |
|---|---|
| FRET_CURRENT_GUITAR_SUPPORT_V2_PLAN.md | 5aec4e187f99b7ec35ff22407f163da080342b9b25cab0bf39da44b3d82884af |
| fret_current_guitar_support_v2.py | 04638f7db6f77625d6766fb959398b01803c0956610b81aeb31bdb4d42ac3a4e |
| run_fret_current_guitar_support_v2.py | 4c664ab0c5b792d1e49ea007480ad93a803c1c46eab6af1f218b4c3d8379a10b |
| fret_current_guitar_support_v2_preserved_run.py | 0a3f6c5d9135f743404bd5e9ece9838d8388a709e674c0cd5c70c045d3104181 |
| run_fret_current_guitar_support_v2.sh | d87a999d621939422538e4276edb8057d2d21bd02ed5d5526ebc99dbaff566be |
