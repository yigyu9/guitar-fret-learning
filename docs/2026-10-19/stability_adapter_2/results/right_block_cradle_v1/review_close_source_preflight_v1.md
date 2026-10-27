# Thorax 초기 간격 축소 source 사전 검수

요약 판정: **실행용 source7은 문제없음 — CPU 탐색 차단 없음.** 현재 Critical 0건(발견 1건 해결), Warning 2건, Suggestion 0건.

## 해결한 Critical

[source6:81](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v6.py:81)는 R_Hip/Chest analytic 간격을 계산하지만 최종 양수 gate를 검사하지 않아 계획과 불일치했다. 전체 mesh LP 감사는 analytic capsule 검사와 동일하지 않다. v6은 다른 native 시도의 입력 SHA에 포함된 원본을 보존하고 **이 source 탐색으로는 실행하지 않는다**. 새 [source7:81](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v7.py:81)이 5개 caps 모두≥0.00005m를 요구하며, [계획 V2](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_BLOCK_CRADLE_CLOSE_SOURCE_PLAN_V2.md:15)와 `search_v7` 출력 경로로 분리한 것을 확인했다.

## 확인한 범위

CFG는 static_Thorax40, BASE는 해당 native 초기 자료다. 순수 CPU `EnvironmentContract` 검사에서 BASE joint 이름과 전체 초기81q가 contract q_ref와 exact였다. body9 ±.1rad/right12 ±.15rad∩모델 한계 및 R_Elbow_y 양쪽5°+1e−6rad 여유를 적용한다. Thorax0.3mm·근위0~30% Shoulder2mm 목표, 전완12mm·자연 형상·Head/왼 wrist 방향·frozen42·모델 범위·최종 LP gate가 유지된다.

기타 p/q는 seed 원본 배열을 보존하고 genuine FK predicted poses를 저장한다. 후보에 실제 `proximal_upper_arm30_witness`와 legacy65 호환 키가 모두 있으므로 기존 runv9/helper의 키 계약과 맞는다. source4/5 경로·범위·반대면 설정은 남아 있지 않으며, 새 후보 config는 정지 amplitude0과 기존 Thorax40/16mm·Shoulder10/4mm 제어 설정을 상속한다. source6/7 AST 검사를 통과했다. source 입력 SHA before/after 검사와 배타적 새 출력 경로를 유지한다.

## Warning

- [source7:50](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v7.py:50), [같은 파일:81](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v7.py:81): Thorax0.3mm는 최적화 목표이며 최종 수락 범위는 0.05~6mm이다. 수락만으로 실제 0.3mm 배치가 됐다고 말하지 말고 측정값을 제시한다. source 간격은 cooked 접촉·관통깊이·접촉력·반대면 집게 인증이 아니다.
- [source7:83](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v7.py:83): 손가락42/G는 exact 보존이지만 왼 wrist 위치는 재맞춤 후 <15mm 허용이며 Head/왼 wrist 방향도 ≤1° 허용이다. 몸통/오른팔 초기각 및 보상 각도를 바꾸는 비교이므로 초기 간격 하나의 효과나 모든 인간 부위의 world pose exact 보존으로 확대하지 않는다.

## 검수 SHA-256

| 파일 | SHA-256 |
|---|---|
| search_right_block_cradle_v6.py — 미실행 보존 | ba3036290f852e3d7fec27d24b961c091d594e46999058ea8edb3e0febb590a3 |
| RIGHT_BLOCK_CRADLE_CLOSE_SOURCE_PLAN_V1.md | 7f04049fb80542d0b93e6931e03218cc6e11cedaeb63b5a3cafa00a6362d544a |
| search_right_block_cradle_v7.py — 실행용 | 652a8bcd4c489a1778d8fbfa6bd88643878c5d58c8bb0ed186841302776e11ea |
| RIGHT_BLOCK_CRADLE_CLOSE_SOURCE_PLAN_V2.md | 6e38034d2931868b2e901bf32eccf376ceb39577c554dc61015b37ac03c3d781 |

이 기록은 새 source 코드·계획·입력 기준 및 native helper 연결 계약의 읽기 전용 검수다. 새로운 source 탐색·물리 실행·기존 원자료 전체 감사는 하지 않았으며 다른 소스·결과·기존 리뷰는 수정하지 않았다.
