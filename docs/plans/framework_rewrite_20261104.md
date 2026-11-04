# Framework Overview / Model / Method 재작성

요청: `guitar_learning` 구현과 `paper/framework/정리.txt`의 설계를 바탕으로 상세 framework 작성. `paper/framework/` 안의 기존 Markdown 7개를 제거하고 새 문서 작성. TXT 3개는 바이트 단위 보존한다. 다른 paper 원고, 학습 소스, 실행, 데이터 및 GPU에는 변경하지 않는다.

구성: README, 01_overview, 02_model, 03_method, evidence_index, images/README. 기존 그림과 JSON은 보존하며 과거 자료로 식별한다. 현재 코드 근거는 별도 snapshot으로 기록한다. 폐기된 04_open_questions의 역할은 Method의 구현·검증 과제로 통합한다.

- [x] TXT·기존 자료 보존 SHA 확보, 범위 내 기존 Markdown 제거
- [x] 현행 압현 v5 / 타현 compact / 공통 물리·PPO / 전신 설계와 구현 경계 확인
- [x] Overview: 문제·전체 흐름·3정책 역할·구현 범위 작성
- [x] Model: 물리·관측·목표·행동·신경망 차원과 수식 작성
- [x] Method: 입력·제어·보상·학습·평가·미구현 통합 설계 작성
- [x] 근거 링크·수치·TXT 보존·독립 검수 및 최종 일관성 확인

성공 기준: TXT 원문 불변, 현행 코드 경로별 입력·출력·신경망·학습·보상이 대응, 3정책 동시 실행/전신 자유균형 미구현을 구현완료와 혼동하지 않음, P7/P9 등 목표 유지·해제 의미 및 물리/음향 평가 범위 구분, 링크 유효. 코드 기반 설명이며 새 실험 성과를 주장하지 않는다.

완료: 기존 Markdown 7개 제거 후 6개 재작성(이전 open_questions 내용은 Method의 후속 설계 역할로 통합). Overview·Model·Method 상세 본문, 근거30항목, 과거 그림 안내, 현행 소스 snapshot 작성. 참조코드37파일, 링크174개, 차원 합10건, Markdown 표·수식/코드 경계 점검. TXT3개와 기존 non-Markdown 총12파일 SHA동일, 감사중 활성코드103파일변경없음. change-reviewer의 타현 보상 조건·척도 및 손별 초기 자세 지적을 반영하고 최종 문제없음 판정을 받았다. 학습 코드·데이터·GPU·실행 상태는 변경하지 않았다.
