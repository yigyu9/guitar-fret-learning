# 비교 범위 정정 설명

comparison_v2.json의 scope 첫 표현인 neutral evaluations는 P0·Q0에만 해당합니다. after_one_update/Q CP1은 실제 1회 갱신한 정책의 deterministic 평가이며 neutral 정책이 아닙니다. 각 row의 수치는 해당 saved controls/trace와 일치합니다. JSON과 실행 소스는 보존하며 이 설명과 최종 README에서 범위를 명확히 합니다. 단일 평가의 차이를 반복성·자연스러움·음악 성공 인증으로 해석하지 않습니다.

최대 SO(3) 회전은 trace의 기타 root quaternion을 정규화한 뒤 초기 quaternion과 비교한 각도입니다. native 관절 scalar q의 변화가 아닙니다.

팔24·왼엄지5의 ±0.15/±0.10rad 제한은 source action을 source/native 교집합에 맞춰 변환한 뒤의 nominal 목표각에 적용합니다. 원본 정책의 정규화 action 값 자체를 이 rad 범위로 제한한 것이 아닙니다. reset preload는 고정 기준이며 실제 관절 q를 매 step 덮어쓰지 않습니다.
