# 이번 단위의 변경 파일

기존 원본 코드/자산/이전 결과를 보존했다. 아래 줄 번호는 실제1-based다.

| 절대 파일 경로·줄 | 역할 |
|---|---|
| [/home/ajou/yigyu/3/stability_adapter_2/compare_right_support.py:60](/home/ajou/yigyu/3/stability_adapter_2/compare_right_support.py:60) | 후처리 입력해시를실제raw/source 의존성으로한정 |
| [/home/ajou/yigyu/3/stability_adapter_2/RIGHT_DISTAL_FINE_INITIAL_POSE.md:50](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_DISTAL_FINE_INITIAL_POSE.md:50) | 미세 초기각 계획과1초 판정 |
| [/home/ajou/yigyu/3/stability_adapter_2/search_hand_support.py:57](/home/ajou/yigyu/3/stability_adapter_2/search_hand_support.py:57) | fine-distal 한 좌표 sweep/기존 coarse 보존 |
| [/home/ajou/yigyu/3/stability_adapter_2/compare_joint_hold.py:17](/home/ajou/yigyu/3/stability_adapter_2/compare_joint_hold.py:17) | 명시0.5초4run 비교 옵션/기본6run 보존 |
| [/home/ajou/yigyu/3/stability_adapter_2/plot_right_distal_fine.py:1](/home/ajou/yigyu/3/stability_adapter_2/plot_right_distal_fine.py:1) | 저장 결과의 비교 그래프와source pose |
| [/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:671](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:671) | 메인 계획29절 |
| [/home/ajou/yigyu/3/stability_adapter_2/README.md:54](/home/ajou/yigyu/3/stability_adapter_2/README.md:54) | 현재 결과/다음 진단 기준 |
| [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:626](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:626) | 누적21절: 이미지와설명 |
| [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/README.md:10](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/README.md:10) | 초기/PI 수치와한계 |
| [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/review.md:6](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/review.md:6) | 독립 변경 검수 |

## 초기 입력

- [/home/ajou/yigyu/3/stability_adapter_2/trials/right_distal_fine_v1/candidate_01.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/right_distal_fine_v1/candidate_01.json:1)
- [/home/ajou/yigyu/3/stability_adapter_2/trials/right_distal_fine_v1/candidate_02.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/right_distal_fine_v1/candidate_02.json:1)
- [/home/ajou/yigyu/3/stability_adapter_2/trials/right_distal_fine_v1/candidate_03.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/right_distal_fine_v1/candidate_03.json:1)
- [/home/ajou/yigyu/3/stability_adapter_2/trials/right_distal_fine_v1/reference.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/right_distal_fine_v1/reference.json:1)

## 비교·진단 원자료

- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/search/search.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/search/search.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/comparison.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/comparison.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/comparison_v2.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/comparison_v2.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/joint_hold/comparison_05s.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/joint_hold/comparison_05s.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/joint_hold/comparison.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/joint_hold/comparison.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/decision.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/decision.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/contact_drift_observations.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/contact_drift_observations.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/verification.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/verification.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/missing_half_regression.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/missing_half_regression.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/historical_manifest_validation.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/historical_manifest_validation.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/source_manifest_search.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/source_manifest_search.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/source_manifest.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/source_manifest.json:1)

- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/comparison_v3.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/comparison_v3.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/postprocessing_dependency_validation.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/postprocessing_dependency_validation.json:1)

- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/media_validation.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/media_validation.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/verification_v2.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/verification_v2.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/comparison_v3_repeat.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/comparison_v3_repeat.json:1)

## 실행별 원자료

short4개·PI6개의 각run은 아래 절대 경로에서 report/trace/states/contacts/leg_torques(PI는controls 포함)를1줄부터 확인할 수 있다. report/원자료의 source hash와명령 파일이 입력을 연결한다.

- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/joint_hold/hold_05s/off/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/joint_hold/hold_05s/off/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/joint_hold/hold_05s/on/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/joint_hold/hold_05s/on/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/joint_hold/hold_1s/off/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/joint_hold/hold_1s/off/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/joint_hold/hold_1s/on/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/joint_hold/hold_1s/on/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/joint_hold/short/off/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/joint_hold/short/off/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/joint_hold/short/on/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/joint_hold/short/on/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/short/candidate_01/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/short/candidate_01/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/short/candidate_02/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/short/candidate_02/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/short/candidate_03/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/short/candidate_03/report.json:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/short/reference/report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/short/reference/report.json:1)

계획·settings·코드 이외 산출물은 이 결과 폴더에 두었다. 매체는 artifacts의 두PNG와 manifest이며 source는 변경 전 사본, source_final은 최종 사본이다. 최초 비교·4run 비교·수정 전 매체도 별도 보존한다.

## 전체 생성 파일 목록

[절대 경로·텍스트 시작 줄·분류 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/right_distal_fine_v1/file_inventory.json:1)은 원자료·실행기록·보존사본까지 포함한다. PNG는 줄 번호가 없는 매체다.
