# 같은 초기 설정의 3초 진단 — 독립 통합 검수

검수일: 2026-10-07 KST. 별도 change-reviewer가 신규 비교·그림 코드와 저장 실행·문서를 검수했다.
쓰기 범위는 이 파일뿐이며 원자료·코드·기존 동결 검수 기록을 수정하지 않았다.
새 native simulation이나 초기 native 환경 생성은 하지 않았다. 재현·누락 fixture 출력은 별도 /tmp에만 저장했다.

**요약 판정: 문제없음. 남은 Critical / Warning / Suggestion 없음.**

## 신규 코드와 계약

- [compare_quiescent_run.py](/home/ajou/yigyu/3/stability_adapter_2/compare_quiescent_run.py:22)는 저장 raw6 JSON과 이전 source audit를 명시적으로 읽는다. 배열 prefix 비교는 trace/states/contacts/controls/leg_torques 5개이며 report의 조건·구동 속성은 별도로 대조한다. downstream 출력 수집이나 native dynamics 호출은 없다.
- [plot_quiescent_pose.py](/home/ajou/yigyu/3/stability_adapter_2/plot_quiescent_pose.py:22)는 전역·행별 checks, 실제 ON run 경로와 embedded SHA를 확인한 뒤 저장 pose를 재구성한다. 기존 geometry helper를 재사용해 step 0/240/720, 동일 world bounds·camera와 기록된 route를 표시하며 source 형상과 native renderer를 구분한다.
- 두 새 파일의 AST 검사를 통과했다. 비교 CLI를 새 /tmp 출력에서 실행해 exit 0 및 canonical comparison 전체 JSON 일치를 확인했다. 기존 결과가 있으면 거부하며 새 CLI의 명시 입력 경로와 출력 보존 조건이 적절하다.
- 원자료를 symlink로 읽고 마지막 control sample 하나만 생략한 별도 /tmp fixture에서 comparator는 exit 1/sample_counts=false로 실패했다. 새 plotter는 failed comparison을 거부하고 이미지 출력 전 중단했다. 원자료는 변경하지 않았다.

## 저장 실행 독립 검증

- 입력은 직전 left_wrist_strap_v1/load_00n 설정과 byte가 같고 native 실행 기록은 기존 runner·PI ON·720 physics steps, exit 0이다. 초기 전체 q/body/기타 상태·목표 p/q·PD·cap·solver·LA·제어 조건이 이전 1초와 같다. 이전 1초의 배열 raw5 prefix는 모두 정확히 같다.
- 720 physics samples와 721개 저장 시점, 240Hz/60Hz 스케줄을 직접 확인했다. 180회 PI update를 구현 호출 없이 e=q_ref−q, 적분·최종 clipping·조건부 rollback 수식으로 재계산해 여섯 저장 벡터와 정확히 일치시켰다. update 사이 기록은 유지되고 native float32 목표는 허용 오차 안에서 같다.
- 팔24 PI ±0.15 rad cap·최종 C02/model box와 주요 66 연결을 유지한다. 손가락42·몸통9·C02 하체는 PD 목표를 유지하며 실제 상태 고정이 아니다. 모든 저장 humanoid root state가 초기와 같고 runner의 target-only/state-write 없음 검사가 통과했다.
- 기타 저장 위치·선/각속도를 native body state와 대조하고 목표 위치 오차·quaternion geodesic 회전 오차를 재계산했다. 각 시점 time/step이 맞고 최초 +5mm 목표 p/q를 후기 이탈 자세로 재설정하지 않았다.
- 직전 route 위치·속도에서 원본 k=6000/c=120/최대300 N slack 법칙을 매 tick 재계산해 적용 tension과 일치시켰다. 절대 LA=1.1010801317960974 m는 고정이지만 runtime tension은 가변이며 post-step 길이와 적용 힘의 시점을 구분한다.
- 접촉 행·고유 samples·첫/마지막 step, 포화 held samples, 실제 arm q의 초기 기준 편차·scalar-limit 초과와 native landmark 기반 palm-up proxy 최솟값을 재집계했다. proxy의 해부학적 부호 검증을 주장하지 않는다. 37개 comparison checks와 79개 입력 SHA가 현재 자료와 같다.

## 결과와 설명

- 최대 기타 오차 251.150464813 mm/81.526862883°, 종료 236.386967767 mm/77.801738144°, 종료 속도 0.012952304 m/s·0.038382001 rad/s가 표·계획·누적 보고서와 맞다. 낮은 종료 속도는 목표를 유지한 성공이 아니라 크게 다른 자세의 후기 상태다.
- 최대 tension 72.260483 N, 실제 arm q의 초기 기준 최대 편차 14.698074°, scalar-limit 초과 0.030300°와 포화 692/720 held samples가 원자료와 일치한다. target bounds 통과와 실제 상태의 제한·안정성 판정을 분리한다.
- LH/어깨 접촉 행은 0이다. Pelvis/R_Elbow/R_Hip/Torso/RH 엄지 접촉 표의 행·고유 samples·첫/마지막 step이 원자료와 맞고 힘·원인·관통 깊이·연속 지지를 단정하지 않는다.
- README의 이전 동일 자세 1초 OFF 144.267967 mm/36.395296°와 ON 73.268255 mm/13.439339°를 링크된 원 trace에서 확인했다. 이번에 OFF 3초를 실행한 것처럼 표현하지 않는다.
- QUIESCENT 계획 결과·PLAN §42·adapter README·VISUAL §34는 같은 실패 해석을 설명한다. 3초는 관측 기간이며 WAIT 선행 과정이나 새 성공 기준이 아니다. 이후 손 위치 유지 제안은 현재 기준/frame 검토와 사용자 확인 전이며 새 controller/gain/gate/기타 p/q feedback/학습을 구현하지 않았다.

## 최종 문서·미디어 확인과 동결

- [두 지원 CLI](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/README.md:45)를 새 `/tmp/quiescent_reviewer_20261007/{trace,geometry}` 경로에서 실행해 exit 0을 확인했다. trace 1902×630, source geometry 2279×931 PNG는 canonical과 byte·RGBA pixel이 정확히 같다.
- 두 canonical 이미지를 직접 확인했다. trace의 시간·단위·curve, geometry의 0/1/3초 caption·저장 pose·기타/손 색·route·동일 world bounds/camera가 맞다. 그림은 source collision 형상 재구성이며 cooked clearance·접촉·지지력 인증이 아니다.
- 두 canonical 및 재생성 manifest의 실제 입력·producer·output SHA를 직접 대조했다. geometry에는 comparison1/raw3/helper8/source config·XML·mesh40/embedded79/output1이 기록되며 출력 hash는 입력과 분리된다. 생성된 절대 링크와 실제 줄 anchor가 존재한다.
- README:15 표기는 ‘팔 실제 q의 초기 기준 대비 최대 편차’로 교정돼 계산식과 target cap을 구분한다. 해당 Suggestion은 해결됐으며 남은 지적은 없다.
- 계획 체크·인덱스 검수 상태·예정 snapshot metadata는 부모의 후속 정리 범위다. 이 기록을 동결하며 snapshot 수집 뒤 추가 수정하지 않는다.
