# V6 실제 native 영상 독립 검수

요약 판정: **문제없음 / PASS**. Critical·Warning·Suggestion 지적 없음.

실제 rl38 Python3.8.20 CPU 읽기로 runtime 입력570개 SHA·전후핀 동등성을 확인했다. 완료/종료·scene close·alias 복원·cleanup 오류없음, NN-only·교사호출0·fit/PPO0, 지정 last300 checkpoint SHA와 모델/optimizer/checkpoint 동결을 재검사했다.

source 고정평가와 원128환경 각1시도 전체 episode 원장 및9보상이 정확히 일치한다. q·target·body_state·candidate·raw NN goal·decoded goal 배열도 정확일치한다. native capture354행의 q/target/body_state가 replay와 정확히 같다. body force의 최대차이는7.62939453125e-6 N이며 제어값 동일성 주장과 별도로 보고한다. 이는 현별 압력·접촉쌍·음향의 증명이 아니다.

hand/fullbody 각각 ffprobe로1280×720·30fps·177프레임·5.9초를 확인하고177프레임 전체 CPU decode를 통과했다. 양쪽0/30/60/90/105/120/150/176번 실제 프레임을 독립 시각 검사했다. 전신은 똑바로 서 있고 인물·기타·바닥이 보이며 수평이 안정적이다. 손 영상은 native 손가락과 기타 neck이 보이고 동작이 관측된다. 표본프레임에 검은 화면·잘못된 회전은 없다. 카메라 고정 위치(-.10,3.4,1.1), 시선(-.15,-.10,.65) 소스도 확인했다. 모든 프레임을 육안으로 본 것은 아니다.

이 검수는 고정기타·검지4축·3음의 env0 첫시도 마지막300 모델 영상 재현성 검수다. 음악적 성공을 뜻하지 않으며 마지막 평가의 A 오압/달성실패 결론은 유지한다. 추가 GPU·NN·학습 실행0회. 기존 봉인·분석·준비 검수는 수정하지 않았다.
