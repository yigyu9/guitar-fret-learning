# From Audio to Full-Body Guitar Performance with a Freely Moving Instrument

작업 제목으로 채택한 논문의 한국어 본문 초안이다. 오디오 해석과 연주 계획, 왼손 압현·오른손 타현,
공통 음악 시간축, 자유 기타의 지지와 상체 제어를 하나의 연구 흐름으로 서술한다.
각 장을 본문으로 읽을 수 있도록 연구 동기, 방법, 실험 조건, 관측 결과와 해석을 연결하였다.
내용을 충분히 채운 뒤 핵심 주장에 맞춰 줄이는 방식으로 작성한다.

기타 연주 제어와 물리 시뮬레이션을 처음 접하는 독자도 문제와 방법의 필요성, 결과의 의미를 따라올 수 있도록 작성한다. 용어를 처음 사용할 때 설명하고, 방법의 직관을 제시한 뒤 수식과 구현 조건으로 구체화한다. 상세 작성 기준은 [논문 작성 원칙](/home/ajou/yigyu/3/paper/AGENTS.md)에 둔다.

본문 초안의 자료 기준일은 2026-10-12다. 현재 기록은 전신 휴머노이드 장면과 상체 81관절 보정 학습을 다루며,
root와 하체는 고정한다. 자유 기타의 지속 양손 연주 성공은 아직 입증되지 않았다.
최근 학습·물리·병렬 수집 검증과 실제 음악 성능을 구분해 읽는다.

초기 자세의 최신 별도 자료는 2026-10-17의 [실용 V3 후보](/home/ajou/yigyu/3/paper/initial_pose/current_v3/README.md)다. 이 후보는 Root만 고정하고 하체를 유한 제어하며, 다섯 개별 시험을 통과했다. 아래 본문 초안의 81관절·하체 고정 조건과 구분한다. 최신 결과를 반영하는 본문 전체 개정은 아직 수행하지 않았다.

## 기본 목차

| 부분 | 내용 |
|---|---|
| [Abstract](/home/ajou/yigyu/3/paper/00_abstract.md) | 문제, 제어 접근, 평가 범위와 주요 관측 결과 |
| [Introduction](/home/ajou/yigyu/3/paper/01_introduction.md) | 연구 동기, 문제 정의, 접근과 기여 |
| [Related Work](/home/ajou/yigyu/3/paper/02_related_work.md) | 기타·악기 동작 연구의 방법과 조건, 현재 문제와의 관계 |
| [Methodology](/home/ajou/yigyu/3/paper/03_methodology.md) | 오디오·운지·기술 prior·공동 음악 판정·상체 보정·자유 기타 물리 |
| [Experiment](/home/ajou/yigyu/3/paper/04_experiment.md) | 평가 조건, 측정 지표와 비교 실험 절차 |
| [Result](/home/ajou/yigyu/3/paper/05_result.md) | 확인된 수치와 실패 분석, 실험별 해석 범위 |
| [부록](/home/ajou/yigyu/3/paper/06_appendix.md) | 좌표·관절·제어·학습 설정, 그림·영상과 재현 자료 |

작성 보조 자료는 [근거 색인](/home/ajou/yigyu/3/paper/evidence_index.md)과
[작성 메모](/home/ajou/yigyu/3/paper/writing_notes.md)에 모았다.
근거 색인은 본문과 원자료의 대응을, 작성 메모는 후속 실험·그림 배치·보류 아이디어를 담는다.
제공된 과거 DIGIT 원고의 활용과 변경 사항은 [과거 원고 대조](/home/ajou/yigyu/3/paper/legacy_draft_review.md)에 기록했다.

## 초안을 읽는 기준

Experiment에는 실험 조건과 검증 방법을, Result에는 실제 관측 결과와 해석을 기록한다.
설계 제안, 실제 구현, 측정된 성능을 구분한다. 미실행 비교와 추가 작성 계획은 작성 메모에 둔다.
본문의 원문 링크는 작성과 검증을 위한 근거이며, 투고본에서는 필요한 인용·표·부록으로 정리한다.

연구 흐름은 오디오에서 시작하지만, 현재 대표 자유 기타 실험은 등록된 곡 번들과 체크포인트를 사용한다.
오디오 전사 오류를 포함한 전체 시스템의 성능은 별도 실험 항목으로 남겨두었다.
전신 장면을 사용한다는 사실, 상체 정책의 제어 범위, 모든 관절의 자유 운동은 서로 구별한다.

## 연구 자료

- [현재 초기 자세 — 값·이미지·영상](/home/ajou/yigyu/3/paper/initial_pose/README.md): 기존 035 설정·native v14·실용 V3의 개별 시험 결과와 정확한 입력·준비 후 상태를 모았다.
- [초기 자세의 동작 실험](/home/ajou/yigyu/3/paper/initial_pose/archive/browse/experiments_README.md): 하체 고정 조건에서 왼손 해제·이동·재접근, 오른손 반복 동작과 초기 위치 변화를 검증한 자료다. `initial_pose/archive`에 보관하며, 과거 실행 기록의 원문은 보존한다.
- [초기 자세 과거 기록](/home/ajou/yigyu/3/paper/initial_pose/archive/README.md): 이전 하체 고정 자료와 하체 해제 초기 실패를 보존한다. 최신 상태는 [front_facing_ready_v1 WORK_STATE](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/WORK_STATE.md)의 맨 위를 따른다.
- [전체 연구 계획](/home/ajou/yigyu/3/master_plan/README.md)
- [현재 파트 계획과 진행 기록](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md)
- [실제 최신 pilot의 네트워크와 보상](/home/ajou/yigyu/3/docs/2026-10-12/Meeting/06_StabilityAdapter2_현재_학습구조.md)
- [관련 연구 분석](/home/ajou/yigyu/3/docs/related_work_analysis/README.md)
- [아이디어 정리 계획](/home/ajou/yigyu/3/docs/plans/research_archive_20261012.md)

원자료·학습 로그·체크포인트는 기존 위치에서 참조한다. 초기 자세 자료에는 값·이미지·영상 사본과 원본 출처를 함께 보존한다.
