# 누적 손목 요청과 실제 추종 지연 CPU 감사

root 승인한 관찰만 수행한다. 소유권은 이 새 폴더이며 active/기존결과/GPU/native는 변경·실행하지 않는다. old original0.5°·lowgain0.1°·current qposv2의 index_reference env0만 사용한다. 기존 archive 검증은 `wrist_position_jacobian_v2/analysis/results_v1/verification.json`을 참조하며 stale old checkpoint의 현재 strict load를 시도하지 않는다.

- [x] source/FK/metadata SHA와 기존 실제 종료·4시도 전체결과/원본 trace 입력을 확인한다.
- [x] 세 trace의221전체 끝점에서 full_fk(actualq)의 wrist/native pose 일치를 확인한다.
- [x] endpoint≥2초의102끝점을 모두 분석한다. qpos actual의 nonarm을 유지하고 arm12만 request 또는 submittedtarget으로 바꾼 FK는 **가상 FK**로 명시한다.
- [x] feedback[k]는 precontrol[k−1]/nextgoal[k]와 맞춘다. precontrol≥2초인101전이에 요청 누적/clip 및 제출목표 alpha/rate 관계를 검산한다(2초경계도 전체 표본에는 보존).
- [x] 실제·가상요청·가상제출목표의 goal 오차,request/target/actual gap,목표반대편 투영과 계속누적 방향을 전표본에서 집계한다.
- [ ] 작은 그림/한국어 결과/원자료 검산·독립검수 뒤 한계와 최소 다음실험만 정리한다.

'이미 넘었다'는 실제 goal-error 방향을 기준으로 요청 FK가 goal 반대 halfspace에 있다는 **투영상 정의**다. 임의오차문턱을 만들지 않고0 기준 dot 부호·가상 goal거리 증가를 별도로 기록한다. 회전은 같은world Log-error의 dot 부호이며 SO(3)의 전역 직선통과를 뜻하지 않는다. 모든 증분은qpos 요청의 유한FK차이를 사용하고 nativevelocityJ와 혼합하지 않는다. 이 가상 요청각은 실제native실현/충돌가능/물리평형의 증거가 아니며 손MCP로 일반화하지 않는다. 생산controller/새gain/시간/힘/보상/실패gate는 변경하지 않는다.
