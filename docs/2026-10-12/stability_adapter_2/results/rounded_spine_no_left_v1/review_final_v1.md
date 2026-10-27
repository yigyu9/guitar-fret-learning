# 분산 척추 굽힘·왼손 비지지 초기 시험 최종 검수

요약 판정: **문제없음 — 완료된 네 조건의 5초 고정 PD 진단과 결과 해석 범위.** 미결 Critical은 없습니다. 왼손 비지지 초기 조건의 기타 유지는 실패했습니다.

## 독립 대조 결과

- [실행 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/verification_v1.json:1)의33검사 입력 SHA와 현재 소스 핀, 네 native 입력 closure를 대조했습니다. 각각1200물리 step/300제어/301상태·초기 q_ref 고정 목표·금지 API0·원본 strap ON·151프레임 녹화를 완료했습니다. v2의 앞8cm·아래3cm 철수 목표가 실제 입력이며 v1의 거절 결과는 보존됐습니다. 체크포인트·Actor·음악·학습·preload·실시간 IK를 실행한 시험이 아닙니다.
- 저장된 기타 위치/quaternion으로 초기→5초와2→5초 이동·SO(3)를 직접 재계산해 요약과 일치했습니다. 실제 접촉300표본에서 모든 L_/LH: 집계와 오른상완/전완/몸통 집계를 대조했습니다. 9° 지지/철수 쌍의 왼팔을 제외한 초기 q_ref 목표는 exact 같습니다.

| 조건 | 초기→5초 이동(cm) / SO(3)(°) | 2→5초 이동(mm) / SO(3)(°) |
|---|---|---|
| 기존3°·왼손 철수 | 36.237116 / 88.160905 | 0.908097 / 0.177405 |
| 분산9°·왼손 지지 | 10.843378 / 18.973592 | 0.047841 / 0.008496 |
| 분산9°·왼손 철수 | 33.535987 / 83.305484 | 0.000543 / 0.000078 |
| 분산12°·왼손 철수 | 33.286432 / 83.414347 | 0.000268 / 0.000037 |

세 비지지 조건의 모든 왼팔·손 접촉 query는0/300이며 R_Shoulder도0입니다. 9° 지지는 왼쪽 접촉299/300·R_Shoulder284/300입니다. 비지지3°/9°/12°의 R_Elbow 접촉은0/4/6표본뿐이고 Chest/Spine은모두0, 9° 철수의 Torso는1표본입니다. 초기에서 크게 이탈한 뒤 정착했으므로 작은 후기 변화는 초기 자세 유지 성공이 아닙니다. 원본 스트랩이 유지된 초기 철수 시험이며 실제시간 release나 strapOFF 결과가 아닙니다.

## 문서·그림·보존

- 실제 PNG3개를 열어 전신/손0·2·5초 프레임과 전체/후기 곡선의 조건·범례·단위를 원자료와 대조했습니다. [결과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/README.md:22)과 [상세 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/artifacts_v1/README.md:34)은 초기 실패·후기 정착·접촉 관측을 구분합니다. 오른상완 source signed-gap 약0.503mm를 cooked 최단 간격/지속 지지로 해석하지 않습니다. 초기 굽힘은 분절 모델의 관절 구성이며 새 연속 척추 형상 변경이 아닙니다.
- [후처리 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/artifacts_v1/provenance_v1.json:1)의43입력 전후 SHA와9출력 SHA, [영상 manifest](/home/ajou/yigyu/3/docs/2026-10-12/video/rounded_spine_no_left_v1/manifest.json:1)의8원본/복사 SHA가 일치합니다. 물리5초와 t0 포함 MP4 5.033333초를 구분했습니다.
- [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/CHANGED_FILES_V1.md:1)·[영상 색인V12](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V12.md:1)의 절대 링크/실제 줄과 main4 완료 append의 원문 prefix·전후 SHA를 확인했습니다. [봉인 구현](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/seal_phase_v1.py:8)을 읽기 전용으로 검토했고 주요 범위 누락은 발견하지 않았습니다. 이전2590개 전체 보존/세 main append chain/전체2416이미지/최종 snapshot·inventory의 실제 실행은 root 후속 봉인 범위입니다.

## Warning

- [analyze_native_v1.py:28](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/analyze_native_v1.py:28)의 `all_left_arm_hand` 집계는 `L_` prefix로 왼하체 이름도 포함할 수 있습니다. 이번 집계 원자료는 지지 조건에서 palm/finger만 관측했고 비지지 조건은모두0이므로 현재 결론에 영향은 없습니다. 향후 새 분석 버전은 명시적인 왼팔·손 몸체 목록을 사용하도록 권장합니다. 소비된 원본은 보존합니다.
- [결과 설명:26](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/README.md:26)처럼 접촉0은60Hz query 관측이며240Hz 전체 substep·연속시간 비접촉 인증이 아닙니다. raw λ는 뉴턴 힘·압력으로 환산하지 않았습니다. 다음 접촉 배치 제안은 미실행이며 이 네 조건으로 보편적인 최적 자세를 결정할 수 없습니다.

검증 JSON SHA256: `3b165fa30c0b951366e19b4277a39621d73f615a081187119794abc8bfdbaf56`. 검수자는 이 새 리뷰 파일만 작성했고 추가 물리·정책·학습 실행 및 기존 파일 수정은 하지 않았습니다.
