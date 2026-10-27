# 기타 좌우·수평 교정 결과 체크리스트


- [x] 기존인계/하체좌표진단/직립phase를읽고원code·입력·결과를보존했다.
- [x] source몸통좌우+150.035mm복원/넥0도/몸통·머리·하체조건별보존을검사했다.
- [x] source2왼팔교차실패를발견하고source3왼팔/source4허벅지6축교정후전체baseline상대형상검사를실행했다.
- [x] 실제6개5초실험과전1201표본배치/접촉/안전/입력보존판정을기록했다. 전체성공0회다.
- [x] 계산IK오차·finite목표·실제손추종의차이및초기righttarget0.049969rad변화를진단했다. initial materialpoint기준으로초기차이가2.38e−7rad로줄었으나전체안정화는실패다.
- [x] 이전과최신V6의실제동일카메라종료비교/전체5초영상/실패를기록했다.
- [ ] 모든5초표본에서넥3도/좌우20mm/몸통5도·옆3도/1초후가슴위팔동시95%를만족한다. V6neck5.269도/Chest5.003207623도/가슴0으로미완료。
- [ ] 같은교정배치에서왼손15초해제검증. 이번phase에서는시작하지않았다.
- [ ] 새PPO학습. 앞선검증전에는시작하지않는다.

현재남은문제는초기free기타흔들림,실제손/몸통의finite추종,Spine접촉과Chest간격이다. gain증가나기타왼이동/넥상향으로문제를우회하지않는다. [상세결과](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_horizontal_v1/README.md)와 [실제영상](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_horizontal_v1/media_index.md)을함께참조한다. 독립검수는각review_*.md,root최종보존감사는 [final_verification.json](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/upright_horizontal_v1/final_verification.json)에분리했다.
