# 1300회 저장본과 복사 원자료 독립 검수

2026-10-22, `/root/review_gpu`. 판정: **문제없음(PASS), 아래 로컬 복사본·checkpoint·검증기 준비 범위.** 실제 prefix1300 검증 main과 GPU 재개는 실행하지 않았다.

## 로컬 복사본 직접 대조

`recovery_copy_manifest.json`의 completed=True/errors0 및 실제 로컬 `recovered_train2000_restart1` 전체 파일 집합1387개를 대조했다. 모든 파일을 로컬에서 읽어 개별 크기·SHA를 전량 확인했으며 총4,499,049,842bytes가 정확히 일치한다. 원경로/복사경로도 각 manifest 행과 같다. 외부 NTFS/FUSE 원본은 다시 읽거나 변경하지 않았다.

| 근거 | SHA256 |
|---|---|
| 복사 manifest | `ee6473509d2c1aaaee250ee59fe8b9930e21ac80d13112ab99c77c6217f3a48a` |
| 원문 settings.json | `ccd4d2fc62e4e412d6a3e8fd2393186342e3c99fdab17e66a32b9aabc29dc606` |
| checkpoint_000499.pt | `a017c58b459ee1f14e30e43df9e5cd36803232e740500f4e08d63a94f1add09c` |
| checkpoint_000999.pt | `4a351b8e59fd4cb1a5825a026d281a08dc7bf3c0d02e0bba69dec163c6e2d8b9` |
| checkpoint_001299.pt | `b32870dbb9ba09dd9e762be3efa73d335493399239fba9174c10706acc2c32de` |

500/1000회 모델 SHA는 중단 전에 작성된 실제 prefix500/1000 분석의 checkpoint SHA와도 일치한다.

1300회 checkpoint와 initial을 CPU로 직접 읽었다. actual updates1300/initial0, identity 전체 동일,544상태·8슬롯·보상v6 계약·3331 curriculum shape를 확인했다. model56/actor Adam54/value Adam57개 텐서가 모두 유한하다. 현재 활성436 Python SHA와 이전 finger_inputs_v1 봉인 manifest SHA도 유지됐다. 이는 실제 strict CUDA 재개나 아직 없는 새 initial1300과의 정확 복원을 대신하는 검증은 아니다.

## 검증기 독립 검수

`verify_recovery.py`의 원경로→복사본 핀 해석은 manifest가 입증한 역사 run 내부 파일에만 적용한다. 외부 run과 무관한 활성 소스·자산 등 핀은 현재 실물 SHA 검사에 남는다. old1300은 CRC가 완료된 선택 prefix·삼중 에피소드 로그·3331 재생·모델 검증이며, old report/전체 gzip EOF/정상 native close를 주장하지 않는다. 새700만 최종 report·전체 EOF·native close를 요구한다. source checkpoint1300→새 initial1300은 metadata 외 모든 상태를 dtype/shape/원바이트까지 비교한다.

초기 리뷰에서 `errors==[]` 필수 조건이 성공한 재시도 이력을 보존하는 복사 계약보다 엄격함을 지적했다. 작성자가 completed+전파일 SHA/크기·정확한 파일 집합·총bytes 검증으로 보완하고 오류 이력을 결과에 남기도록 수정했다. 현재 실제 copy의 errors는0이다. 수정된 CPU fixture7개를 직접 실행해0.007초 PASS했다. 실제 raw 검증 main은 실행하지 않았다.

검수 기준 verifier SHA: `489971bb32ceb11fba23a57734286ee41b558ab6453020191a0dcfbf89cba21d`.
검수 기준 test SHA: `5be4664eda7fb76f74040302ed2e07d42904680101bf2a1d9f42984bcde59c8e`.

## 합산과 한계

유효 경로는 old global0..1299의41,600행/42,598,400전이와 새 local0..699(optimizer1301..2000)의22,400행/22,937,600전이다. 두 세그먼트가 각각 검증됐을 때 합계64,000행/65,536,000전이가 된다. 복사본에는 old update1300..1361의62파일이 실제 존재하며 이 가지는 저장된 정책 경로에 합산하지 않는다. 첫13회 중단도 계속 별도다.

old report는 없고 실제 GDB 로그는 EIO 뒤 exit1이므로 정상 종료·전체 원자료 EOF를 인증하지 않는다. 실제 물리 장면/진행 중인 곡은 새 준비 에피소드로 시작한다. 하드웨어 원인·연속2000회 단일 프로세스·연주 향상은 이 자료의 결론이 아니다.

이 검수는 로컬 CPU 읽기와 이 기록 파일 작성만 수행했다. 외부 복구·재마운트·삭제, 복사/검증 main, GPU·native·GL·신호·학습은 실행하지 않았다. 소스·도구·원자료·이전 봉인은 수정하지 않았다.
