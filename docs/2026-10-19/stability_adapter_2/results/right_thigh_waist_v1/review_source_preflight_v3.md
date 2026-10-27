# waist flank source3 발견 기록

판정: **source3/helper1은 수정 필요. 미실행 원본으로 보존.** Critical 1건, Warning 1건, Suggestion 0건.

## Critical

[left_arm_clearance_source_v1.py:21](/home/ajou/yigyu/3/stability_adapter_2/left_arm_clearance_source_v1.py:21)의 `p+r.apply(centre+corners)*size`는 geom centre와 world로 회전한 좌표에 half-size를 곱한다. 올바른 XML box 정점은 `p+r.apply(centre+corners*size)`다. 실제 Pelvis geom centre[−.0031,.0168,−.0215]m·half-size[.1079,.084,.0846]m와 현재 native pose로 대조하면 정점 최대25.135809mm 오류가 있다. 잘못된 Pelvis box가 왼 forearm clearance 선호에 들어가므로 수정해야 한다.

source3은 실행하지 않았고 helper1은 독립 segment QA로 소비된 원본을 보존했다. 새 helper2/source4에서 교정한다. 최종 whole LP는 별도로 유지되므로 이 오류가 반드시 잘못된 후보 수락으로 이어진다는 뜻은 아니다. 원본 실패를 숨기거나 source3을 실행하지 않는다.

## Warning

[source3:29](/home/ajou/yigyu/3/stability_adapter_2/search_right_thigh_waist_v3.py:29): waist 반폭 최소+15mm flank 구간은 기존+5mm core보다 넓어진 수락 정의다. core는 별도 참고로 남기고 실제 native 접촉이 어느 구간인지 분리한다. analytic 왼팔 간격3mm는 최적화 선호이며 whole LP·모델·6caps·손목 정확도 최종 gate를 대신하지 않는다.

검수 SHA-256: helper1 `fb53331228a7589c17b331bb640677d9d91e53aa61db0edd0ca55f0f3146c85b`, source3 `c7692bf7c928237551db704579674114acd1edc3820899997f55abb19f7ab8a1`.

코드·기존 native 기준의 순수 좌표 산술 검수다. 새 fitting/native·정책 추론/학습·원본 수정은 하지 않았다.
