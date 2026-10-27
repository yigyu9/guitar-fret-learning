# 정적 마감 설명 보완 검수 v4

요약 판정: **문제없음.** 이번 검수는 새 [결과 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/README.md:1)와 [변경 파일 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/CHANGED_FILES.md:1)의 정적 설명만 대상으로 했다. 기존 검수·소스·산출물은 수정하지 않았고 추가 native 실행·정책 추론·학습은0이다. 이 파일만 새로 작성했다.

Critical 없음. 추가 Warning 없음.

[README:25](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/README.md:25)는 `last_applied_tension_n`을 관측 시점의 **직전 물리 적분에 제출된 계산 케이블 명령**으로 정확히 정의하고, 소비 산출물 v2의 ‘다음 적분’ 표현을 명시적으로 정정한다. 센서값·현재 후보 장력과 혼동하지 않는다. 따라서 [검수 v3](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/review_v3.md:1)의 설명 시점 Warning은 이 새 마감 설명에서 해소됐다.

초기 OFF/ON 비교의 동일 정책·초기 상태, 위치/회전 정의, 안정화·음악 실패 판단이 앞선 raw 검수와 일치한다.12회 갱신·각3072전이와 OFF4.55초 안전 종료/ON full16.3667초를 구분하고, 조기 종료로 검열된 OFF 비율을 ON 전체 구간과 직접 비교하지 않는다. ON12회 위치 밖95.62%는 저장된 controls에서95.621181%로 재계산되어 일치했다. reset300진단/추가 최적화0, probe v1 물리0 실패와 이전 long_run 실패의 미상 관절속도 범위도 분명하다.

[README:47](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/README.md:47)는 CPU PhysX/CUDA 정책·PPO,12-update CP에서 새 물리 episode로 재개하는 장기 실행, `initial_000000`의 내부12회/3072 이력을 구분한다.11:40/11:59는 예약 설정으로 설명하고 진행 중 성공·정오 산출물 완료를 판정하지 않는다.30분 반복 평가와 최종 판단 체크박스도 미완료다. 파일럿을 전체 보상 구현·연주 학습 완료로 부르지 않는다.

두 문서의 모든 절대 링크 존재·인용 행 유효·trailing whitespace0을 확인했다. 색인의 route law42/force guard58/environment188, warm-start16/equivalence85와 네 main 추가분의893/1992/662/2442행은 실제 정의/제목과 일치한다. 동적으로 갱신되는 장기 폴더를 봉인된 완료 결과로 취급하지 않는다는 설명도 맞다. 프로젝트 전체 보존 감사·장기 실행 상태·최종 마감 인증은 이번 정적 검수 범위 밖이다.
