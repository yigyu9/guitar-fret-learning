# 거리 solver 상태와 root 감사 보완

16배치 중 step120의 비율0/0.25 및 step1200의 비율0/0.25에서 SLSQP가 `Positive directional derivative for linesearch`로 success=False를 반환했다. 원자료의 네 실패 flag를 그대로 보존한다.

기존 source_patch_interval은 solver 성공 여부와 별도로 hull 내부점으로 witness를 조정하고 polygon weight를 정규화한 후 feasible 상한과 support-plane 하한을 계산한다. 이 네 경우 feasibility_error_mm=0이며 상하한 차이의 최대값은5.798403876156044e-9m다. 따라서 보고서의 거리 ‘상한/구간’ 표시는 유지하되 solver가 모두 성공했다거나 exact optimum이라고 설명하지 않는다.

Root 감사 v1은 success flag를 무조건 요구하는 잘못된 가정을 추가해 이 검사에서 중단했다. 실행 소스·실패 원인·관측을 root_audit_failure_v1에 보존하고, v2에서는 feasible witness와 실제 world 두점 거리, 하한/상한 관계를 검증하며 네 solver flag를 별도 확인한다. 분석 결과·producer·그림·native 입력을 수정하거나 재실행하지 않았다.
