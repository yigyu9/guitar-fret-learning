# 잡기·놓기 진단 V2 재현 검증

V1의16초/3840step 실행은 정상 종료했다. 실제 A/B 잡기 유지 각각360/360표본에서 엄지와 다른 손가락의 양의 raw lambda 동시 접촉을 관찰했다. 놓기 원시 contact 분류에 L_Hip이 포함되는 prefix 오류를 발견했고, 상속 tracking.encode의 이전 벡터 “final” 설명도 남아 있다. V1 원자료·소스는 보존하고 분석에서는 하체를 명시적으로 제외한다.

V2는 동일 초기 자세·궤적·gain·모델·16초로 재현한다. 왼팔/손 contact 분류만 실제12팔/21손 관절 body 목록으로 한정하고, 실제 MRO encode 모듈의 save를 patch해 이전 벡터 scope를 명확히 한다. 직접 읽는 A/config.json도 사전 SHA에 추가한다. V1에서는 이 파일의 실행 전 SHA가 누락됐으므로 사후 해시로 소급 인증하지 않는다. 모델/자산 SHA·초기 native state exact·동적 가드 통과는 V1 기록대로 별도 유효하다.

- [ ] 소스 문법 및 독립 재검수.
- [ ] 동일16초 실제 Isaac Gym 재현.
- [ ] 실제 LH 접촉-free 구간/엄지+다른 손가락 동시 접촉 확인, 기타 변화와 V1 대조.
- [ ] 전체 영상·문서·입력 보존 검증.

완료 상태는 결과 문서에 남긴다. V1 계획의 다른 조건과 안전 범위를 유지하며 오른팔 타현은OFF, 유한 오른팔 지지 유지, 기타는 자유·스트랩OFF다. 변경 코드는 새 left_grip_release_cycle_v2.py/run_left_grip_release_cycle_v2.py이며 기존 소스는 수정하지 않는다.
