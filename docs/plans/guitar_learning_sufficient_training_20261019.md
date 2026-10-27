# 단음 A 충분한 추가 학습과 전후 평가

사용자 요청: 충분한 학습을 실제 진행하고 결과를 분석한다. 현재 회복 시연은0건이므로 이번 실행은 검증된 현재 단음 A 보상·관측·행동 계약을 유지하는 추가 PPO 학습이다. R1/R2·회복 과제·두 음·전곡 성과로 설명하지 않는다.

1. [x] 현재 내부화 코드/입력을 별도 복사·읽기전용 실행 view에 고정한다. 기존 평가용 출처 이관 B32의 학습 사용을 이번 사용자 요청에 따른 새 결정으로 기록하고 원 manifest는 보존한다. 8환경1업데이트 연결과 모든 종료 감사를 통과했다. 실제1,920전이 반영·counter32→33·성공7/8·물리0·9개runtime감사·persistent/teacher/core·입력 재해시 통과(training_smoke_validation_v1.json). 원 캐시 경로 쓰기 실패는 업데이트0으로 보존하고 별도 task cache로 보완했다.
2. [x] 같은20 seed의 결정적/탐색 평가를 기준 모델에 수행한다. 단음 A·8환경·H240에서 추가128업데이트(245,760전이·1,024에피소드 목표, 최대4시간)를 실제 진행한다. 학습/물리/자원 로그와16회 간격 checkpoint를 보존한다. 물리·무결성/학습률 고갈 같은 실질적 실패는 원자료를 보존하고 조치하며, 성공률이 낮다는 이유만으로 조용히 실행을 성공으로 바꾸지 않는다.
3. [x] 반영 전이·에피소드·유지/해제·준비 접촉·물리 비용·KL/LR/std/BC·실패 분포와 앞뒤 구간을 분석한다. 마지막과 중간 후보를 같은 평가 protocol로 검증하고 개선/정체를 구분한다. 독립 검수·실행/모델/무결성·종료 상태를 문서화한다.

PPO/탐색/BC/신경망 크기는 원 strict identity를 유지한다. Root만 고정·하체 유한 제어·105/97/8·자유 기타·중력ON·스트랩OFF·원 gain/제한/안전을 유지한다. 기타 직접 힘/부착/상태 덮어쓰기를 사용하지 않는다. 평가 seed 변화는 초기 자세 다양화나 독립적인 물리 초기조건을 뜻하지 않는다.

자료 위치: docs/2026-10-12/stability_adapter_2/results/guitar_learning_sufficient_training_v1. 명시 학습 사용 결정·현재 source/외부 입력 snapshot·namespace argv·설정·PID·학습 원자료·전후 평가·보고서를 함께 남긴다. 기존 봉인 소스/자료는 수정하지 않는다.

추가 검증(중간 결과 검토 후, 최종 모델 생성 전 고정): persistent-reset의 초기 pose/velocity/target은 같지만 contact_history 차이를 확인했으므로 기준 B32와 최종 모델의 stochastic fresh_process 각6회(seed101/103/107/109/113/127)를 추가한다. 매 case 새 interpreter/native 장면·case local index0·초기상태 전체/contact_history·PID·source/runtime를 검사한다. 기존20회는 보존하고, 새6쌍은 반복이력 영향을 줄인 진단이며 통계적 독립성/일반화/숨은 캐시 동등성으로 확대하지 않는다.

실제 본학습 완료(10/20 01:05KST): 추가128회/누적160회,245760전이,1024에피소드529성공·물리0. stopped=updates_complete,wall9654.138초(선행감사제외). training_long_validation_v2.json passed:2389input·9runtime·journal0discard/source변화0·coreSHA·128update파일. 최종SHAae9770470cdbd7141bf47c277a4a81757a753841beab18419c60de31f2e9a7e6. 최종det20/stoch20/fresh6 평가를시작했고아직결과대기다.

최종 완료: 최종det20/20·stoch11/20·fresh4/6,기준20/20·8/20·3/6,중간20/20·11/20. 별도평가총132회와학습1024회를분리했다. 모든native/검증세션정상종료,active진입점없음·8workerexit0. 최종검증v2/verification/독립검수FINAL_REVIEW통과. README/analysis_FINAL·상세·학습곡선·완료seal저장. 후반완만한개선이나준비접촉취약성과품질tradeoff가남음;R1/R2/회복학습미적용.
