# Native velocity 좌표 감사 독립 검수

요약 판정: **문제없음 / 읽기 감사 PASS**. 남은 Critical·Warning·Suggestion 없음. 다른 파일 수정·native 초기화·물리 실행은0회다.

- `analysis.py:48`의 계산 입력3개 SHA와 현재 분석 소스 SHA가 summary와 일치한다. JSON/XML을 읽기 전 입력 SHA를 수집하고 종료 대조하며 simulator/helper 실행 import는 없다. Python3.8 AST도 통과한다. 저장 trace는151개, step0..1200의8-step 간격, 시간0..5초/30Hz와 일치한다.
- `:90–112`의 native 이름별8그룹 및 XML parent/axis mapping, 별도 scalar q/v 읽기, 같은 snapshot의 world angular velocity 차이 `ωchild,W−ωparent,W`를 확인했다. 이름의 x/y/z suffix를 world축으로 해석하지 않는다. 10개 후보의 코드 순서·표현식과 문서가 일치하며 B·Jleft·Exp·parent/child/world frame을 구분한다.
- 모든8그룹에서 native-v mask `||v||>0.01` 및 별도 reference mask count를 대조하고 주요3후보를 독립 재계산했다. `:40` RMS는 세 scalar 성분을 개별 평균한 값이 아니라 `sqrt(mean(||벡터오차||²))`다. `:159`는 그룹별 RMS 평균이 아닌 전체 mask 표본을 합친 집계다. 총1,188표본에서 child Bv RMS/max0.00036523815267426504/0.0032007713155937224rad/s, parent Bv RMS0.16984619141062732, parent Jleft Bv RMS0.08725150298680298로 저장 결과와 일치한다.
- `:122–134`의 q 중앙차분·relative rotation log 중앙차분 및 parent→world 변환을 검수했다. 내부149개 시점에서 양옆 간격은총16physics steps=0.066667초다. R_Shoulder/R_Elbow/R_Wrist의 native-v 대 FDq RMS0.437060801/0.630352764/0.267039895rad/s 및 pose-FD 대 snapshot 상대 angular velocity RMS0.407210667/0.529176350/0.229752508rad/s를 각각 독립 재계산해 일치했다.
- README의 수치·표본수·단위와 summary의 관측 범위가 정확하다. Child Bv와 parent Exp(Bq)Bv가 이 자료에서 근접한다는 결과를 일반 rest-frame 생략 계약으로 확대하지 않는다. 유도된 chart qdot는 조건부 수학식이며 실제 q 시간미분·force/virtual-work 공액 좌표·Jacobian·다른 asset/driveMode의 증명으로 사용하지 않는다. 큰 FD 오차의 가능 원인도 분리 측정하지 않은 가설로 한정되어 있다.

확인 SHA256: 분석 `6faea466c1a7ed710f397a00321bd0800f5c28f9992bff12daba41c532c28e0a`, summary `f408291cab3942a6a5ab819a514a5ee9c58ee08e20cedcc42e14ed8f30e4f86f`.

이 판정은 저장 snapshot의 수치 관계와 감사 구현·문서 범위다. Native velocity API의 일반 좌표 계약·순간 시간미분·torque 설계의 물리 유효성·폐루프 안정성·지속 지지 또는 후속 회전 spring 결과를 인증하지 않는다.
