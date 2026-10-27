# 스트랩 길이 고정·관절만 변경하는 초기 안정화 비교

사용자 요청에 따라 strap rest length를 탐색변수에서 제외한다. 이번 고정값은 최근
original/−2/−4mm 비교의 original인1.1018469719600776m다. 스트랩 제거/장력0 강제는
아니며, 관절 변화로 route길이·수동장력이 바뀌는 것은 실제 물리 결과로 측정한다.

## 이번 작은 단위

1. 기존 small_wrist_motion_v1 actual5초를 길이고정 기준으로 보존한다.
2. 기존 coupled_palm_witness_v1의 초기팔12+hinge6 및 대응PD목표를 사용하되,
   LA만 위 original로 복원한 새 trial/proposal을 만든다. 기준과 비교해 바뀌는 것은
   초기18각과 대응목표이며, 기존left33offset·나머지63각/목표·PD/gain·G 초기p/q·
   root/하체 고정·body9PD×2·손목±.005rad/1Hz 파형은 같다.
   최대 초기각 변화는.002616494894rad다. 작은 국소후보 한 개로 모든 관절탐색의
   가능/불가능을 결론내리지 않는다. Sourceprofile6관절 호환 시험은 이 요청 뒤로 보류한다.
3. 기존 frozen run_palm_witness_initial_diagnostic를 수정 없이 재사용한다.
   Fresh native14검사/전체비인접self source·실제81각/FK·PD·길이를 확인하고,
   gate 통과 시 한 초기화/1200step/실제0~5초 전신·손151frame strap영상을 저장한다.
   initial gate 실패는partial로 보존한다. 추가 source 최적화/actor/학습은 이번에 하지 않는다.
4. 동일LA/물리/clock을 원자료에서 확인하고 최대초기이탈·종료오차·2초기준2~5초변화,
   실제손목응답·body9변화·장력·접촉을 비교한다. Rawλ를 N이나 지속palm지지로 해석하지 않는다.
   초기G복원과 후기유지를 분리하고 작은 후보의 개선 없음을 관절만 안정화 불가능으로 확대하지 않는다.

## 산출물과 검증

새 입력/소스는 stability_adapter_2에, 로그·이미지·영상을
/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_only_fixed_strap_v1에 둔다.
기존 자산/계획/실행묶음은 수정하지 않는다. source/checks/inputSHA를 실행 전에 보존하고
입출력 전후SHA, 실제영상/PNG, 독립검수,이전phase보존을 확인한다.
새 이미지 설명은 누적 VISUAL_REPORT에 추가한다. 최종66권한과 연주공동residual 설계는 유지한다.

- [ ] 고정LA 새입력/기존실행SHA·코드검수.
- [ ] Fresh native gate/한actual5초/초기값·두영상.
- [ ] 같은LA 관절18차이 비교·그림설명·검수·보존.
