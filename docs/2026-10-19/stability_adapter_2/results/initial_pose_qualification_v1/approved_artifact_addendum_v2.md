# 관절 측정 주기 보충

원래analysis_*와qualification_summary_v1.json은 보존한다. 그 안의 actual joint maximum 속도/한계 초과는60Hz81관절각·속도표본 기준이다. 전체240Hz 실제 최대라고 쓰지 않는다.

joint_240hz_audit_v1.json은초기/매prestep/최종post까지active33(body9+양팔24)위치와81속도를240Hz로재계산했다. 나머지48관절의240Hz위치최대는기록범위밖이다. active33위치한계초과:baseline.0200193°,static.00160168°,strike.00780008°,leftcycle.22019847°(L_Wrist_y5.541667초),Z+3mm.00277135°.81속도최대는각각.499782/.375186/3.203110/2.556389/.399174rad/s다. 모두50rad/s미만이며목표변화율rad/s와실제속도를구분한다.

root권장결과는README_v2.md다. 산출물은기존소유artifacts_v1/과video/initial_pose_qualification_v1/안에새producer/문서버전으로만쓴다. 아직완료문서를생성하지않았다면README.md↔영상README.md를권장쌍으로만들어도된다. 원자료·이전producer·brief·before·성공출력은수정하지않는다.
