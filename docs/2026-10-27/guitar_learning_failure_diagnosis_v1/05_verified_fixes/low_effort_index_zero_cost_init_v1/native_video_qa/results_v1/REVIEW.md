# B300 실제 영상 독립 검수

판정: **문제없음 / PASS**. Critical·Warning·Suggestion 없음.

원source_review의3개SHA가현재일치하고27직접/1271검증입력SHA도일치했다. 실제best/latest가모두300이므로한모델·손/전신두영상을선택한것을확인했다. 원128환경/native105·private16cap/90쌍/Bdescriptor·평가fresh=False/원strictcheckpoint·정책/입력불변/loader·alias복원/장면닫기근거를독립대조했다.

각MP4의ffprobe를저장검증JSON과대조했고h264/1280×720/30fps/110frame,합220frame전체CPUdecode를통과했다. 각영상0/36/92/109프레임을메모리로재추출해총8PNG의RGB픽셀이exact임을확인했다. 두contactsheet와손/전신음중원해상도프레임을직접보았다. 화면은upright이며머리와양발이전신프레임안에있다. 파란검지의큰끝마디굴곡과일부손가락/넥가림은남아있다. 이는자연스러움·해부학·압력·음향인증이아니다.

221원래고정평가끝점과q/target/body_state/명령/candidate·wrong/손목기록9종이exact였다. 몸체합력의최대차이는1.1444091796875e-5N으로보존되어있으며완전동일로표시하지않는다. raw는physics4..884를4간격으로저장하고영상은8..880을8간격으로인코딩한다. 프레임n은control2×(n+1),첫프레임1/30초이며마지막control221은raw만있다.

영상env0은달성/clean1/wrong0이고원전체고정평가128/128과구분한다. 다른127상세힘·접촉쌍·motor torque·240Hz최대·자유기타/전곡/자연성을영상으로확정하지않는다. 최종16검토파일SHA는review.json.reviewed_sha256에있다. 기존영상/source/원자료/결과수정과GPU/native실행은없고새review2파일만작성했다.
