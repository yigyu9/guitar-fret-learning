# v8 GPU 왼손 장기 학습 — 진행 중

사용자 요청으로 현재 v8을 large·1024환경·H32·seed7에서 fresh2000업데이트,65,536,000전이 예산으로 학습하고 있다. 기본곡05_BN2-131-B_solo의67음을 사용한다. 이전 smoke8+1회와 v6 장기 결과는 이 예산에 합산하지 않는다. 시작 시각은2026-10-22 22:52:56 KST이며 현재 속도 기준 학습 약6~7시간, 후속 평가·영상에는 추가 시간이 필요하다.

손가락 움직임 비용0, 전체 native 범위·독립 누적제어·PD·물리·성공·안전 기준을 유지한다. 현재438 Python 원문은 training_source_manifest.json과source_training/에 SHA 대조해 보관했다. 학습 중 이 소스는 변경하지 않는다. 평가·검산·감시 보조 도구는 이 새 결과 디렉토리에만 추가한다.

- [실행 설정과 PID](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/launch.json)
- [진행 기록](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/progress.jsonl)
- [작업 계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_long_training_v8_20261022.md)
- [직전 v8 구현·짧은 검증](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_targeted_finger_learning_v1/README.md)

주 결과는 `/media/ajou/새 볼륨1/guitar_learning_runs/20261022_v8_long/` 아래 새 경로에 저장한다. 프로젝트 SSD 여유가 적어 기존 데이터를 지우지 않고, 외장 저장소의 새1MiB 쓰기/fsync/rename/읽기SHA 검사를 통과한 뒤 시작했다. 이는 디스크 전체의 영구적인 건강을 인증하는 시험은 아니다. 원래 학습·영상·Git 자료는 변경하지 않았다.

`train2000`에는 설정·초기/마지막 모델·100회 간격checkpoint·음별 원장·원자료·수집/PPO/자원 로그가 저장된다. 학습은 별도 프로세스에서 계속되며, 자연스러운 기타 이탈은 학습 데이터에 포함한다. 저장소 오류·진행 정지·소스 변동은 별도로 감시한다.

학습 정상 종료 이후 전체 CRC/EOF·전이 수·438소스/입력SHA·3331 curriculum·모델/두Adam 유한값을 확인하고, 별도2000→2001 strict resume1회를 검산할 예정이다. 후속 재개32768전이는 fresh 예산과 합산하지 않는다. 초기/500/1000/1500/2000 모델의 동일1024 첫 에피소드를 평가하며, 각 모델의 저장된 curriculum은 그대로 복원한다. 평균 달성음→안전 완료수→최근순으로 평가된 학습 모델 중 대표를 고른다. 초기 모델은 후보에서 제외한다.

대표 모델의 실제 자세 캡처로 전신·손60fps 영상을 만들며 재생 중 새 물리는 진행하지 않는다. 실행 완료·원자료 검증·자동 수치 집계와 실제 연주 성과/영상의 시각 검수를 구분한다. 이 문서 작성 시에는 학습이 진행 중이며 장기 결과·전곡 성공·자연스러움 개선을 아직 주장하지 않는다.

## 실행 중 확인한 내용

첫100업데이트(3,276,800전이·확정3200행·100gzip member)의 CPU prefix 검산을 통과했다. source438/입력SHA·저장본/두Adam 유한값·3331curriculum 재생도 확인했다. 이는 확정 구간의 검증이며 전체2000회 완료·전체파일EOF·최종GPU close나 전곡 성능 평가를 뜻하지 않는다. [첫100회 검산](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/verification_prefix_000100.json).

원래 미사용 Git 임시 pack 한개(3,644,790,537바이트)는 두차례 열린 handle없음·연결 index없음·stat동일 확인 후 외장 storage_backup으로 전체복사/fsync/재읽기SHA 대조해 이전했다. 유효pack/index/ref/staging과학습자료는변경하지않았고Git연결검사는exit0이다. storage_relocation.json에원래경로와복구가능한backup/SHA를기록했다. 프로젝트여유는이전직후약3.5GiB다.

현재 monitor_v2가 실제 학습 PID/명령/시작시각을검증해감시한다. after_training.py는별도프로세스에서정상학습종료marker를기다리고있으며,검산→strictresume1→로그분석→5개checkpoint고정평가→대표전신/손영상을순서대로실행하도록연결했다. [후처리대기설정](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/postprocessing_launch.json). 오류가나면원자료를보존하고실패단계를기록한다. 자동집계후에도결과의독립검수와영상시각검토는별도다.
