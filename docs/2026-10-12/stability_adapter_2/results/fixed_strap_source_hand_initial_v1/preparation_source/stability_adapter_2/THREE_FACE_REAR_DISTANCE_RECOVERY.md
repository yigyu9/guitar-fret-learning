# 후면 source 거리 계산의 수치 중단 복구

첫source검색은5.311616초/exit1/native0였다. 첫후보의실제source거절자료는partial_selection.json에남겼고둘째QP는Positive directional derivative for linesearch로중단했다. 원소스/실행/로그/부분자료를expectedSHA대조후새v2phase에exact보존했다.

후속 search_rear_thumb_facet_v2.py는같은anchor/bounds/목표/G/LA/gain/source검사와네후보계약을유지한다. 기존소비source는수정하지않는다. QP의successflag와유효거리구간은구별한다.

- 반환hull점은 convex vertex 평균으로 향해필요한만큼만이동해plane내부1e-8mm를확보한다. polygon의nonnegativeweights는sum1로정규화한다. 조정량과원/조정후feasibility를기록한다.
- 유효한두점거리상한과supportplane하한을그대로기록한다. QP미수렴때도실제거리는이구간안에있으며gate는하한≥.3mm/상한≤1mm일때만통과한다. 구간이경계를가로지르면거절한다. 미수렴을최적해로표현하지않는다.
- 같은네source후보를새경로에서다시검사하고첫부분후보와반복값을대조한다. Source반복과새native/physics0을분리한다. 유효후보가있으면당초최대2회5초계약을따른다.
