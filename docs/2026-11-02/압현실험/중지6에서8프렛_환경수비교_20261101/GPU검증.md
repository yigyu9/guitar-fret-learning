# 새 6→8 학습 실행 경로 확인

2026-11-01 21시대 실제 RTX 4070 Ti에서 확인했다. 검증용 모델과 본 실험 모델은 분리했다.

| 검사 | 실제 설정·결과 | 근거 |
| --- | --- | --- |
| 새 목표 물리 참조 | 두 음 정시 시작·각1.5초 유지, accepted=true | validation/reference_native_v3/report.json |
| 새 학습·저장 | large·1024·H32, 2회·65,536경험 | learning_v1/jobs/smoke_train2/J/report.json |
| strict 재개·저장 | 동일 계약·환경·난수, 추가1회·32,768경험 | learning_v1/jobs/smoke_resume1/J/report.json |
| 최초32에피소드 평가 | 실패 포함 분모·원장·보상 성분 합계·6/8시간표 확인 | learning_v1/jobs/s7_t98304_smoke_mean_n32/analysis.json |
| 실제 정책 영상 | 손·전신, 4환경, 정책 불변·정리 확인 | learning_v1/jobs/smoke_render/report.json |

모든 실행 보고서는 completed/lifecycle_verified=true이고 입력 변경·정리 오류가 없다. 영상은 1280×720, 217프레임·약7.234초이며 전신 중간 프레임을 직접 확인했다. GPU 검증용 모델은 3회 학습이므로 압현 달성0/32이며 이를 학습 성과로 제시하지 않는다.

검증 이후 seed7의 본 실험을 fresh로 시작했다. seed17도 같은 예산으로 학습하며 최대 각2,097,152경험까지 진행한다. 평균32 중간 평가와 최고·마지막 모델의 평균128 반복·탐색32·손/전신 영상이 뒤따른다. [자동 진행](learning_v1/진행상황.md)과 [자동 연결 상태](pipeline_v2.json)는 실행 중 갱신된다.

벤치는 원래6→7 workload, 참조는 수동으로 찾은6→8 경로, 본 실험은 새 정책의6→8 학습이다. 이 세 가지의 결과를 구분한다.
