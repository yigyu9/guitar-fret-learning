# PD 실행과 보완 후처리 기록

첫 palm_hold_pd_v1은 세 조건3init/72step 모두 exit0이며 실제 설정 readback과
state/target 보존 검사가 통과했다. setter API의 bool 반환값이 기록되지 않아
성공 반환 검사까지 포함한 별도 producer로 v2를 세 조건3init/72step 다시 실행했다.
v2도 모두 exit0이며 각 조건의 원자료5배열은 같은 배율 v1과 exact다.
이는 같은 실행의 이어쓰기나 추가72step 유지가 아니라 처음부터 시작한 별도 시험이다.
전체 PD 실행은6init/144step이고 관측2init/48step과 구분한다.

두 PD phase의 세 .log는 각각 실제 stdout/stderr 콘솔 캡처다. v2 execution.json은
실제 명령·elapsed·terminal exit code를 기록하며 analysis_execution.json은
rl38 환경에서 저장 자료만 처리한 후처리 exit0을 기록한다.

분석 첫 시도는 기본 Python에서 gymapi import가 실패했다. 그 시도의 producer와
stdout 파일 및 exit1 기록은 analysis_attempt_v1에 보존했다. stderr는 실행 도구로
반환됐으며 stdout 파일에 합쳐 캡처하지 않았다. 기록된 rl38 import 환경으로 분석만
다시 실행했고 추가 native 초기화/physics step은 없다.
문법 검사와 원본 보존 검사도 신규 물리 실행이 아니다.
