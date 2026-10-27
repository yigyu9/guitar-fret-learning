# 보상 v6 장기 실행 도구 독립 검수

2026-10-22, 검수자 `/root/review_gpu`. 최종 판정: **문제없음(PASS), 아래 도구·CPU 검증 범위에 한함.** 활성 소스나 다른 작업자의 도구는 수정하지 않았으며, 이 기록 파일만 작성했다.

## 확인한 범위

- 평가·영상: 이전 봉인 v4 도구와 변경부 대조. GPU 왼손544/8개 정확한 슬롯/E24/보상v6, strict3331 복원, source436 및 봉인 입력 핀, 외장 공백 경로와 별도 out/tag, 캐시 필수 핀, 첫 에피소드1024개·사전0..7 캡처를 확인했다. 초기0도 동일하게 캡처하며 best는 평가한 학습 모델만 비교한다. 실제 자세 렌더의 추가 물리 실행은 없다.
- 학습 검증·분석: v6 전체 계약, soft posture 각0.05/s·tracking4/s 상한, CRC/EOF와 prefix의 구분, 삼중 에피소드 로그 대응, 3331 재생, 안전/실패·손가락·관측 시점별 분모, 외장 run과 로컬 모니터 경로를 검토했다. 디스크 표본은 명시된 동일 run 경로만 사용하고 출처 없는 legacy 행은 제외한다.
- 운영: PID 명령행·출력 경로·시작시각 식별과 Git 설정의 키별 원복 의무를 확인했다. 중단된 첫13회는 commit425984/discard32768이며 fresh2000 성과에 합산하지 않는다. 백업8개 manifest와 실제 파일 크기·총12,615,505,504bytes를 대조했다. 복사 당시 검증된 대용량 백업 SHA는 이번에 전량 재계산하지 않았다. sandbox `/proc`에서 native PID가 보이지 않아 실시간 생존 여부를 독립 인증하지 않았다.
- 자세 분석: 실제 부모-자식 quaternion과 독립 SciPy 각도식, t0 제외60Hz·유효 관절/관절묶음 분모, 안전/실패와 공통 안전 ID, 빈 집단의 결측 처리를 확인했다. native q와 실제 기하각, 끝점 raw 품질과240Hz 누적 보상을 구분하며 캡처0..7을 전체1024나 다른 곡으로 일반화하지 않는다.

## 발견 및 해소

1. **Critical 해소:** `analyze_training.py`의 `verify_motion` import 누락을 발견했다. 작성자가 복원했고, 실제 `analyze()`의 종료 에피소드 루프를 통과하는 CPU 회귀검사가 추가됐다.
2. **Warning 해소:** preflight의 LR·비용 고정 표현을 수동 튜닝 없음과 기존 KL retry 자동 LR 감소·자동 cost weight 갱신 유지로 구분했다.
3. **Warning 해소:** watcher가 GPU 조회나 로그 쓰기 실패로 low-disk SIGINT에 도달하지 못하는 경계를 지적했다. root가 조회 timeout10초, 이벤트 쓰기와 독립적인 finally 신호 처리, 정상 progress 쓰기 오류 후 감시 지속으로 보완했다.

## 직접 수행한 CPU 검사

| 대상 | 직접 확인한 결과 |
|---|---|
| 평가·영상 fixture | 최초8개 PASS, 초기0 캡처 변경 후 최종9개 PASS(0.032초) |
| 검증·분석 fixture | 최초13개 PASS였으나 import 누락은 정적으로 발견. 수정 후14개, run 필터 보강 후 최종15개 PASS(0.126초) |
| watcher mock | 4경로 PASS: 이벤트 쓰기 실패에도 SIGINT1회, PID identity 변경 시 신호0회, progress ENOSPC·조회 timeout 후 감시 지속, 정상 low-disk 기록·신호 |
| 자세 분석 fixture | 4개 PASS(0.008초): 알려진 각도·비평면 회전·퇴화 투영·역할/fade·빈 분모·분담 및 안전 집계 |

횟수는 개정본별 반복 실행이며 합산한 고유 검사 수가 아니다. Python 검사에는 CUDA 비활성화와 `-B`를 사용했다. watcher의 subprocess·프로세스·신호는 전부 mock했다. 실제 GPU/GL/native 실행, 실제 신호 전달, 학습·모니터 조작은 하지 않았다.

## 최종 검수 SHA256

| 파일 | SHA256 |
|---|---|
| evaluate_checkpoints.py | `57b9e54cb6503d8c1c0e2108758e5126525d4bf44e64c3ee5131bb8efaf41423` |
| render_video.py | `da4bdf31b855f39bcc544011945bc0e5147eab872115daf265cc886eaf67e499` |
| test_evaluation_tools.py | `33c3228e519a8a0e95d2a03a699b16ad4b3b537edbc96e1805af1b0e56c5dada` |
| verify_training.py | `ee83d4dc403152ded9ca9e4f469ff88de3462fbe8c362820b8ad304434d6e42e` |
| analyze_training.py | `8560e8950f0d6f052e1e28c8509910a07c738969132cfb89ba7e5a658b6d856a` |
| test_analysis.py | `788baafc758dc861c4696955c1df6d692dd8643612644996d3fef3bc187f39f8` |
| preflight.md | `d9245d458ee6d51190ed59140c0dc3ceaa2f2232542b6e0159052d1685bae6ef` |
| watch_training.py | `7bb63f850ed4046d019a13ba2c0650f61b9f81c9e6ebccb81a6d23f942628dd5` |
| analyze_posture.py | `13d3d2c6ae5668c0ba4a735cfd86289d028f6c1167a974d62688c8b7655a4597` |
| test_posture_tools.py | `ba02217976a11c8e136b0b1a2d260d641f229e63199872f26b4771b955a6c2e5` |

이번 검수는 도구 준비 상태를 확인했다. 진행 중 fresh2000 실행의 최종 raw/모델·고정 평가·자세 분석 결과·영상·최종 보고서는 아직 독립 검수하지 않았다. 분석 main이나 평가/렌더 main을 실행하지 않았으며, 완료·연주 향상·자연스러움·메모리 안정성을 인증하지 않는다. 실제 최종 결과 검수는 학습 및 후처리 완료 후 별도로 수행해야 한다.
