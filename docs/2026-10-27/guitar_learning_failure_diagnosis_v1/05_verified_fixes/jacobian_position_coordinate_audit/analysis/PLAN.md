# 실제 동시 frame CPU 분석

root 실제 단1조건 exit0 인계 후 진행한다. 이 analysis/만 수정하며 690봉인·raw·활성소스/GPU를 보존한다.

- [x] launcher/scene/17checks/690pins/4환경 첫시도·실패분모 및 원래 평가/전 trace 실제동일성 재계산.
- [x] 4시점×4환경의 raw q/qd/body/COM/nativeJ clock/행열 확인, wrist COM→origin 및 angular nativeJ@qd closure.
- [x] env0 next feedback4개의 원래nativeDLS+clip 재현. 다른환경에는 저장 feedback 원장이 없음을 표시.
- [x] 팔4개 ball의 ownbody FK pose 일치, native angular block S·독립 qpos 미분M·T=S⁻¹M 조건수/민감도 및 nativewristJ×blockdiag(T) 재현 확인.
- [x] 수치/작은그림/한국어 RESULTS·verification·독립 change-reviewer 검수.

T는 qpos rate→native velocity 좌표의 실측 국소 변환 후보로 검산한다. 팔/wrist16표본의 수치적 확인 이상으로 일반화하지 않으며, MCP 2축·production 보정·힘·성공 개선을 구현하거나 주장하지 않는다. 기존60Hz 차분 오차와 실제 동시 native closure를 분리한다.

최종: results_v2의 실제 CPU 분석/독립검수 PASS. S/M 원행렬이 NPZ에 있다는 문구1건은 T/wrist 행렬만 저장한다는 사실로 수정했다. 검수자는 독립epsilon2e−5 및 회전행렬 미분으로 basis를 재검산했고 전체 결과도 메모리 재실행했다.690봉인/raw/생산 소스와 GPU는 변경하지 않았다.
