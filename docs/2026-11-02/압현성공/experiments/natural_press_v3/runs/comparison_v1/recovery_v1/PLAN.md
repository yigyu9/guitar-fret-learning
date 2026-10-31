# 고정 비교 후보의 남은 실험 계속 실행

원본 후보 E1/E2와 학습 소스·물리·PPO·평가·원본 source_seal은 변경하지 않는다. seed7 E1 누적200 블록의 KLGuard 실패를 성공으로 바꾸거나 재시도하지 않는다. 완료된 최초100 모델과 실패한 추가 블록을 구분한다.

원래1400회 계획 중 완결된 학습 블록은600회이며 E1의 실패 블록은 별도 부분 전이를 남겼다. 남은 승인 작업은 seed7 E2 추가100회(누적200), seed17 E0/E1/E2 각각100+100회로 총700회다. 완료될 경우 완결 블록 합계는1300회이며 원래1400회 전체 성공이라고 표현하지 않는다. 실패 블록의 실제 commit은 보고서에서 별도 기록한다.

- [x] 원본 실행기·현재 중단 상태·고정 후보 확인
- [ ] 실행 전 원본 progress/진행상황/RESULTS를 before 사본과 SHA로 보존
- [ ] 원본 입력 SHA와 추가 continuation 코드 SHA 봉인 확인
- [ ] seed7 E2 누적200 실행·정렬/v9 최초32 평가
- [ ] seed17 E0/E1/E2 각각100·200 실행·평가
- [ ] 조건100 실패 시 같은 조건200은 prerequisite 실패로 건너뛰기
- [ ] 선택 시 완료된 seed7 E1/E2의100/200 모델 최대4개만 추가 영상 생성
- [ ] failed/skipped 블록을 남기고 finished_with_failed_blocks로 최종 기록

계속 실행기는 원본 run_study 모듈의 HERE를 유지하며 block/run_job/progress/기존 영상 공개 함수를 재사용한다. 원본 RESULTS.md·summary.json은 보존하고 이후 집계는 recovery_v1/RESULTS.md·summary.json에 기록한다. 원본 progress.json/진행상황.md는 현재 상태를 보여주도록 갱신한다. 마지막 예상 종료는 실제 finished_at으로 바꾼다.

개별 블록 실패는 원본/추가 소스 SHA가 모두 그대로이고 child 종료·GPU 비점유를 확인한 뒤에만 기록하여 다음 독립 조건을 진행한다. 입력 변경·남아있는 GPU 프로세스·출력 충돌은 전체 중단 사유다. 원본 및 새 출력에 덮어쓰지 않는다. 영상 오류는 학습 실패와 별도로 기록한다. 이 파일은 추가 승인 계획이며 원본 PLAN.md를 수정하지 않는다.

CPU 테스트 후 주 실행자가 다음을 사용한다. 이 문서 작성은 GPU 실행을 시작하지 않는다.

```bash
python -B recovery_v1/continue_remaining.py
# 완료된 후보 영상도 만들 때만 --render 추가
```
