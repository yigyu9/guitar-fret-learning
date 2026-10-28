# fresh300 실제 분석 독립 검수

판정: **문제없음 / PASS**. Critical·Warning·Suggestion 없음.

고정7평가896첫시도 전체를 원원장·9보상·음시계와 대조했다. 달성은0/128/128/128/0/0/76이며 모든 물리·손목실패는0이다. 원사전 순위는best150/latest300, 학습후인접통과쌍은50–100 및100–150으로 재현되었다. 초기0은 연속쌍에서 제외되었다. 최종300 clean0.5933921756/wrong0.4065122517의 후퇴가 보고서와 그래프에 명시되어 있다.

300metrics×4096=1,228,800 전이, 글로벌9600control/38400physics와5504종료episode(1,216,384steps)/미종료12,416steps를 독립 집계했다. 모든 종료는timeline_complete이고 실제 실패비용은0이다. 반면costGAE와value loss는각300회nonzero이며 이를 새 실패로 세지 않았다. 원9보상 합산 최대잔차는학습평균2.92240e-9, 학습종료episode1.03950e-6, 평가episode1.00211e-6이다.

1234직접/1136검증입력의 현재 SHA 일치,8scene128환경·105readback/90pairs·원설정/계약·닫기·입력/alias복원 assertion을 확인했다. actualinitial73tensor의 동일seed7 기본초기화 및7checkpoint identity/source 대조도 원분석을 CPU 메모리 재생하여 통과했다. 원checkpoint strict native 평가와 CPU identity 대조를 구분하며 CUDA RNG를 우회해 load/resume하지 않았다.

출력 쓰기를 메모리에 가로채 JSON2개·CSV4개·RESULTS를 재생해 동일함을 확인했다. env0 1547끝점의 helper기하 재생과 별도 NumPy actual/target각·기타pose 기반 손목·세마디 합력/원후보·오압현 집계를 대조했다. 두 그래프를 직접 확인했다. best150의 PIP actual17.70785°/target90.00019° 및 distalmean6.50917N 등 남은 추종차이를 성과로 덮지 않았다.

검토한11파일 최종 SHA는review.json.reviewed_sha256에 있다. 후퇴 메커니즘·다른127환경 상세힘·자연스러움·쌍압력·다른seed/자유기타 성과는 이 검수로 확정하지 않는다. 기존source/preparation/precheck/raw/results 변경·GPU/native 실행은 없으며 새 review2파일만 작성했다.
