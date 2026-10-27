# guitar_learning 구조 정리

현행 실행은 [README](/home/ajou/yigyu/3/guitar_learning/README.md), 입력·진단 도구는 [tool](/home/ajou/yigyu/3/guitar_learning/tool/README.md)를 따른다. 학습·물리·보상·관측/행동·엄격한 checkpoint 검증을 유지하며 소스 위치와 공통 기능을 정리했다.

| 항목 | 이전 | 이후 |
|---|---:|---:|
| 활성 Python | 394 | 373 |
| 루트 Python | 88 | 79 |
| 구현 Python | 270 | 253 |
| 검사·검사 도우미 Python | 124 | 120 |
| Python 줄 수 | 44,890 | 42,162 |
| 활성 실행 캐시 | 769개/6,597,476bytes | 0개 |

전체 물리 파일 수와 활성 소스 수는 다르다. 원형 snapshot·자산·과거 SHA 검증 원문은 보존했다. 보관은 삭제와 구분하며 현재 코드는 archive를 import하지 않는다.

## 변경

- 대체된 runtime V1, 감사/모방 평가/단일환경 CLI, anchored·독립 단음풀 실험을 관련 검사와 함께28파일(24Python) 보관했다. [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261019_retired_experiments/manifest.json).
- 진단·운영 도구6개를 tool로 이동하고 렌더helper를 분리했다. 공용 의존성 판별은 기존recording 함수를 직접 사용한다. [도구 이동과 비교](tool_cleanup.json).
- 기존score reader를 공통 기반으로 재사용해 planner의 중복628줄을 제거했다. 학습 reader 원문과 planner 생성 로직은 보존했다.
- 현행 검사들이 재사용하던 단음 계약fixture를 별도 도우미로 분리했다. [원래 계약과 양손 전체 필드 동일성](fixture_parity.json).
- 실행 안내·AGENTS·계보 링크·보관 색인과 초기 원구현 연결을 정비했다. [변경 파일과 원래/현재 SHA](changed_files.json).

## 검증과 보존

최종 [전체 회귀](final_tests_v2.log)는 680개 모두 통과했다. 검사 동안 [활성373소스](final_source_manifest_v2.json)는 바뀌지 않았다. 도구 관련 검사는Python3.8/3.13에서 통과했고7곡 전체 계획JSON·학습 reader 왕복·frozen audit 결과가 원본과 같았다. [실제 native12물리 스텝](native_parity.json)은 전후 JSON의 모든 필드가 정확히 같다. 이는 연결·동등성 검사이며 새 연주 성능을 주장하지 않는다.

변경 전449원문과 보관28파일의 SHA, native190파일·도구18파일의 현재 SHA, historical CAS2,105객체를 확인했다. 기존 historical 버전·default SHA는 유지했고 누락·미참조 객체는0이다. [백업 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261019_before_structure_cleanup/manifest.json) · [원문 등록](historical_preservation.json) · [최종 검증](verification.json).

독립 change-reviewer의 tool README SHA 지적을 수정했고, 추가된 검사fixture 분리까지 재검수하여 남은 문제없음 판정을 받았다.

## 중간 검사 기록

- 변경 전717검사 중1실패는 생산pin이 내부 자산을 정확히 기록했는데 검사에서 옛 경로를 기대한 문제였다. 현재 경로와 정확한SHA를 함께 대조하도록 검사만 보완했다. [기준선](baseline_tests.log) · [진단](baseline_reward_pin_diagnostic.log) · [보완 후13검사](evidence_regression_final.log).
- 첫 정리 후 회귀는 보관한 검사fixture를 다른 검사들이 재사용하던 참조 누락으로 중단했다. 현행 환경 기반 공통fixture로 분리하고 별도 복원 작업 공간의 원fixture와 정확히 대조했다. [초기 중단 로그](final_tests.log) · [보완 후17검사](fixture_regression.log). 과거 원문을 현행 코드에서 import하지 않는다.
- native 첫 시도는 기본Torch 확장 캐시의 쓰기 제한으로 실패했다. 쓰기 가능한 임시 캐시에서 재실행해 전후 비교를 완료했다. 기존 Isaac 경고는 원형대로 남겼다.

기존 실행 원자료·성공/실패 모델과 이전 snapshot은 덮어쓰지 않았다. 공통runner를 다시 설계하거나 접촉 회복 보상을 변경하는 작업은 포함하지 않았다.

[독립 최종 검수](review.md)에서 전체680검사와373소스 동결 일치를 재확인했다.
