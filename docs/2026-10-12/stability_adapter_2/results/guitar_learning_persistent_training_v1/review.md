# 실제 학습·분석 최종 독립 검수

요약 판정: **문제없음**. 실제 학습 결과, 분석 집계, 권장 그림 v2, README의 주요 수치와 주장 범위가 일치한다. 현재 검수 범위에서 수정해야 할 오류는 발견하지 않았다.

## Critical

없음.

## Warning

없음.

## Suggestion

없음. 사전 검수에서 제안한 discarded 수 대조는 `analyze_learning.py:83`에 반영됐으며 실제 두 값은 모두 0, `counts_consistent=True`다.

## 실제 원자료 대조

- `run_v1/report.json`은 completed=True, stopped=wall_budget, failure=None이다. 1,855.2455초 동안 추가 14 업데이트, 28,672전이를 반영했다. canonical 결과에 연결된 core_report.json의 SHA가 실제 파일과 일치하고 core 및 persistent 감사도 모두 통과했다. 시간 제한은 기존 코드가 업데이트 시작 전에 검사하므로 마지막 배치 때문에 1800초를 넘은 종료를 오류로 보지 않는다.
- 종료된 `transitions.jsonl.gz`를 독립적으로 전부 스트리밍했다. 3,584행 × 8환경 = 28,672전이, 완료 episode 320개, 압현 후보·물리 실패·50/100ms 매칭·목표음 유지 모두 0으로 집계됐다. 양발 접촉 28,672회, 삼중 지지 25,704회(89.6484375%)로 분석과 일치한다.
- 첫/마지막 5 업데이트의 왼손 onset 직전 표본은 각각 112개이며 19.846475→19.330089mm다. 오른손 sweep 표본은 1120/1136개이며 55.156293→54.659579mm다. 서로 다른 표본 수와 기하 proxy를 README가 구분하고 있어 실제 압력이나 음악 성공으로 과장하지 않는다.
- 328개 준비 후 상태를 원자료에서 다시 계산했다. 모든 준비에서 주요 3부위 지지와 양발 접촉을 확인했다. 같은 worker의 첫 준비를 기준으로 기타 위치 최대 0.422133mm, 회전 0.001548694rad, 발 위치 최대 0.054810mm, q 최대 0.000983298rad로 보관된 preparation 분석과 일치한다. 회전 비교는 정규화되는 scipy Rotation을 사용한다.
- 8개 worker 최종 lifecycle 각각 create_sim=1, create_env=1, load_asset=2, destroy_sim=1, episode_index=40, closed=True, forbidden_calls_total=0이다. 각 worker의 41개 reset 증거 SHA도 대조했다. 전체 328회 준비와 완료 320 episode의 차이는 마지막 부분 episode이며 폐기한 rollout이 아니다.
- 원 resources.jsonl로 자원 분석을 다시 계산해 전체 결과가 일치함을 확인했다. 60초 이후 같은 8개 worker의 현재 RSS는 4.924194336→4.924446106GiB, OLS +0.000957631GiB/시간이다. 약 31분 관측과 이전 약 1시간 관측의 차이, RSS/PSS/peak 구분, 장시간 누수 부재를 증명하지 못한다는 제한이 문서에 명시돼 있다.
- 기존 checkpoint SHA, initial 모델 일치, 누적 업데이트 25→39, 최종 가중치 유한성을 직접 확인했다. 분석의 모델·optimizer·계약·cost weight·전체 RNG 복원 결과도 모두 True다.

## 그림·보존·범위 확인

- 권장 `training_progress_v2.png`를 직접 열어 확인했다. 범례가 KL 표본을 가리지 않으며 제목·누적 업데이트·거리 단위·0% 성공·메모리 관측 길이가 원자료에 맞는다. 이전 약 60분과 새 약 31분 곡선은 각 관측 구간까지만 표시된다. PDF는 같은 그림 객체에서 생성된다.
- 네 후처리 사전 입력 목록 총 381개 항목을 현재 파일 SHA와 대조해 차이 0개였다. source_run_v1 73개 보관 파일 및 그 목록의 활성 Python 소스에도 차이가 없었다. README의 실제 절대 경로 링크 11개는 모두 존재한다.
- 분석은 현재 고정 첫 단음의 연속 학습 관찰이다. seed 반복·별도 결정적 정책 평가·좌우 개별 성공 확인·실제 현 압력/음향·Root 자유 균형을 검증한 것으로 설명하지 않는다. 기존 제어기 위 39축 공동 정책이라는 설명도 구현과 일치한다.
- 새 학습·중단·소스/모델/원자료 수정은 하지 않았다. 이 검수 기록 외의 산출물은 생성하거나 수정하지 않았다.

이 검수는 학습과 분석 내용에 대한 판정이다. root 담당 최종 source_final·artifact_inventory·final_verification의 생성 및 봉인은 이 문서 작성 이후 별도로 수행한다.
