# 도구 이전과 구형 기타 프로젝트 보관

사용자가 `guitar_learning/tool`에 필요한 도구를 이전하고 기존 여섯 디렉토리를 보관 정리하도록 지시했다. 현재 학습의 물리·관측·행동·보상·checkpoint 계약은 유지한다.

- [x] 현행 안내·규칙·외부 도구 closure 조사, 수정 대상 원본 보관.
- [x] 곡 등록·압현/타현 데이터·계획·입력 감사·타임라인 도구를 내부화하고 실제 입력 결과를 대조한다.
- [x] 현행 진입점과 문서 링크를 새 도구/내부 자산으로 바꾼다.
- [x] 원본 tree inventory를 기록하고 fret/full/strike/stability_adapter/stability_adapter_2/tab2body를 archive/legacy_guitar_20261019로 이동한다.
- [x] 이동 전후 파일·symlink 보존, 옛 경로 부재, 외부 읽기/import 차단, 도구·학습 입력 검증을 확인한다.
- [x] change-reviewer 검수와 결과 기록을 완료한다.

보존: 원본과 기존 실험 기록의 내용을 고치지 않고 디렉토리를 이동한다. 최상위 옛 경로를 되살리는 symlink는 만들지 않는다. 필요 시 과거 환경을 재현하는 방법과 원래/보관 경로 대응을 기록한다. 기존 g.l/archive 및 data·docs·paper·Isaac Gym·tab2fingermapping는 보관 대상으로 옮기지 않는다.

검증: 새 도구는 임시 곡 복사본에서 생성·등록·감사·시각화를 수행한다. 곡 데이터와 과거 checkpoint/결과는 덮어쓰지 않는다. 현재 내부 native provenance와 저장 학습 입력을 검증하고 별도 프로세스에서 보관본 접근을 막아 이전 폴더 의존 여부를 확인한다.

기록: docs/2026-10-12/stability_adapter_2/results/guitar_learning_tools_archive_v1/.
