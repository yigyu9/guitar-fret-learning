# 프로젝트 작업 맥락 — 2026-10-19

현재 구현·완료 결과·진행 중인 전곡 작업은 [CURRENT_STATUS](/home/ajou/yigyu/3/CURRENT_STATUS.md)를 기준으로 읽는다. 정량 결과와 원자료 링크는 그 문서에 모았다.

- 주제: 오디오 목표를 휴머노이드와 자유 기타의 물리적 상호작용으로 실행한다. 모션 생성 모델은 사용하지 않는다.
- 물리: Root 고정·하체 유한 제어·105채널/97비영 범위/8원 영범위, 기타 중력ON·스트랩OFF.
- 정책: 왼팔·왼손33축과 오른팔꿈치·손목6축. 나머지 관절의 유한 자세 유지와 신경망 출력을 구분한다.
- 완료: 손별563 BC 각4/4 평가. 단음joint1132상태·Actor 각569입력, 실제840전이·PPO1회와 저장 모델 재평가. 공동 음악 성공0.
- 전곡: song500상태·67음·1969tick,4096전이·8업데이트 완료. 안전 완주2회, 전곡 음악 성공0/2. 저장 모델의 별도 평가를 구분한다.
- 코드: 신규 환경·학습은 `guitar_learning/`에 둔다. [현행 안내](/home/ajou/yigyu/3/guitar_learning/README.md)에서 버전을 선택한다.
- 초기 상태: 기존035/v14를 사용하고 native 정착 대기는0초다. 단음7초와 전곡32.8166667초의 정책 준비3초를 구분한다.
- 결과: phase별 설정·소비 입력·에피소드·전이·PPO 반영·종료·checkpoint와 실패를 함께 보존한다.

논문 제목은 **From Audio to Full-Body Guitar Performance with a Freely Moving Instrument**다. 순서는 Abstract→Introduction→Related Work→Methodology→Experiment→Result→부록이다. [작성 원칙](/home/ajou/yigyu/3/paper/AGENTS.md)과 [근거 색인](/home/ajou/yigyu/3/paper/evidence_index.md)을 따른다.

