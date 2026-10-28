# 소지121 새4시도 분석 준비

이 `analysis/`만 추가하며 기존1108봉인·준비·소스·원자료는 바꾸지 않는다. GPU/native 실행0이다. root의 학습+평가와 소지 fresh4 실제 종료 통보 뒤에만 `analyze.py --root-completed`로 새 `results_v1/`을 만든다. 무인자 실행은 원자료/배열 모듈을 읽지 않는다.

1. 실제 한 child 소지 launcher 종료0, 준비 PASS/전체 SHA, 원105 native readback/16 effort0.25Nm/90pairs/4환경·장면종료·입력 전후·경로 객체 복원을 확인한다.
2. 모든4첫시도와9보상·실패를 원 acceptance 그대로 집계한다. 원 grid121(env62)의1시도와 새4시도는 별도 실행이고4seed가 아님을 표시한다. baseline112의 새grid시도와 원 reference4/zero4도 출처를 분리한다. 기존 검수된 분석값을 재사용하며 grid 전체를 다시 계산하지 않는다.
3. 기존 prelearning `trace_audit`로 새 env0/60Hz 각도·세 마디 힘·손목·CPU6gate/오프렛·오현·other higher·arm actionbounds를 분석한다. 원자료의 선택 target4가 ramp 후121목표와 맞는지, 저장된 인접 끝점 사이4rad/s/원nativebounds를 지키는지 확인한다(t0 target은 미저장). env0의 전체 LH body 순힘 평균/p95/최대를 함께 남긴다.
4. 실제 결과·짧은 한국어 표와 독립 검수를 남긴다. 새4시도가 미완료면 미완료 그대로 기록하고 판정 문턱을 낮추지 않는다.

미저장 nativeqd/다른3환경 상세힘/nearest sample·normalcos를 추정하지 않는다. CPU기하와 실제240Hz음원장을 구분하며 nearest가 any-candidate와 같은 점이라고 인증하지 않는다. actionbox 경계와 native범위/actual 추종을 구분한다. 몸체 순힘은 접촉쌍·현 압력·모터 토크가 아니며 고정기타/noNN 유한목표를 정책학습·자유 기타·인체정답·생산채택으로 확대하지 않는다. 같은 팔 teacher여도 actual feedback/손목 경로가 달라질 수 있다.
