# 엄지 후면 안내면 v3 수정·검증 계획

실제 동일 물리 A/B에서 기존 안내는 접촉0, face-only playing-neck1 안내는 접근·유지·해제·재접촉을 모두 통과했다. 안내가 OBJ에서 실제 face에 쓰이지 않는 vertex까지 hull에 포함한 오류를 먼저 고친다. gamma/보상 계수/PD/한계/종료 조건은 이 수정에서 바꾸지 않는다.

## 작업과 판정

- [x] 활성517Python·README·AGENTS를 새 archive에 SHA와 함께 보존한다.
- [x] 기존 원본 입력이 필요한 A/B CPU 분석과 독립 검수가 끝날 때까지 활성 소스 동결을 유지한다.
- [x] loader가 물리 playing-neck1의 face 참조 vertex만 사용하도록 수정한다. headstock 전이면은 현재67목표의 안내 영역이 아니므로 합쳐 단일 평면을 만들지 않는다. API는 triangles/plane으로 유지한다.
- [x] 엄지 지원 계약v3 및 episode 진단 계약v6에 정확한 면 범위를 명시한다. 기존0.02/s 예산·같은 점 방향/거리/부하 gate는 유지한다.
- [x] CPU 회귀: flat rear z=-0.008m·유한 neck 경계·기존 witness 5.146mm 오차·실제 면 가까운 점의 후보/반대방향/무부하 제외, 기존 전체 관련 검사와 짧은 학습 계약 검사를 확인한다.
- [x] 별도 change-reviewer가 최소 변경·SHA 보존·범위/문서 일치를 확인한다.
- [x] 현재 loader를 쓰는 별도 GPU contact probe에서 실제 접촉→유지→해제→재접촉과 자원 종료를 확인한다. 과거 A/B를 새 생산 코드의 실행으로 소급하지 않는다.

## 이후 비교 순서 보정

이 검증 후 fresh 원래 gamma 기준선을 먼저 만든다. 시간척도 A는 같은 수정 후 기하의 기준선과 비교해야 한다. 기존 실행과 source seal은 보존하고 새 봉인·새 출력으로 진행한다. 엄지035 고정/손목 teacher의 큰 하중은 별개 문제이며, 이 기하 수정만으로 해결됐다고 보고하지 않는다. 하중 원인 분리·정상 해제·2~4음 전환·자유 기타·67음 평가가 남아 있다.

## 구현 후 CPU 결과

수정 전 관련48검사, 수정 후 환경·기본runner·짧은과제까지101검사가 통과했다. 실제 native B와 동일한 patch128점/normal/valid/유한rear꼭짓점/plane을 CPU에서 exact 비교했다. 사전519보관파일 SHA를 확인했고 활성변경은지정6경로뿐이다. 이전 모델 입력은기존strict검사에서변경4Python경로를명시하며거부됐다. 독립source검수는문제없음이며현재생산helper의실제GPU회귀는다음검사다.

## 생산 GPU 회귀

현재 helper로 fixed15초/3600물리 endpoint의5프로토콜을 모두 통과했고, launcher0·장면종료·137declared입력·450영상frame를 확인했다. 원본사전archive+사전CPU수정SHA에 기초한 활성517Python보충검증은 별도파일에 실행후기록했다. 자유 기타 추가검사는 접촉/유지/재접촉과2.976mm이격은통과했지만release창의candidate41/360=11.39%로기존10%미만기준에미달했다. 이를고정기타회귀통과와구분하고기준을바꾸지않는다. fixed전체동작은이전face-only B의31공통배열과exact동일했다. 새기준학습은large128/H32/300/seed7/원gamma로시작했으며고정기타제한과제다.
