# local G_Y −5° 후보 native 연결 검수

판정: **문제없음 — 선택 후보의 제한된 정지5초 실행 차단 없음.** Critical 0건, Warning 2건, Suggestion 0건.

대상은 [source5 shift95_front30_roll-5](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/search_v5/shift95_front30_roll-5/candidate.json:1)다. `EnvironmentContract`로 candidate/reference SHA·native 순서81·전체 q 모델 한계를 확인했다. R_Elbow_y ±5° 요청 뒤 하한/상한 여유는2.208802250469/0.583724719728rad이다. config는 이전 B 정지 조건에서 candidate 경로/SHA만 바꾸며 amplitude0·모드/reference·T40/U10·body150/1·물성/제어 설정을 유지한다.

genuine human predicted poses66개와 기타 상태39개가 존재하고, parent가 읽는30%/legacy witness 키가 유지된다. 기타 회전은 이전 G 기준 local rotvec [0,−5,0]°이며 world 넥축 변화는1.36e−16이다. 전체39 G 상태가 같은 rigid transform을 따른다는 독립 재계산의 위치/회전 잔차는≤2.49e−16, 예측 속도는0이다. 최신 [runner3 사전 코드 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/review_native_preflight_v2.md:1)의 SHA가 유지된다.

LP clear/frozen42 및 전체6caps 양수, Thorax0.322750mm<1mm·Shoulder1.884456mm·forearm23.483256mm·RHip0.300000mm/LHip2.341698mm·Chest0.989824mm를 확인했다. waist witness G_y−0.355243512m는 flank 구간[−0.365562980,−0.278240536]m 안이다. Head/왼 wrist 방향과 자연 팔 gate도 통과했다. 수락 값은 source 형상 측정이며 native 접촉 인증이 아니다.

## Warning

- 새 기타 회전/위치와 초기각·fit 설정을 함께 바꿨다. 넥축 보존을 front/back 판 또는 전체 초기 회전 보존으로 부르지 않는다. 확대된+15mm flank 수락과 좁은+5mm core·실제 걸침을 구분하고, native 초기 pose/PD/질량/source LP·접촉 및 유지 변화를 별도로 검사한다.
- 직전 source4 시험은4.783333초/1148step의 actor-root20cm 위치 보호 중단이다. 새 결과와 같은 초기 짝 비교나 회전35° 실패로 취급하지 않는다. 원 partial 원자료/영상은 보존하며 새 조건의5초 완료·반복 강건성·팔꿈치 운동/연주는 선인증하지 않는다.

## 검수 SHA-256

| 파일 | SHA-256 |
|---|---|
| candidate.json | e059fb539f88156a333de5cf584fc7a24eafc7f9c36b5cd9d67cc0741643c694 |
| config.json | 493c312b0eaad7f7cfa3a5ce2fc267ded692429c3bcbd85f185006e18bcc0b7a |
| shift95_front30_roll-5_audit.json | 1c82185274d618a9aee40439be831cf1fc2ae67b278145b369859144fc523d78 |
| run_right_thigh_waist_v3.py | 69e75bbe8ea30aa26e52e75b7227e1f9dde3d9d92ab7f0571bda1d46aaf06a18 |

읽기 전용 선택 후보·정확config·기존 제어 연결 및 순수 산술 검수다. 새 fitting/native·정책 추론/학습·다른 소스/원자료/기존 리뷰 수정은 없다.
