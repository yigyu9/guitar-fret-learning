# Rear source 거리 복구 실행 전 독립 검수

검수일: 2026-10-08. **요약 판정: 문제없음.** 최종 미소비 복구 source에 Critical/Warning/Suggestion은 없다. 거리 helper의 수치 검증과 실제 후보 검색·지지 인증은 구별한다.

검수한 [search_rear_thumb_facet_v2.py](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet_v2.py:1)의 SHA256은 `0120843f1a07d51f65f35fe0666652dbcbf319b6408260719a22b24badc2be33`이다. [복구 계획](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_REAR_DISTANCE_RECOVERY.md:1)의 SHA256은 `759cc1a5682279752f33af0fa009e4ec617c90919475aae7bbcfb55c85f3089c`다.

## Critical

없음.

## Warning

없음. 현재 수정이 거리 구간 gate를 완화하거나 미수렴 값을 최적해로 인증하는 경로는 확인하지 않았다.

## Suggestion

없음. [잔차 기록:238](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet_v2.py:238)은 원/조정 후 hull plane 잔차(mm)와 polygon weight 합 오차(무차원)를 각각 기록하며 두 허용치도 각각 검사한다. 최종 source의 synthetic 검사에서 두 단위의 분리를 확인했다.

## 확인 결과

- [원 실패 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v1/search_execution.json), [원 실패 부분 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v1/partial_selection.json) — 5.311616초/exit1/native0, 첫 후보 거절1개·통과0개를 확인했다. 원 log에는 둘째 거리 QP의 `Positive directional derivative for linesearch` 중단이 남아 있다. 원 search source와 실행 원문 복사본의 SHA가 실행 전후 `3f26ff1fa49ed1a3e7c4ee666043a735e7b0160f8230807172d9913cc4443dc1`과 exact 같고 log SHA 및 wrapper의 입력 전후 mapping도 일치한다. 원 phase의 정상 proposal은 없다. 첫 부분 결과를 정상 네 후보 완료로 바꾸지 않았다.
- [실패 보존 mapping](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_rear_facet_v2/source_failure_v1_snapshot/preservation.json) — 12개 전부 original/snapshot/기록 SHA를 읽기 전용으로 대조해 불일치0을 확인했다. 원 source·wrapper·실행 기록·log·attempt·facet·sensitivity·부분 결과·기존 검수/복사본을 보존했다. 기존 소비 source는 수정하지 않았다.
- [새 경로:11](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet_v2.py:11), [봉인:33](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet_v2.py:33) — 새 result/trial 경로를 사용하며 attempt/proposal·trial 경로 재소비 보호가 유지된다. 직전 검수된 source 입력 mapping을 이어받고 직접 읽는 직전 proposal·복구 계획·새 producer·실패 보존 mapping·기존 exact producer 보존 기록을 입력 SHA에 넣는다. 검수 종료 시 새 attempt/proposal 및 trial 디렉터리는 없었다. 이번 보존 대조와 앞으로 실행 wrapper의 검수 기록 SHA binding은 별도 단계다.
- [변경 diff](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet_v2.py:218) — 기존 source와 비교한 변경은 새 phase/trial 경로·보존/복구 입력 목록·거리 witness 복구다. 모든 nested function의 AST를 대조해 `certified_distance`만 달라졌음을 확인했다. 기존 facet 선택·17각 bounds·두 초기 후보/실패 시 두 확장 후보 흐름·목표·front-finger soft preference·전체 source 교차·대표점 여유·rear witness·81 target compose 및 LA/gain/trial schema 계약은 그대로다.
- [witness 조정:235](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet_v2.py:235) — 반환값의 finite 여부와 nonnegative polygon weights/양수 합을 먼저 확인한다. Full-dimensional source convex hull의 vertex 평균을 내부점으로 사용해 활성 plane의 `−1e-8mm` 경계까지 필요한 비율만큼 축소한다. Nonnegative polygon weights를 합1로 정규화해 finite patch 내부 witness를 만든다. 조정 후 feasibility를 확인하고 실패하면 중단한다. Convex 조합에 의한 hull 내부 이동과 patch witness의 유효성이 거리 상한의 근거이며 solver success 자체는 근거로 쓰지 않는다.
- [거리 구간:255](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet_v2.py:255), [gate:369](/home/ajou/yigyu/3/stability_adapter_2/search_rear_thumb_facet_v2.py:369) — 유효 witness 사이의 거리는 실제 최소거리의 상한이다. 그 차의 unit 방향에 대해 `min(hull vertices·direction)−max(patch vertices·direction)`은 convex set 사이 거리의 하한이고 음수는0으로 둔다. 따라서 solver 미수렴이어도 실제 거리는 구간에 포함되며 하한≥0.3mm/상한≤1mm일 때만 기존0.1µm tolerance로 gate를 통과한다. 넓은 구간이 경계를 가로지르면 보수적으로 거절한다. 성공 bool·message·raw/조정 후 plane feasibility·weight 합 잔차·hull witness 이동량·primal–dual gap을 기록한다.

## 독립 synthetic 검사

새 source의 거리 함수만 AST로 분리해 메모리에서 실행했다. Main·실제 source 후보 검색·native scene·물리 step은 호출하지 않았다.

- 알려진 box–finite quad 거리0/0.25/0.30/0.70/1.00/1.10mm를 world offset과 함께 검사하고 동일한 여섯 형상을 회전하여 총12개를 대조했다. 모든 실제 거리가 구간에 수치 오차 범위 내 포함됐고 최대 상한 오차는 `1.000003389556997e-11m`, 최대 내부 이동량은 `1.000000380652938e-8mm`였다. `feasibility_error_mm≤1e-10`과 `weight_sum_error≤1e-10`을 각각 확인했다.
- 실제 SLSQP witness에 hull 바깥1µm 오차와 polygon weight 합1.2를 주고 `success=False`, status8 message를 강제 반환했다. 원 plane 잔차 `0.0009999999999988907mm`와 weight 합 오차 `0.19999999999999996`를 각각 기록했다. 조정 후 두 잔차0, 이동량 `0.0010000099999988854mm`, 하한/상한 `0.7000000000000298…0.7000000100000339mm`로 실제0.7mm를 포함했다. 미수렴 bool/message가 그대로 남았으며 최적해라고 바꾸지 않았다.
- status9를 강제한 coarse 내부 witness는 구간 `0…1.4422205101856248mm`가 나와 실제0.7mm를 포함하지만 gate는 거절했다. 음수 polygon weight는 `invalid source patch witness`로 거절했다.
- UTF-8 decode와 Python3.8 `compile` 검사를 통과했다. 검수 뒤 source SHA가 위 SHA와 같은 것을 확인했다.

## 완료 범위와 남은 실제 확인

코드·경로·원 실패 보존·거리 helper의 사전 복구 검수를 완료했다. 새 실행의 첫 부분 후보 반복값·실제 네 후보의 solver 상태/조정량/거리구간·전후 입력 SHA 및 모든 거절/통과 이유는 실행 자료에서 별도로 확인해야 한다. Source통과 후보가 있으면 fresh native admission 및 당초 최대2회5초 자료를 따로 검수한다. 이번 결과는 실제 source 후보의 후면 지지, cooked clearance, 지속 지지·안정성 또는 연주 성공의 인증이 아니다.

본 담당자가 이번 복구 단계에서 생성한 파일은 이 검수 기록 하나뿐이다. 원 실패 파일·기존 source/review·다른 담당자의 파일을 수정하지 않았다.
