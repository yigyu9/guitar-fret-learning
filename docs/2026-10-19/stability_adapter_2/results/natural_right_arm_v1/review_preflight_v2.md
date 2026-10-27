# 자연 오른팔 V3 사전 검수

요약 판정: **문제없음 — source 거절을 유지하며 native 진행 후보 없음.** Critical 0 / Warning 1 / Suggestion 0. V3 변경 코드와 완료된 source 탐색 결과를 읽기 전용으로 검토했다. 새 물리 실행·학습은 하지 않았다.

- [수락 판정 코드](/home/ajou/yigyu/3/stability_adapter_2/search_natural_right_arm_v3.py:41)는 팔꿈치 하강 80mm를 필수로 검사한다. 두 후보의 실제 source 값은 34.791mm와 52.443mm로 미달한다. 전완 간격은 각각 1.714mm와 1.572mm이고 전체 source clear는 통과했지만, [최종 선택 목록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/search_v3/search.json:570)은 비어 있다. native 실행 수는 0이다. 이 결과를 자연스러운 자세·지지 성공 또는 탐색 범위 전체의 불가능성으로 확대하지 않는다.
- [기타 초기 위치 변수](/home/ajou/yigyu/3/stability_adapter_2/search_natural_right_arm_v3.py:35)는 world X ±25mm, Y 0~90mm, Z −70~20mm 범위다. 두 결과의 이동은 각각 [17.085, 88.373, −13.233]mm 및 [25.000, 90.000, −10.479]mm로 범위 안이다. 이동한 기타 상태로 전체 source audit를 수행하며, 회전과 다른 69개 초기 관절값은 유지한다. 두 결과 모두 모델 안쪽의 설계 범위를 통과하며, 두 번째 결과의 설계 경계 반올림 오차 약 2.98e−10rad는 코드의 1e−7rad 허용 범위 안이다.
- [제어 변경](/home/ajou/yigyu/3/stability_adapter_2/run_natural_right_arm_v3.py:87)은 human 전완의 초기 world 목표를 고정하고 목표 속도를 0으로 둔다. 기타의 현재 상태는 관측용이며 기타 pose setter·직접 기타 외력·부착을 추가하지 않는다. task 3000/80 및 요청 벡터 40N 상한, posture 60/8을 명시한다. 기존 right12 EFFORT 마스크·native 토크 상한·owner window·POSITION69 제출/상태 불변 검사·4개 물리 소단계·Jacobian 속도 오차 검사는 유지된다. 40N은 요청 벡터 상한이며 측정 접촉력이나 실제 8mm 관통을 뜻하지 않는다.
- 완료 결과에 기록된 입력 SHA 566개를 현재 파일과 대조했고 불일치 0개였다. source 조건은 실제 cooked collider 간격이나 native 안정성 인증이 아니다. 수락 후보가 없어 1200행의 고정 world 목표·native 접촉·사진과의 외관 대응은 실제 실행으로 확인하지 않았다.

## Warning

1. [run_natural_right_arm_v3.py:94](/home/ajou/yigyu/3/stability_adapter_2/run_natural_right_arm_v3.py:94): `safety_stopped`는 위치 20cm/회전 35° 초과를 기록하지만, 고정 world 목표와 토크 계산을 중단하지 않는다. 결과 설명에서 이를 안전 종료나 토크 차단으로 부르지 말고 **이탈 감지 래치**로 한정해야 한다.

## 검수 SHA256

- 계획 V3: `a36cfb082edbfa96f82d328a17db77d980ed0efa9c4acdb0f215ae4f2a82dd5f`
- source 탐색 V3: `0f8eb19469375f78f9f99324b36d0be729bf2388fea7622724eb0def39be85eb`
- 실행용 runner V3: `68cc9bc725d406bf92f388c682111e4f3054ec0eb32c00ce68eb774f48279332`
- source 결과 search.json: `81576bdf133d8f92dcc76ba303df1943c6963b5133dbbb08568210f330b829f8`

기존 V1/V2 리뷰·소스·실험 출력은 수정하지 않았다. 이번 검수는 이 새 리뷰 파일만 작성했다.
