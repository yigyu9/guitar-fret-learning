# 현행436 장기 학습 상태

사용자가 장기 학습·로그/결과 분석·좋은/마지막 checkpoint 영상을 요청했다. 계획은 `docs/plans/guitar_learning_long_training_v4_20261022.md`다.

기본명령: `python -m guitar_learning.train --hand left --song 05_BN2-131-B_solo --physics gpu --device cuda:0 --size large --num-envs 1024 --horizon 32 --seed 7 --updates 2000 --checkpoint-every 100 --out <phase>/train2000`.

현행436/진단v2를 fresh로 시작하며 기존435 checkpoint를 strict resume하지 않는다. 학습/물리/GPU평가/실제자세 렌더 실행은 root만 수행한다. agents는 독립검수·CPU분석/도구를 담당하며 활성 소스와 기존 봉인 결과를 수정하지 않는다. 학습 중 소스·자산·보상·안전 기준은 고정한다. 기술 오류가 없으면 낮은 음 달성만으로 조기 중단하지 않는다.

현재: fresh2000 학습 완료. unified session76314 exit0, native Python PID1248061 GDB 정상 종료. report completed=true/failure=null/cleanup_errors=[]/changed_inputs=[], lifecycle_verified=true. 65,536,000전이·64,000행·2,000개 저널 member가 sampled/logged/durable/committed 일치하고 discard=0·closed=true다. 실제 wall22692.68초(6.30시간), 종료된 곡35,185개. 활성436소스 변화 없음. initial과100회 간격19개 및final 모델을 보존했다.

후처리 실제 완료: CPU 전체 검산/분석 session45417 exit0, GPU 고정5모델 평가 session55206 exit0/native1434296 정상 종료. 초기/500/1000/1500/2000 전체1024 평균은4.02734375/0.9521484375/0.3837890625/3.6552734375/5.42578125이고 안전완주는1024/926/99/967/1019다. 평가한4학습모델 중best=latest2000이다.

실제전신 session45019 exit0/native1456804 정상 종료, 왼손확대 session4329 exit0/native1458062 정상 종료. 두영상은env0 안전9/67음·1969프레임·60fps·32.816667초·1280×720이며 새물리0이다. root 화면QA/독립ffprobe와 reviewer의 전체pose/597핀 검산을 통과했다. 4현행문서는 변경전원문을 archive/20261022_before_long_training_results_v4에 보존하고 갱신·독립검수했다. integrity_after.json은현행436소스/사본·기존3봉인1075파일·4원문SHA 일치를검증한다. 통합README·고정평가보고서·영상·4현행문서의 최종독립검수는모두PASS다. 이번phase의result_manifest.json은자기자신을제외한모든파일의bytes/SHA를봉인한다. 실행·분석·영상·보존작업을완료했다. GPU/GL 작업은종료했고활성실행소스변화는없다.

기술 오류/장시간 진행 정지/비유한/GPU·host memory floor/디스크2GiB 미만이면 root가 원자료를 보존하고 복구를 판단한다. 디스크3GiB는 조기 경고선이다. 생성·readback 실패 자료를 지우지 않는다. 실행 도중 활성 소스/자산 변경은 금지다. 변경 후 개입이 필요하면 새실행 버전으로 분리한다.
