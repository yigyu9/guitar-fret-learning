# 학습150·300 실제 영상 독립 검수

판정: **문제없음 / PASS**. 남은 Critical·Warning·Suggestion 없음.

42개 직접 입력 및1126개 검증 입력의 SHA가 현재 일치했다. 실제150·300 render child 종료0와 두128환경 장면의 원strictload/모델·checkpoint·입력 불변/105native·private16effort/90쌍/loader·alias복원/닫기 기록을 대조했다.

4개 MP4 각각 ffprobe 결과를 원기록과 독립 대조했고 h264/1280×720/30fps/110프레임을 확인했다. 총440프레임을 CPU에서 전체 디코딩했다. 각4프레임을 원영상에서 메모리로 다시 추출하여 저장된16PNG와 RGB픽셀 exact를 확인했다. 손·전신 contact sheet와150손/300전신 음중 원해상도 프레임을 직접 보았다. 화면이 upright이고 전신 머리와 양발이 화면 안에 있으며 파란 검지의 큰 마지막 관절 굴곡과 손 영상의 일부 넥 가림이 보인다. 이 관찰은 해부학·자연스러움·현압력 인증이 아니다.

각221원래 고정평가 끝점과 q/target/body_state/명령/candidate·wrong/손목 기록9종이 exact였다. 합력 최대차이는150모델3.814697265625e-6N,300모델7.62939453125e-6N으로 비동일성이 보존되어 있다. README의150 표기반올림 한 곳을 root가3.81e-6N으로 정정한 최종본을 확인했다.

영상 프레임 n은 control끝점2×(n+1), 첫프레임1/30초이며 마지막control221은 raw만 있고 영상은220까지다. 원150평가128/128과최종300평가76/128을 원학습분석과 대조했다. 영상env0두시도 성공을 전체128의 성공으로 확대하지 않는다. 몸체 합력은 pair압력·torque·240Hz최대가 아니며 음향도 인증하지 않는다.

최종22파일 SHA는review.json.reviewed_sha256에 있다. 기존 QA·영상·원자료·source·준비 변경 및GPU/native 실행은 없으며 허용된 review.json/REVIEW.md만 새로 작성했다.
