# 실제 수집·후기분석 독립 검수

요약 판정: **문제없음 / PASS**. 최종 `analysis/results_v2` 기준 Critical·Warning·Suggestion 지적 없음. 이 PASS는 진단 자료와 기준 재현의 정확성을 뜻하며 음악 수용이나 기본 채택을 뜻하지 않는다.

- 현재 봉인 입력910개를 포함한 고유1005개 입력·출력 SHA를 모두 확인했다. 네 실행의 기록된 종료코드는0이고 observer는354회 act/step,45312×4 actor 행, raw128 첫시도·384음과 종료된 장면을 남겼다. 원 checkpoint·모델·optimizer 불변과 입력 감사 결과도 확인했다. 검수자는 GPU/native/체크포인트 load/실모델 생성·forward를 추가 실행하지 않았다.
- 전체512개 raw v8 원장과 v2의10몸체/3원인 순서, source ID·target ID·실제 음 길이 분모를 확인했다. raw left/clean/wrong/missing을 compact achieved/시간비율과 전부 대조했다. 분모는 A0.1703s/B7 0.7779s/B8 0.3483s이며 required clean 시간을 대신 쓰지 않았다.
- 평균/private7은 원 V7 전체128 평가 JSON과9보상, env0 모든 비힘 trace 필드가 정확히 같다. 힘 최대차이는 양쪽 모두7.62939453125e-6N으로 별도 보고됐다. 네 조건의 최초128 mean/log_std가 같고, actor tick/env ID/clock/tanh 및 env0 목표 일치를 확인했다.
- 독립 코드로 네 조건9보상 평균, 음별 비율/달성/해제, 전체360개 body/cause/note/case 출처 시간비율·활성환경·프렛범위, Gaussian latent 잡음RMS/std 평균/정규화RMS를 재계산하여 최종 analysis.json과 일치했다.
- 실제 rl38 CPU·CUDA hidden 환경에서 최종 analyze_v2를 `/tmp` 새 디렉터리에 재실행했다. JSON·문서·그림2개의 네 최종 출력이 byte exact였다. 두 그림을 직접 시각 검수했다.

|조건|세 음 달성/128|달성+첫음 해제/128|첫음 해제/128|
|---|---:|---:|---:|
|평균|13|5|13|
|private7|58|30|60|
|private17|60|27|59|
|private27|68|29|60|

평균행동의 뒤두음에서 index3 own_wrong_fret와 own_wrong_string은 각각0.7421875이며 출처 프렛은4..4, 목표는5다. 두 원인은 겹치므로 합산하지 않는다. 원소스7/8은 음 ID이며 두 음 모두2번현5프렛이다. private17/27 일부 누적 출처 범위는4..5이므로 모든 확률 오압현을4프렛만으로 설명할 수 없다. 프렛 범위는 몸체별 여러 원인의 합집합이지 각 원인의 독립 범위가 아니다.

초기 results_v1 heatmap의 colorbar 겹침/라벨 잘림은 검수 중 발견하여 수정됐다. 원 analyze.py 절대경로/바이트와 results_v1을 보존하고 analyze_v2.py/results_v2로 분리했다. 양쪽 각각991개 입력과4개 출력의 현재 SHA가 유효하다. 두 버전의 analysis.json·env0 그림은 byte exact다. 명시적으로 superseded 처리한 중간 layout 시도는 현재 유효한 입력 증거에서 제외한다.

네 조건 모두 원 음악 stage_ready는 false다. 이는 물리/reset seed7을 고정한 정책 잡음 표본3개이며 새로운 학습 seed3개가 아니다. 최초 행동 이후 상태·평균행동이 함께 바뀌므로 후반 차이를 순간 잡음의 단독 인과효과로 설명하지 않는다. 60Hz endpoint와240Hz 누적 원장만으로 정확한 substep 사건·실제 접촉쌍·줄 압력·음향을 입증하지 않는다. 고정기타·검지4축·원3음 범위이며 다른 손가락/학습seed·자유기타J33·원67음의 미완료 범위는 그대로 남는다.
