# 최종 그림·검증 상태와 후속 결정

새 실제 시험은 한 번, 초기값 포함5초/1200physics step이다. 전신·손151frame 영상과
원native PNG·스트랩 overlay PNG를 보존했다. 세 조건의 초기11필드/81관절 이름/
1200제출 목표는 일치하며 trial에서는 절대LA만 원본 대비−4mm다.

Luna가 문서·그림 producer를 작성하고 root가 실행했다. V1의 범례9개 중복,
v2의 caption과x축label 겹침을 실제PNG에서 발견해 원본/manifest/소스/로그를 모두
보존한 뒤v3를 생성했다. V3는 범례3개, caption과x축label이 분리되어 root 실제QA를 통과했다.
원자료3조건의 추세/단위와 대조했고 native hands t0/5s 두 장면도 직접 확인했다.
그림 재생성은 저장 trace만 사용하며 추가 물리 시험을 하지 않았다.

![원본/−2/−4mm 실제측정 비교 최종v3](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/artifacts/body9_strap_minus4mm_comparison_v3.png)

각 선은 같은 작은손목목표 조건의 실제0~5초 측정이다. 위에서부터 초기위치오차mm,
초기회전오차°,직전step 적용 cable법칙장력N이다. 현재hand-pose 고정 그림이나
학습된 연주 결과가 아니다. −4mm는회전감소/후기변화증가를 함께 보이며 위치최대는거의같다.

[후속 결정](/home/ajou/yigyu/3/stability_adapter_2/STRAP_MINUS4MM_DECISION.md:1): −2mm는후기유지비교기준,
−4mm는회전개선후보로보존한다. 다음은추가단축대신팔12+조건부hinge6의연동source검증이다.
손바닥positiveλ0과불완전한세면지지는유지하며 초기p/q복원·연주성공을선언하지않는다.

[보완된checkpoint schema 조사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/contract_correction/contract_audit.json:1)는
fret.observation.v2/strike.observation.v2를각각명시한다. 기존null표시조사는그대로보존했다.
다섯CPU검사통과,추가모델추론/학습/물리실행0이다.

[영상126개 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v4.md:1),
[변경 줄 보충](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/CHANGED_FILES_SUPPLEMENT.md:1).
독립검수는[review.md 예정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/review.md:1),
최종보존검사는[final_verification.json 예정](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus4mm_v1/final_verification.json:1)으로구분한다.
