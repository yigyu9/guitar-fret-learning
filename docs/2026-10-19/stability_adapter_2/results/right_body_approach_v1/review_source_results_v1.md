# source 세 후보 완료 검수

요약 판정: **문제없음 — 지정 source 후보/설정 연결 범위**. Critical 0 / Warning 2 / Suggestion 0. native 결과의 회복 여부와 별도 판정이다.

[source 완료 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/search_v1/search.json:1)은 3/6/10mm 세 후보를 모두 검사·수락했고, 각 audit와 candidate의 수락 행이 같다. 입력 746개는 현재 SHA와 일치한다. 세 config 모두 후보 경로/SHA 외 현재 waist 정지 config와 동일하며 native reference SHA도 맞다.

| 후보 | 높이 재맞춤 world ΔZ | Thorax gap | 근위 상완 gap | 오른 Hip gap | Hip witness G_y |
|---|---:|---:|---:|---:|---:|
| 3mm | −0.166893mm | 0.301694mm | 1.993185mm | 0.300006mm | −0.354706m |
| 6mm | −0.333726mm | 0.302528mm | 1.991688mm | 0.300015mm | −0.354168m |
| 10mm | −0.539958mm | 0.304493mm | 1.984619mm | 0.300002mm | −0.303915m |

81관절 유한값/모델 범위·선언 변경 범위·팔꿈치 ±5° 여유와 finger42 exact를 확인했다. 세 후보의 native 기준 보정 FK를 순수 수식으로 재계산해 human66 예측 오차가 최대 2.31e−16m/5.90e−16rad였다. G39 rigid 변환과 이전 기타 회전도 일치한다. 각 source_clear와 최종 capsule/waist/손목·머리·팔 형상 수락 항이 기록됐고 [수락 구현](/home/ajou/yigyu/3/stability_adapter_2/search_right_body_approach_v1.py:85)은 전체 audit를 적용한다. 검수자가 LP 최적화/전체 형상 감사를 다시 실행한 것은 아니다.

## Warning

1. [source witness 검사:93](/home/ajou/yigyu/3/stability_adapter_2/search_right_body_approach_v1.py:93)에서 10mm의 가장 가까운 Hip 지점은 좁은 core 안으로 옮겨지고 3/6mm는 flank에 남는다. 이 source witness 전환은 실제 cooked 접촉 분포·지지력 기여나 향후 두 블록 회복의 인과 증거가 아니다. 실제 5초 원자료의 후기 Thorax/상완 동시 접촉과 기타 변화를 별도로 비교해야 한다.
2. [앞선 연결 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_body_approach_v1/review_native_preflight_v1.md:1)의 이전 핀 범위 정정과 무왼손/장기/연주 미검증 제한을 유지한다. 세 config의 동일성은 제어 설정 보존을 뜻하며 초기 IK 각도 차이를 제거한 인과 비교는 아니다.

## 확인 SHA-256

- search 완료 JSON: `434deb446d6426f531165dc8fcf46850fdb3cdad829162c3428cba620740471e`
- 6mm config: `aba7c6ed675c2e9997eb4e3fdb3a3e8dfa11246218607494e88f1ea9ae15c30e`
- 6mm candidate: `651cb862589c01fbb415fdf341cf2e3356913a28b2541532c9dc75e249e4471b`
- 10mm config: `709386e6962f9a37c74b9deae0dae7bd39d9c2ec0ce146d4fc4ffa9c02ee8080`
- 10mm candidate: `8e63eb72d55891037080e5f138847975f6ace91fd3a7678b302e6e05bf2a8b92`

새 최적화·native·정책·학습을 실행하지 않았고 소유한 새 리뷰만 작성했다. 진행 중 native 실행의 결과는 포함하지 않는다.
