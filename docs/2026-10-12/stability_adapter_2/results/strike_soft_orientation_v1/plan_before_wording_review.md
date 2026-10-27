# 기타 기준 위치 보정에 손 방향을 부드럽게 유지

actual-angle PI의 EFFORT와 POSITION은 모두5초 기타약45°로 미채택이다. POSITIONgeometry에서는타현0/miss10/PLAY범위45of251이다. 따라서 비교 기준은 이전 안정성이 가장 나았던 POSITION timed-wait-rebase (타현1/회복1/최대7.095°/PLAY범위164of178)로 되돌린다. 기존 policy+PI base/대기actualIK/RECOVER이전목표+2δ/nativePOSITION phase1kdquarter/learned손가락21을 유지한다.

새 요인은 PLAY IK residual에 현재 기타 기준 RHpick 방향 선호 항 하나를 추가하는 것이다. PREPARE가 이미 쓰는 candidate soft_reference_pick_rotation_G를 공유한다. 실제pick회전을 anchor로, current Chest 변화×calibratedFK 회전변화×inverseChest 변화로 회전예측한다. 위치1000m→mm residual에 방향5mm/rad soft residual을 더한다. exact정렬/손부착/접촉강제는 없다. 모든 source phase0/1/2가 같은 선호 방향을 쓰되 위치·관절규제·기존±.15/±.3와rate한계가 우선 협상한다. Finger21/왼팔/기타힘은 변경하지 않는다.

근거: EFFORTgeometry1.2s RHring3–Gbody positivecontact/pick 방향handoff대비13.44° 뒤2s G31.67°/손방향45.37°가 관측됐다. 이전 POSITION도접촉이있지만G7.095°에머물러 접촉만으로원인을확정하지않는다. 방향constraint효과를같은base에비교한다.

- [ ] AST3.8·회전anchor 수학검사·독립사전검수
- [ ] 동일초기·PREPARE49controls/25native states·첫actorobsaction exact
- [ ] 5초1200steps151frames·입력불변·force/state쓰기금지
- [ ] 타현/회복/후속타현·기타범위·손회전/접촉 비교
- [ ] 결과/이미지영상/독립검수/보존봉인

결과: /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_soft_orientation_v1/
