# inset3mm — native 연결 사전 검수

요약 판정: **문제없음 — 지정 3mm 후보의 기존 guard를 유지한 5초 정지 시험 진행 가능**. Critical 0 / Warning 2 / Suggestion 0. 실제 native 실행 결과와 후기 두 블록 접촉 회복은 아직 인증하지 않는다. 계산 중인 나머지 후보는 이 판정에 포함하지 않았다.

## 확인한 연결

- [선택 config](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/search_v1/inset3mm/config.json:1)는 후보 경로/SHA 외 현재 waist 정지 config와 정확히 같다. native reference SHA도 맞고 mode/gain/제어/물성 설정은 변경되지 않았다. 후보·audit의 수락 행은 일치하며 전체 source_clear가 true다.
- 초기81 q는 유한하고 모델 범위 안이다. finger42는 현재 waist 기준과 exact 일치한다. 몸통9/오른12/왼12/머리6의 최대 변경은 각각 0.066031/0.035975/0.029065/0.016306rad로 선언 범위 안이다. R_Elbow_y는 ±5°를 추가한 뒤에도 하한·상한에 2.219087/0.573440rad의 여유가 있다.
- native 초기 기준으로 보정된 순수 FK를 재계산해 human66 예측 위치/회전 오차가 각각 최대 1.67e−16m/5.35e−16rad임을 확인했다. G39는 후보 root 기준 단일 rigid 변환으로 정확히 연결되며 위치 오차 최대 5.55e−17m, 회전 오차 0이다. 현재 기타 회전/넥 방향은 보존된다. 실제 설정 이동은 world `[+0.115961,−2.997756,−0.166893]mm`이며 마지막 성분은 허벅지 높이 재맞춤이다.
- source gap은 Thorax 0.301694mm, 상완 1.993185mm, 전완 22.403440mm, 오른/왼 허벅지 0.300006/1.994109mm, Chest 1.632505mm다. 왼 손목 위치 오차 7.70e−9m·방향 오차 4.44e−6°, 머리 방향 오차 2.18e−6°도 수락 조건 안이다. 이들은 source proxy 값이다.
- source 시작 전 입력 746개를 현재 SHA와 대조했다. [native entry:36](/home/ajou/yigyu/3/stability_adapter_2/run_right_body_approach_v1.py:36)에 실제 guitar XML mesh 전부가 포함된다. 기존 waist runner3와 비교한 변경은 설명과 mesh pin뿐이며 33 EFFORT/48 POSITION, 단일 제출·4 physics step, 자유 기타/strap OFF/root·하체 고정은 같다. [native 초기 검사:55](/home/ajou/yigyu/3/stability_adapter_2/run_right_body_approach_v1.py:55)의 후보 G39·모델/FK·PD·질량·finger42·root/하체·actual pose source LP gate도 유지된다.

## Warning

1. [초기 감사 gate:88](/home/ajou/yigyu/3/stability_adapter_2/run_right_body_approach_v1.py:88)를 통과해도 실제 cooked 비접촉이나 후기 Thorax–상완 동시 지지를 뜻하지 않는다. 이전 기준의 왼손 손가락 접촉도 분리되지 않았다. 이번 진행 판정은 한 번의 5초 정지 관측이며 힘 기여·무왼손·수동 집게·연주·장기 강건성 인증으로 확대하지 않는다.
2. **이전 입력 감사 한계의 정확한 정정:** 이전 waist [source5 before map](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/search_v5/inputs_before.json:1)에는 neck1/neck2가 이미 있었고, 추가 XML 선언의 `upper.obj/lower.obj/headstock.obj` 3개가 없었다. 이전 [native attempt](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/native_elbow5_v1/attempt.json:1)는 해당 5개 모두 핀돼 있었다. 앞선 새 source 사전 검수의 “이전 5개 누락” 포괄 표현은 이 실제 map 구분으로 정정한다. 이번 before로 과거 source의 누락 3개를 소급 인증하지 않는다. 소비된 이전 리뷰/자료는 수정하지 않았다.

## 확인 SHA-256

- 후보: `552d894863eb4ccfbec336dafa7bc4328441db9e631bbd21d43737732820d8e3`
- config: `4fe7452f499e2b4c4e404e0f76f342862d160fb4f4626249f34b2ae7f0769e47`
- audit: `52a3c64bd5ca00bf281e876078226a29f3ac28b7f5ead2623b243260f9e143f4`
- native entry: `420f8fffd4b9d87087c2fe2d6019485e5d34bb5d52b929d60bec0bc74525ad72`

검수 중 새 최적화·정책·native·학습을 실행하지 않았고 소유한 새 리뷰만 작성했다.
