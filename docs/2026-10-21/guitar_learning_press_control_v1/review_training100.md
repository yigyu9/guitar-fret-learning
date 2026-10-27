# 압현 제어 smoke100 독립 검수

요약 판정: **문제없음 — 100회 학습 실행 및 저장 자료의 무결성 범위 PASS.** 고정 정책 평가와 성능 개선 판정은 이 검수에 포함하지 않는다.

## 범위와 방법

`smoke100_verification.json`, `verify_training.log`, `smoke100_process_result.json`, 실제 `smoke100` 설정·계약·보고서·종료 scene·100개 업데이트·metrics/episodes JSONL·최종 checkpoint 및 입력/source manifest를 읽었다. GPU·native physics·GL을 실행하지 않았고 활성 소스와 기존 결과는 수정하지 않았다. 전체 gzip 검증기를 재실행하지는 않았으며, 검증기 코드·실행 로그·결과와 파일 크기를 대조했다. CPU에서 최종 checkpoint를 직접 읽고 tensor finite를 확인했다.

## 확인 결과

- 실제 fresh `large / left / N1024 / H32 / seed7` 100회가 완료됐다. optimizer 업데이트 100, 전이 **3,276,800**, 물리 step 12,800, 실행 시간 **1,124.461673초**가 보고서·업데이트·종료 scene·프로세스 결과와 일치한다. GDB 로그에는 정상 inferior 종료가 있고 프로세스 exit code는 0이다.
- journal의 sampled/logged/durable/committed 전이는 모두 3,276,800이다. discarded/pending/unresolved는 0이고 journal은 정상 닫혔다. 검증 결과의 raw 3,200행, 100 gzip member 전체 CRC/EOF 통과 및 실제 압축 파일 크기 **70,450,130바이트**가 일치한다.
- 100개 업데이트 파일과 metrics 100행이 정확히 대응한다. 업데이트의 종료 원장을 이어 붙인 결과는 episodes JSONL **1,222행**과 순서·내용이 같다. 종료는 **timeline 785 / physical failure 437**, 전곡 과제 성공은 0이다. 이는 수집 결과이며 개선 효과의 증거로 사용하지 않는다.
- 새 항을 포함한 16개 보상 성분이 존재한다. 업데이트 성분합 오차 최대 **5.91e-9**, 검증기의 에피소드 성분합 오차 최대 **0.00017815**는 명시된 허용오차 안이다. 새 tracking 항의 관측값은 0..4/s 적분 상한 안이다.
- curriculum 3,331개 상태의 전체 원장 재생은 검증 결과에서 최대 오차 0이다. 최종 checkpoint는 업데이트 100이며 reward v4 / observation v2 계약과 일치한다. 직접 읽은 모델 56개·actor optimizer 54개·value optimizer 57개, 합계 **167개 tensor가 모두 finite**다.
- 최종 checkpoint SHA256은 `f7f65548793273e1796a447daa4bf4577f0d312f542362186447b1b18d4e4bfe`로 검증 결과와 같다. 현재 입력 **580개 SHA**, 활성 Python **435개 전체 집합 및 원문**, `source_training` 사본을 직접 대조해 일치했다.
- 종료 scene은 닫혔고 cleanup error, Python failure, 입력 변경은 없다. 물리 240Hz / 제어 60Hz 및 기존 native 설정이 보존돼 있다.

## 자원과 로그 해석

optimizer 뒤 cache 반환 후 GPU 여유 최저는 **7.81543GiB**, 마지막은 **8.20410GiB**다. 전체 실행의 raw 여유 최저 **7,229,931,520바이트** 및 guard 여유 최저 **7,471,104,000바이트**와 구분한다. 비Torch 추정 증가 최대는 **0.033203125GiB**이며 native 메모리의 개별 귀속이나 장기 plateau를 증명하지 않는다. cache 반환 100회는 모두 optimizer boundary이고 low-memory 분기는 없다. 이 100회 결과를 2,000회 안정성으로 확대하지 않는다.

시작 로그의 `Could not load visual geom` 6개는 이전 incremental smoke100 로그에도 동일하게 존재한다. 이번 실행에서 GPU OOM/illegal access/SIGFPE나 비정상 종료는 확인되지 않았지만, **native 진단이 전부 없었다고 표현하면 안 된다**. 이 여섯 visual 진단의 구체적인 geom 또는 학습 영향은 이번 검수로 규명하지 않았다.

## 한계와 종료

Critical / 수정이 필요한 Warning: 없음. 이 문서는 완료·로그/저장 무결성·수치 유효성 검수다. CPU 865개 합성 커버리지 및 N4 접촉 probe는 별도 검수 문서를 참조하며 재검수하지 않았다. 고정 0/100 정책 평가 결과, 네 손가락 학습 효과, 압력·음향 정확성, 장기 실행 준비 여부는 이 PASS에 포함하지 않는다.

이 문서 외 파일 변경 및 GPU 실행 없이 작성했으며 작성 종료했다.
