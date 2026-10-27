# 현재 기타 기준 Strike 진단 사전 검수

요약 판정: 수정 권장. 현재 읽은 실행 경로의 즉시 물리 blocker는 발견하지 않았다. 다만 아래 provenance 및 probe-only 검증 범위를 보완해야 하며 전체 전이 계약 PASS나 연주 성공으로 확대하지 않는다. 검수자는 코드·원자료를 변경하거나 actor/native/테스트/분석 본체를 실행하지 않았다. 다른 담당자 파일과 기존 봉인 결과는 보존한다.

## Critical

현재 검토 범위에서 확인된 항목 없음.

## Warning

1. [run_strike_live_probe.py:91](/home/ajou/yigyu/3/stability_adapter_2/run_strike_live_probe.py:91) — `sys.modules`의 패키지 prefix 목록에는 `-m` 실행의 producer `__main__`가 없으며 실제 비Python 입력 config/pose/gains/asset mesh·BASE·FACETS도 빠져 있다. 또한 hash 수집은 checkpoint load와 fresh 초기 감사 이후다. 저장 probe_v3/attempt의 63개 현재 SHA는 전부 일치하지만 현재 runner 및 위 직접 입력은 실제 목록에 없다. 소비본을 수정하지 말고 다음 별도 버전에서 `Path(__file__)`와 직접 읽는 자료/helper 입력을 초기화·측정 전에 manifest/사본으로 보존한다. 외부 wrapper의 추가 보존은 별도 근거로 구분하며 이 attempt의 inputs_unchanged를 전체 소비 입력 인증으로 설명하지 않는다.

2. [run_strike_live_probe.py:119](/home/ajou/yigyu/3/stability_adapter_2/run_strike_live_probe.py:119), [run_strike_live_probe.py:147](/home/ajou/yigyu/3/stability_adapter_2/run_strike_live_probe.py:147) — probe-only에서 advance/step 루프를 0회 수행하므로 commands_preserve_state/held_other39/target_bounds/root_lower_fixed의 true는 초기값이다. 현재 저장 report도 physics0/control0/videos없음/5초완료false다. 반사실 관측 검사 완료를 실제 source 후처리·rate/native 제한·history 회신 검증 완료로 해석하면 안 된다. 새 버전의 읽기 전용 목표 조립 검사 또는 이후 실제 첫 명령 저장 대조를 해당 근거로 따로 기록한다.

## 코드 정합과 확인 범위

- [strike_native_view.py:25](/home/ajou/yigyu/3/stability_adapter_2/strike_native_view.py:25)의 원본 Base shared_backend 필수 속성/단일환경 CPU tensor layout은 현재 Base 소비 경로에 맞는다. body/root pose·twist·joint 상태는 실제 native 복사이며 접촉 force는 SDK readback이고 비측정 초기 sentinel을 0 측정으로 꾸미지 않는다. ReadonlyGym은 원본 task에서 simulator 호출을 거절한다.
- [strike_native_view.py:103](/home/ajou/yigyu/3/stability_adapter_2/strike_native_view.py:103)는 checkpoint Strike config와 training context를 원본 constructor/stage에 전달하고 원본303 packer를 사용한다. grip reference 후처리 객체를 유지하면서 물리 초기 목표와 history를 실제 native 초기각으로 되돌린다. native joint range와 초기 자세/actuator를 사용하는 독립 연구 진단으로만 해석하며 원본 학습 환경의 전체 ABI·공식 G0 자격 동등성은 인증하지 않는다.
- [strike_native_view.py:84](/home/ajou/yigyu/3/stability_adapter_2/strike_native_view.py:84)는 terminal reset 요청을 기록하는 no-op이며 terminal observation을 반환한다. 원본 task done을 [runner:154](/home/ajou/yigyu/3/stability_adapter_2/run_strike_live_probe.py:154)에서 받아 더 이상 다음 명령을 실행하지 않는다. source reset이 물리 state를 덮어쓰는 경로는 없고, 예외도 failure 및 partial 자료로 남긴다.
- [run_strike_live_probe.py:120](/home/ajou/yigyu/3/stability_adapter_2/run_strike_live_probe.py:120)는 LH12 PI와 RH30을 한81목표로 합성한다. 남은39는 초기 목표 exact이며 RThorax3도 그 집합이다. RH는 원본 pick-grip 후처리·EMA 뒤 .8rad/s 및 native bound 제한을 받고 실제 float32 제출 목표를 source pd_target/history에 회신한다. 한60Hz source step당 native240Hz 4step으로 원본 phase/detector/song clock의60Hz를 유지한다. Native loop는 inherited no-strap simulate/fetch이며 외력·state overwrite 없이 PD position 목표만 제출한다. rate 제한이 바꾼 actuator/history 전이를 원본 source replay와 동일하다고 인증하지 않는다.
- [counterfactual:34](/home/ajou/yigyu/3/stability_adapter_2/run_strike_live_probe.py:34)의 whole-scene 회전은 수직 Z축이라 world gravity와 모순되지 않는다. 기타-only 및 전체 scene의 pose와 선속도/각속도를 같이 변환하고 이후 복사 buffer를 복구한다. 실제 native state는 변경하지 않는다. 저장 반사실 결과의 string transform 최대 오차는 약0.2522µm, whole-scene 관측 최대 차 약1.2815e-6이며 기타+10mm/5°에서는 관측과 actor 출력 변화가 관측됐다. 이는 CPU 입력 반응 근거이며 실제 자유 기타 타현/음악 성공 근거가 아니다.
- 계획은 RH 비접촉을 초기 조건으로만 제한하고 타현 중 접촉을 허용한다. 공식 양손 G0 qualification false/학습0/music_success false와 source explicit torque 대 native implicit position PD 차이를 명시한다. 5초 결과·native 명령 raw·영상·최종 산출물은 후속 검수 대상이며 아직 봉인하지 않는다.

## 소스 식별

Python3.8 AST는 두 새 Python 파일에서 통과했다. 현재 읽은 파일 SHA:

- 계획: `5bbaf6920370ac24d29ca94e99aa7bbc172df057499dfa8b4a6a08d2a3b349c2`
- strike_native_view.py: `a092510e0fccb2dea99d9e80a466ac6b46208b73169614e12bbbaecd6dfccdb2`
- run_strike_live_probe.py: `7470bef1dd661bd6e4c5cf082e5e30bb340646db756fe588d9cd082b84600da0`

이 사전 검수는 소비본의 남은 한계를 기록한 것이며, 최종 실험 성공 또는 전체 provenance 봉인 판정이 아니다.
