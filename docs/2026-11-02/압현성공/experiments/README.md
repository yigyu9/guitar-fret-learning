# 압현 연구 결과와 재현 자료

현재 결과를 확인할 때는 첫 행부터 읽는다. 아래 폴더는 완료한 연구의 원문·설정·입력·로그·분석을 함께 보존한 위치다. 폴더의 버전 번호가 현행 기본 학습의 실행 버전을 뜻하지 않는다.

| 구분 | 실험 | 읽을 자료 | 해석 |
| --- | --- | --- | --- |
| 최신 완료 결과 | [target_transition_v2](target_transition_v2/README.md) | [600회·12평가](target_transition_v2/runs/comparison_v1/RESULTS.md) | 평균 행동의 두 음 전환0/32, 확률 행동16/32·10/32. 안정적인 전환 학습은 미달 |
| 이전 전환 진단 | [virtual_transition_v1](virtual_transition_v1/README.md) | 판정 오류를 발견하고 기존 실현성 주장을 정정한 기록 | 수정 전 동시 성공 수치로 실제 전환을 입증하지 않음 |
| 준비 조건 비교 | [natural_press_v3](natural_press_v3/README.md) | 목표 노출·대기/준비 E0~E4 비교 | 특정601열 연구 계약; 기본557열 J와 구분 |
| 구조·범위 확장 | [structured_press_v2](structured_press_v2/README.md) | A/B/C 구조·7시간 연구·손가락별 비교 | 팔 지원 조건·전체33축·난수·평가 방식을 구분 |
| 초기 탐색 비교 | [exploration_lr_sequence_v1](exploration_lr_sequence_v1/README.md) | 탐색·학습률·순차 gate 비교 | 이전 구조의 실패 근거 |

## 현재 실행과 보존 자료의 경계

기본 새 학습·평가·영상 명령은 [학습 안내](/home/ajou/yigyu/3/guitar_learning/README.md)를 따른다. 연구 도구는 [tool 안내](/home/ajou/yigyu/3/guitar_learning/tool/README.md)에서 선택한다. 이 디렉토리의 소스·체크포인트·catalog·preflight는 해당 실행 시점에 봉인된 자료이므로, 현재 코드에서 옛 명령을 실행하기 전에 source/계약 일치 여부를 확인해야 한다. 검사에 실패했다고 과거 input pin을 현재 값으로 덮어쓰지 않는다.

| 하위 위치 | 역할 |
| --- | --- |
| `tools/`, `source_*`, `before/` | 당시 도구·원문·비교 근거; 기본 학습 코드와 구분 |
| `runs/`, `validation/`, `geometry/` | 학습/평가 결과와 실행·도달 가능성 검증 원문 |
| `RESULTS.md`, `ANALYSIS.md`, report·요약 | 결과를 이해하는 입구; 원시 로그 전부를 대체하지 않음 |
| 상위 [video](../video/) | 공개 MP4; 실험 이름으로 찾기 |

새 실험은 새 디렉토리를 사용한다. 이 위치는 봉인 경로와 기존 링크를 유지하기 위해 일괄 이동하지 않았다. 완료 계획의 분류는 [계획 안내](/home/ajou/yigyu/3/docs/plans/README.md), 정리·삭제 근거는 [maintenance](/home/ajou/yigyu/3/docs/maintenance/README.md)를 따른다.
