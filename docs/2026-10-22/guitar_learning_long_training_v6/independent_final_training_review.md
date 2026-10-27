# 1300+700 실제 학습 경로 최종 독립 검수

2026-10-22, `/root/review_gpu`. 판정: **문제없음(PASS), 선택된 학습 경로의 실행·집계 범위.** 고정 정책 평가·영상·자세 개선 결과는 별도 검수 대상이다.

## 선택 경로 및 실제 종료

선택된 old run은 프로젝트 밖 durable `recovered_train2000_restart1`, 새 run은 phase 안의 `train_resume700_restart1`이다. old local0..1299와 새 local0..699/global1300..1999만 읽었다.

| 구간 | 유효 업데이트 | 전이 | raw 행 | 종료/안전/물리 실패 |
|---|---:|---:|---:|---|
| 원 저장 prefix |1300|42,598,400|41,600|23,162 / 17,294 / 5,868|
| 새 재개 |700|22,937,600|22,400|11,679 / 10,031 / 1,648|
| 합계 |2000|65,536,000|64,000|34,841 / 27,325 / 7,516|

새 run의 실제 report는 completed/optimizer2000/stopped=updates_complete, failure=None, cleanup/changed/missing 입력 목록 없음, lifecycle 검증 성공이다. wall은8175.392568초다. `gpu_scene_final.json`과 report가 같고1024환경·89,600 physics step·closed를 확인했다. journal sampled/logged/durable/committed는 모두22,937,600이며 discarded0이다. GDB는 native PID1709267의 정상 종료를 기록했다.

old run의 report는 없으며 old prefix의 전체 gzip EOF/정상 native close를 주장하지 않는다. root의 full verifier는 old1300의 CRC 완료 member·새700 전체 CRC/EOF와3331 재생오차0을 기록했다. 전체64,000 raw CRC·3331 재생은 이미 수행됐으므로 독립 검수에서 반복하지 않았다.

## 원장·metrics 독립 재집계

두 선택 구간의 metrics2000행을 직접 스트리밍해 local update·global optimizer·누적 commit 순서를 대조했다. 각 종료 에피소드를 별도 `episodes.jsonl`과 내용·순서까지 전부 비교했다. 실제67음의 목표 finger와 원장 `left`를 독립 합산하고 에피소드 성공 수·최종 분석의 집단 평균/finger fraction과 대조했다.

| 집단 | 에피소드 | 달성 음 합계 | 에피소드당 평균/67 | 검지/중지/약지/소지 달성 합계 |
|---|---:|---:|---:|---|
| 전체 종료 |34,841|98,121|2.8162509687|71,256 / 4,863 / 21,825 / 177|
| 안전 시간축 완료 |27,325|84,418|3.0894053065|61,263 / 4,225 / 18,780 / 150|
| 물리 실패 |7,516|13,703|1.8231772219|9,993 / 638 / 3,045 / 27|

67음 전체 과제 성공은 모두0이다. 이 수치는 수집 중 바뀌는 정책의 종료 에피소드 통계이며, 반복 환경·곡과 물리 재시작을 포함한다. 누적 소지 성공177건 또는 안전곡150건을 최종 모델의 소지 성과나 보존 능력으로 해석하지 않는다. 안전 완주는 물리/시간축 결과이며 곡의67음 달성과 다르다.

`analysis_final/analysis.json`의2000점 전역 축·구간 offset·집계가 직접 계산과 일치한다. 그림6 PNG·6 SVG의 CPU 디코딩/구문 검사도 통과했다. 그림 재생성이나 실제 분석 main은 실행하지 않았다.

## 모델·입력 및 제외 범위

실제 source checkpoint1300과 새 initial1300을 CPU로 읽어 metadata 외 모든 필드의 타입/shape/원바이트를 대조했다. 모델·두 Adam·cost weight·업데이트·Torch/NumPy/Python/CUDA RNG·3331 상태가 정확히 같다. 최종2000 모델·양 Adam은 초기 재개본에서 갱신됐고 비활성 오른손 actor tensor는 보존됐다. 최종 model56/actor Adam54/value Adam57개 텐서는 모두 유한하며 identity·544상태/8슬롯/v6/3331 계약이 유지됐다.

old581개·새582개 입력 핀을 각각 대조했다. 역사 외장 run 내부 핀만 파생 manifest가 입증한 outside 복사본으로 해석했고 나머지는 현재 실물 SHA를 검사했다. 활성436 소스와 finger_inputs_v1 봉인 manifest SHA도 유지됐다. 현재 선택 manifest는 `f543902c7b267271d6b22bc0f4ed84b3629f66bfd6c595c693c6af6138ba3306`이다.

제외된 첫13회·old1300 이후62파일·처음 재개 후 중단된5회는 이2000회에 합산하지 않는다. 첫5회 report는 completed=False/optimizer1305/163,840전이/interrupted이며1305 failure_last_valid를 별도 보존한다. 실제 새 initial은1305가 아니라1300과 정확히 같음도 확인했다. old62파일의 존재는 원시 전체 완전성을 추가 인증하는 근거가 아니다.

새 물리는035/v14의 새 곡 에피소드에서 시작했다. 이 검수는 끊김 없는 단일2000회 native 실행·물리 상태 재개·외장 장치 고장 원인·연주 수렴·자연스러움 향상을 인증하지 않는다. 고정된5개 모델의1024환경 평가와 영상·자세 분석은 완료 후 별도로 대조해야 한다.

## 주요 SHA256

| 파일 | SHA256 |
|---|---|
| recovery_verification.json | `c69c1d3de417a9f712bb074135e4013e1f7ecdcc472314912d92bf30ce577acf` |
| analysis_final/analysis.json | `bc440a33868fc9bdfc75737c569f4df2959dfe67bc3fa1f545df331caaf29fb6` |
| 새 run report.json | `ef2d115cb4913f425682685589e0cfdc9e563bf9899f257560c45147334e1033` |
| 새 run gpu_scene_final.json | `98726add01ec24fdbb4dff36281f48dedb04cfea0e8c9208ee354c3b5cfd2c2c` |
| 새 run final.pt | `1a037c1854555a2fd84a940b73a71c0334335379faa5e182fdc0641b8a655f47` |

이 검수는 CPU 읽기와 이 기록 파일 작성만 수행했다. 원자료·도구·활성 소스·이전 봉인을 수정하지 않았고, 실제 GPU·native·GL·학습·프로세스/신호·평가/분석 main을 실행하지 않았다.
