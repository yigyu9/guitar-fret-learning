# 엄지2 scalar 비교의 identity 검사 정정과 재실행

source_hand_thumb2_clearance_v1의 첫source실행은other_pose_identity assert에서중단됐다. 직접sourceXML을확인하니LH:thumb2의자식에는LH:thumb3·LH:thumb_top뿐아니라충돌형상에서제외된LH:thumb_pad body도있었다. Thumb2를바꾸면이자식pose도따라야한다. 원소스/로그/exit1/전후입력SHA를보존하고native는시도하지않았다. 7조건의물리적해소불가로해석하지않는다.

새search_thumb2_clearance_v2와wrapper는sourceXML의thumb2 body하위모든body를moving_names로유도한다. 실제movingcollisiongeom은thumb2와thumb3둘이라는assert는그대로유지한다. Thumb_top/pad는pose만scalar체인을따르고다른bodyposeidentity를검사한다. 나머지7각도/float32양자화/source HG·cross/self1188/palmup/후면패치거리/최소변경선택·LA/기타초기p·q/PD/최종66권한과기존SOURCE_HAND_THUMB2_CLEARANCE_PLAN.md의목표는그대로다.

- [ ] 정정소스/사전입력보존 및 7조건 재계산
- [ ] Clear한후보1개의fresh native직접gate/통과시같은초기화5초,또는7조건모두실패근거
- [ ] 결과·이전실패구분·이미지/영상·독립검수와보존

새결과는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v2 에저장한다. v1은수정/덮어쓰기하지않으며소비된wrongscope의top meshes문구도원문으로보존한다. v2에서는collisiongeom2와따라가는posebody를구별한다. Actor/학습/추가물리제어변경은없다.
