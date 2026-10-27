# 승인된 기타 초기 Z +5mm 시험 검수

2026-10-06, 별도 change-reviewer 검수. 요약 판정: **문제없음**.

현재 남은 Critical / Warning / Suggestion은 없다. 이 판정은 승인된 초기 배치 변경,
CPU 진단 실행, 결과·그림의 정확성에 대한 것이며 정지 안정성 성공 판정은 아니다.

## 검수 범위와 계약

- [입력 검증](/home/ajou/yigyu/3/stability_adapter_2/trial_settings.py:23)은 실제 Z offset을 0 또는 +0.005m로 제한한다.
- [초기 목표](/home/ajou/yigyu/3/stability_adapter_2/environment.py:46)는 원본 위치를 별도로 보존하고 승인된 offset만 더한다. actor 생성에 적용하고 prepare 이후 초기 상태를 한 번 복원한다. 실행 중 body/DOF 상태 재주입은 없다.
- [native 계약 테스트](/home/ajou/yigyu/3/stability_adapter_2/tests/test_native_contract.py:12)는 사람 초기 상태·기타 회전/속도·절대 rest length 보존, 모든 기타 body의 Z 평행 이동 및 초기 상태 제출 호출 횟수를 확인한다.
- [원본 기준 오차](/home/ajou/yigyu/3/stability_adapter_2/run_initialization.py:21)는 후보 목표 오차와 별도로 기록한다. 기타 회전 목표는 원본과 동일하다.
- [짝지은 비교](/home/ajou/yigyu/3/stability_adapter_2/compare_guitar_z_trial.py:62)는 초기 관절 목표, native gain/mode/cap, solver, 절대 스트랩 길이와 원본 기준을 대조한다.
- [후속 승인안](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_Z_TRIAL.md:49)은 아직 미실행이며 하체 초기각 변경에 사용자 확인이 필요함을 명시한다. 이번 완료 시험의 승인 범위에 포함하지 않는다.

## 독립 검증

1. 프로젝트 rl38/native Gym 환경에서 전체 unittest 17개를 직접 실행해 통과했다. CUDA 미탐지와 visual geom 오류가 있는 CPU 진단 조건이며 native renderer 검증은 아니다.
2. H0와 +5mm를 각각 동일한 24 physics steps로 파일 저장 없이 재현했다. 각 run의 25개 native 상태·trace sample과 24개 contact record가 저장된 원자료와 정확히 일치했다. 실행 중 목표도 변하지 않았다.
3. 두 초기 source geometry query를 다시 계산해 저장 결과와 정확히 대조했다. 모든 위치·원본 위치·회전 최대 오차와 하체 raw 각도 최대 편차를 원자료에서 독립 계산했다.
4. 후처리를 /tmp의 복사본에서 실행해 comparison JSON을 정확히 재현했다. 기존 geometry의 bytes/mtime은 유지됐으며, 불일치하는 기존 geometry는 FileExistsError로 거부되고 덮어쓰지 않았다.
5. [plot 코드](/home/ajou/yigyu/3/stability_adapter_2/plot_guitar_z_trial.py:18)의 단위·목표 구분과 source 형상 좌표를 대조하고 두 PNG를 직접 확인했다. 임시 경로에서 timeline 2108×1390, source geometry 1742×998 그림이 픽셀까지 동일하게 재생성됐다. 검증 전후 기존 JSON/PNG의 SHA256과 mtime은 불변이었다.
6. [결과 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/README.md:7), [누적 그림 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:484)의 수치·원자료 링크·source/native 구분과 승인 범위를 대조했다.

## 수정 후 해소된 지적

- 기존 geometry를 무조건 쓰던 후처리 보존 문제는 [기존 파일 검증·재사용](/home/ajou/yigyu/3/stability_adapter_2/compare_guitar_z_trial.py:28)으로 해소됐다. 위 독립 재실행에서 동일 파일 보존과 불일치 거부를 확인했다.
- 결과 README의 후속 목표 표현은 [올린 후보 목표 고정·원본 오차 별도 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/README.md:35)으로 명확해졌다. 재생성 명령은 native library 탐색 환경을 명시한다.

## 결과 해석과 기록 한계

초기 human–guitar source query 음수 pair는 1→0, R_Hip gap은 −1.331→+3.303mm로 개선됐다.
최대 후보 목표 오차는 H0 65.315mm/7.318°, +5mm 63.033mm/7.320°였다.
공통 원본 위치 기준 +5mm 오차는 65.349mm로 개선되지 않았다. 두 조건 모두 0.05초
L_Knee–기타 root body 접촉과 약 107.8° 하체 raw 이탈이 남았으며 24step 적용 장력은 0N이었다.
source gap은 보정된 관통 깊이나 native cooked clearance가 아니다. 초기 배치 개선과
전체 장면 무겹침·자세 유지·feedback·연주 성공을 구분한 설명이 원자료와 일치한다.

[보호 파일 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/protected_validation.json)는 기존 87파일 metadata와 2026-08-19 49파일 SHA 불변을 기록한다. 해당 전후 기준 자료는 부모의 보존 검사 결과이며 리뷰어가 별도 이전 스냅샷을 만든 것은 아니다.
물리 run의 source hash는 실행 당시 증거다. 부모가 후처리 수정·계획 체크 갱신 뒤 source snapshot/manifest를 정리했고, 리뷰어는 최종 14개 manifest SHA가 현재 파일과 모두 일치함을 확인했다. [최종 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/source_snapshot_validation.json)도 두 물리 run의 runtime source hash 보존과 일치를 기록한다. 이후 검수 링크·변경 인덱스 갱신은 문서 정리이며 이전 run 증거를 변경하지 않는다.
리뷰어는 구현·원자료·기존 산출물을 수정하지 않았고, 요청된 이 review.md만 새로 작성했다.
