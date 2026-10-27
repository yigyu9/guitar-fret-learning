# fresh restart1의 prefix100 독립 검수

2026-10-22, `/root/review_gpu`. 판정: **문제없음(PASS), 첫100 committed 업데이트의 중간 자료 범위.**

대상은 외부 `/media/ajou/새 볼륨1/guitar_learning_runs/20261022_v6_long/train2000_restart1` 및 이 phase의 `analysis_prefix_000100/analysis.json`이다. 중단된 첫 `train2000`의13회는 합산하지 않았다. 분석 JSON의 SHA256은 `f0c14087d6c1320ec16d9829ab9b6e4d6283885f8591940785538612572c686b`다.

## 직접 확인

- 원 run의 첫100개 `learning_metrics.jsonl` 행과 `update_000000.json`~`update_000099.json`을 전부 대조했다. update 순서0~99, 매 업데이트 누적 commit32,768전이와100회 총3,276,800전이가 맞다. 각 업데이트의 종료 에피소드와 별도 `episodes.jsonl`의 해당 prefix가 내용·순서까지 정확히 일치한다.
- 67음 원장의 `left`를 실제 목표 finger별로 독립 합산하고 에피소드별 성공 수 및 분석 집단의 평균·finger fraction과 대조했다. 아래 수치는 분석과 일치한다.

| 집단 | 종료 에피소드 | 서로 다른 env ID | 달성 음 합계 | 에피소드당 평균/67 | 검지/중지/약지/소지 달성 합계 |
|---|---:|---:|---:|---:|---|
| 전체 종료 |1285|1024|2022|1.5735408560|1023 / 9 / 990 / 0|
| 안전 시간축 완료 |671|671|1210|1.8032786885|532 / 7 / 671 / 0|
| 물리 실패 |614|491|812|1.3224755700|491 / 2 / 319 / 0|

- `checkpoint_000099.pt`를 CPU로 직접 읽어 optimizer update100·544상태/8슬롯·보상v6 전체 계약·3331 curriculum을 확인했다. model56/actor Adam54/value Adam57개 텐서가 모두 유한하다. SHA256 `fb60b85a3b93747619285adc42aea51e1a290aeeffceec41a800ec75f52eda9e`는 prefix 검증 결과와 일치한다.
- 실행 입력581개와 현재 활성436 Python의 SHA, 분석에 기록된 계약·소스 manifest SHA를 현재 파일에 대조했다. 이전 `finger_inputs_v1` 봉인 manifest SHA `03588cd5c3c5b042eb3f3f64d1574aed8d2902c716e7a4b850309f3e4a20f42a`도 유지됐다. 이전 봉인 전체 파일의 대용량 재해시는 반복하지 않았다.
- 분석의 모드는 `committed_prefix`, `final_completed=False`, `final_execution_verified=False`다. 검증 기록은 raw3200행의 완료된 gzip member CRC를 검사한 prefix이며 전체 파일 EOF·최종 native close는 인증하지 않는다. root가 이미 수행한 raw 전체 prefix 검산·3331 재생을 이번에 중복 실행하지 않았다. 기록된3331 재생 최대오차는0이다.
- 디스크 표본은 restart1의 로컬 phase 기록을 사용하며 optimizer1~100 범위다. 진행 중인 다른 run이나 첫13회 자료를 성과에 섞는 명백한 오류는 찾지 못했다. 그림6 PNG·6 SVG는 CPU 디코딩/구문 검사가 통과했다. 그래프를 다시 생성하거나 영상·GL을 실행하지 않았다.

## 해석 경계

root의 안전671/실패614·안전곡 평균1.8032786885·소지 성공0 해석은 맞다. 실패614건에는491개 환경의 반복 종료가 포함되므로 전체1024 독립 고정 평가의 실패율로 환산하지 않는다. 안전곡은 update61~99에 종료됐고, 집계에는 수집 중 변하는 정책과 시간에 따른 선택 효과가 있다. 현재 curriculum은 surface_approach 진행도0이다.

100×32/60=53.333초는 환경당 물리 수집 예산이며 같은 정책으로 완주한 횟수가 아니다. 장기2000회 완료·현재 고정 checkpoint의1024환경 첫 곡 성능·손가락 성과 유지·자연스러움 향상은 아직 이 자료로 검증하지 않았다. 낮은 중간 성과 자체를 기술 실패나 조기 중단 조건으로 해석하지 않는다.

이 검수는 CPU 읽기와 이 기록 파일 작성만 수행했다. 분석/검증 main, GPU·native·GL, 실제 신호, 학습·모니터 조작은 실행하지 않았다. 활성 소스·도구·원자료는 변경하지 않았다.
