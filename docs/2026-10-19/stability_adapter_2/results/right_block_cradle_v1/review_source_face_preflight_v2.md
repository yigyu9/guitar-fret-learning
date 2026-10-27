# 다른 면 받침 source5 사전 검수

요약 판정: **CPU 후보 탐색은 문제없음.** 새 Critical 0건, Warning 3건, Suggestion 0건. 이전 source4 거절은 유지하며 이번 수락 여부나 native 결과는 미검증이다.

[source4 seed0 입력](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v5.py:51)이 SHA 목록에 포함되고 원본을 덮어쓰지 않는다. body9 초기 ±.3rad/right12 ±.75rad는 native 한계와 교집합이며, [R_Elbow_y bound](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v5.py:45)는 양 끝에 5°+1e−6rad 여유를 둔다. solver bound를 적용한 뒤 float32 q로 최종 전체 모델 범위를 검사한다. 아래쪽 elbow 기준은 명시적으로 79.9→59.9mm로 변경됐다.

[최종 gate](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v5.py:96)의 나머지 자연 형상·Head/왼 wrist 방향, 왼 wrist 위치, 중간 구간 내부 fraction, T/U 법선·각도, full analytic capsule 간격·전체 source LP 감사·손가락42 exact·기타 p/q 보존은 이전과 동일하다. 중간 캡슐 35~65% 및 원래 축 fraction 변환도 유지된다. 새 Python AST 검사를 통과했다.

## Warning

- [계획 V2:5](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_BLOCK_CRADLE_FACE_WRAP_SOURCE_PLAN_V2.md:5): body ±.3rad/right ±.75rad와 elbow-below 59.9mm는 초기 후보 탐색 범위 변경이다. 실행 중 body 실제각 .08rad 기준이나 실제 elbow 동작·충돌 경로 인증과 구분한다. 모델 각도 여유 5°는 정적 q 한계 여유이며 공간 충돌·지지 유지의 보장은 아니다.
- [source5:103](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v5.py:103), [현재 native helper:24](/home/ajou/yigyu/3/stability_adapter_2/right_block_effort_v6.py:24): 기존 helper의 `proximal_upper_arm30_witness` 키 불일치는 아직 이 source 변경에서 해결되지 않는다. 계획대로 native 전에 새 helper가 실제 middle witness 키/구간을 명시해 읽어야 한다. CPU 탐색의 차단점은 아니며 기존 helper 그대로의 native 실행을 허용하는 판정도 아니다.
- [source5:69](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v5.py:69): max_nfev150은 numerical Jacobian 및 별도 왼팔/Head fit까지 합친 전체 함수 호출·시간 상한이 아니다. source 법선/간격 수락은 실제 cooked 접촉이나 force closure, 연주 성공을 뜻하지 않으므로 완료 기록과 후속 native 측정을 별도로 제시한다.

## 검수 SHA-256

| 파일 | SHA-256 |
|---|---|
| search_right_block_cradle_v5.py | 2f5b4174df47f3e8ac98f51ff2943de84f07fc3c42577385c79e8e7eb54cbe20 |
| RIGHT_BLOCK_CRADLE_FACE_WRAP_SOURCE_PLAN_V2.md | db6b6484e17d35ecb9eecf2ad51137384ff9d27e1665ea7a57ec0f1dfbbe6673 |

읽기 전용 계획·source diff/수락 조건 검수에 한정한다. 추가 source 탐색·native 실행·광범위한 과거 원자료 감사는 수행하지 않았고, 소스·기존 결과·기존 리뷰를 수정하지 않았다.
