# 접지 후보 source V2 메타데이터·BOX 감사 보완

2026-10-16. source V1 fit과결과는불변보존한다. V1은MUJOCO_GL=egl import오류1회(물리실행0), MUJOCO_GL=disable에서source생성1회성공했다. V1의6기하gate true이나, 상속된expected chair z가이전높이이고 lower24_q_rad는복원기준이었다. 실제human/G/q/IK는그대로두고source V2에서실제chairpose/lower24메타를정정하며이전reference를historical키로명시한다. cube half/actualcenter/condition은V1에서이미새높이로갱신됐다.

기존analyticcapsule감사의범위에4개footBOX검사를추가한다. 실제collisionmask/parent/contactexclude를따라 human capsule/BOX와의새교차, chairBOX와의completeSAT, G:bodyconvexpieceSAT를원source4대비확인한다. handmesh/기타작은marker형상전체의인증은아니며native안전/접촉검증이필요하다. V2candidate는human/G예측과q가V1과exact여야한다. run V1(미실행)은source eligible·sourceinputsunchanged 검사를추가해실패source의native진입을막는다. 형상통과를실제발접지성공으로부르지않는다.
