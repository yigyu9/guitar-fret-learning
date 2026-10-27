# Persistent reset 최종 독립 검수

판정: **문제없음.** 검수 범위에서 Critical/Warning 발견은 없다. 같은 장면의 반복 사용, 경계 초기화, 기존 checkpoint 재개 및 음악 목표가 다른 환경의 부분 reset에 대한 단기 연결 검증을 완료한 것으로 판단한다. 장기 재사용의 안정성·solver cache 동등성·연주 성능 개선의 증명은 아니다.

## 원자료와 주장 대조

- 네 실행의 `transitions.jsonl.gz`를 읽어 직접 재집계했다. fresh 176/2, repeat 704/8, resume 256/2, pool 384/4 전이/완료 episode이며 합계 **1,520전이·16완료 episode·4개 별도 PPO 업데이트**다. 각 report의 완료 및 오류 목록과 일치한다.
- Persistent 세 실행의 worker 총 5개는 각각 create_sim=1, create_env=1, load_asset=2, destroy_sim=1이다. reset 근거 19개의 SHA, 동일 scene/controller/FK identity, local step 및 target history 0, 경계별 상태 쓰기 증가량 2, 마지막 경계 이후 총계 불변을 확인했다. readback의 DOF q/qd·기타 pose/velocity는 선언한 1e-6 기준 안에 있다. 원 core_report 해시가 canonical report의 보존 SHA와 일치한다.
- 반복 준비 9회의 새 장면 첫 준비 대비 최대 차이는 DOF q 0.00098330rad, qd 0.02332012rad/s, 인간 link 위치 0.6166mm, 기타 body 위치 0.7189mm, 기타 회전 0.00155289rad, 목표 0.00000257rad다. README의 반올림 수치와 일치한다. 준비 후 완전 동일성을 주장하지 않고 9회 모두 세 지지 부위와 양발의 양성 접촉을 확인한 범위로 제한했다.
- Strict resume는 분석 생산자가 기존 checkpoint와 initial checkpoint의 identity/model/두 optimizer/cost weight/updates/모든 저장 RNG 필드를 정확 비교한 결과와 15→16 업데이트를 남겼다. 해당 비교 코드와 입력 checkpoint·initial/final의 사전 SHA를 확인했다. 검수자가 Torch checkpoint를 별도로 다시 로드하거나 학습을 실행하지는 않았다.
- Pool의 실제 정책 표본 event는 **1·2·3·4**다. 설정의 전체 [0,1,2,3,4] 중 0까지 검증했다고 설명하지 않는다.
- 원자료에서 모든 전이의 failure_reasons가 비어 있고 타현 매칭 및 목표 유지 누적 최대값은 0이다. 연주 성공이나 실제 압력·음향 검증으로 확대하지 않았다.

## 지표 범위

- 접촉 비율과 기타·발 편차 최대값은 compact 로그의 **60Hz endpoint** 집계다. 직접 재집계한 삼중 지지는 fresh 92.04545%, repeat 92.75568%, resume 97.26563%, pool 88.80208%이며 기타 최대 이동은 각각 1.81543/2.11613/1.44405/2.04704mm로 분석·README와 일치한다.
- 물리 실패는 환경이 각 전이의 **네 240Hz 표본에서 합친 failure_reasons**로 집계한다. 6,080은 준비를 제외한 실제 정책 구간 물리스텝 수이며, 전부 raw 저장된 표본 수라는 주장은 하지 않는다.
- N1 reset 시간 합/횟수는 76.95809/3=25.65270초와 194.54985/9=21.61665초다. N2에 같은 산식을 적용한 값은 병렬 부모 대기시간의 환경당 분담 비용이다. 이를 개별 reset latency로 설명하지 않는다.
- sampled worker 현재 RSS 합 최댓값 664.164/629.766/1260.141/1261.695MiB를 resources 원자료에서 확인했다. 공존하는 장기 실행과 5초 표본이라는 한계, 장기 누수 부재나 일정 가속률을 보증하지 않는다는 설명이 적절하다.
- status.json은 core 진행 상태이며 lifecycle 감사까지 결합한 report.json이 최종 판정이라는 구분이 명시됐다.

## 보존·검수 한계

`analysis_inputs_before.json`에 선언된 **125개 입력 전체를 streaming SHA-256으로 다시 확인하여 변경 0**을 확인했다. CPU 146개 통과는 사전 검수에서 확인한 로그를 따른다. 새 물리 실행·학습·전체 테스트를 반복하지 않았으며, 검수자는 이 문서만 새로 작성했다. root가 추후 생성할 source_final/artifact_inventory/final_verification은 이 판정의 이미 완료된 근거로 취급하지 않았다.

## 검수 시점 문서·분석 SHA-256

| 파일 | SHA-256 |
| --- | --- |
| `README.md` | `43fa1034021dbfae6479ad1a73c7c6f7c86b40b2d0d28caaf18ebc0a873b4e06` |
| `analyze_results.py` | `56b2966c93b8b7055f08ec7f0bfe03d012d04aec1505ca1bcca9379adb627caf` |
| `analysis.json` | `a61ec74eb8f5535f9382e8df07ade7a8f2a62ebe60e35f7459bdd1b32f3175b8` |
| `analysis_verification.json` | `454b62390e2518d2e8844eabdb43d1a8c9731f43601ac3db703f6ab4331fcc48` |
