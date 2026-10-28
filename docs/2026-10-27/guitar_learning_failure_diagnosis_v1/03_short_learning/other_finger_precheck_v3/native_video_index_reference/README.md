# 검지 기준 동작의 실제 영상

학습 전 initial.pt의 scripted reference 동작이다. 원래4환경 배치의 env0 첫시도를 촬영했으며 압현은 미달이다. 학습된 정책 성과가 아니다.

- [손 확대](hand.mp4) · [전신](fullbody.mp4)
- 1280×720·30fps·각110프레임(3.6667초), 실제221 control/884 physics step. 몸체 각도/카메라 방향을 확인했으며 전신은 머리와 발이 보인다.
- 현재674입력 SHA·strict load·모델 불변·native 장면 종료·인코더 종료0을 확인했다. 실제 outer 종료0,34.87995초다.
- 기존 index_reference와 실제 q/target/body pose·명령·candidate/wrong·패드거리·손목요청 등11배열이 정확히 같다. 왼손 전체 force도 정확하다. time 표현차 최대4.44e-16초, 전체힘 중 기타 body 한 float만1ULP(3.815e-6N) 차이가 있어 전 배열 bit-identical이라고 보고하지 않는다. [검증](qa/verification.json)을 따른다.
- 이 영상은 현재3초 준비 조건의 도달 실패를 보여준다. 힘은 body resultant이며 물리 접촉쌍 압력 인증이 아니다.
