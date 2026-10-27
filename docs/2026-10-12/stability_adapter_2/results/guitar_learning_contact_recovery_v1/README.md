# 접촉 회복 첫 구현과 실제 연결 검사

2026-10-19. 구현 범위는 명시 평가 seed·초기화 진단, 작은 유한 관절 목표 교란, 실제240Hz 획득/상실/회복 기록, 독립 감사와 회복 자료 선별이다. 새 보상 R1/R2·새 BC/PPO·목표 B·전곡은 수행하지 않았다.

코드와 실행법: /home/ajou/yigyu/3/guitar_learning/contact_recovery/README.md

## 구현과 검증 경계

- 정책500상태·39행동(왼손33, 오른손6은0), medium, 원 목표/음악/안전/제어 계약을 유지했다. Root고정·하체유한제어·자유기타·중력ON·스트랩OFF, 원 gain·한계·충돌을 변경하지 않았다.
- 평가 seed는 strict checkpoint load가 저장 RNG를 복원한 뒤 적용한다. 결정적/탐색 평가, 새 프로세스 첫 실행/같은 장면 반복 reset을 구분한다. 관절·기타 위치/속도·제어기/행동/접촉 이력을 저장하며 숨은 solver 상태나 물리 결정성을 주장하지 않는다.
- 기존 실제 측정 기반 접촉 교사를 재사용한다. 교란은 지정된 왼손 손목/해당 손가락의 한 축 제어 목표에만 최대0.01rad·0.2초로 부여하고 원래 codec을 통과한다. 기타 직접 힘·상태 덮어쓰기·gain변경을 하지 않는다.
- 획득50ms 후 음 종료 전의 clean 접촉 상실을 기록한다. 회복은0.5초 내 재접촉 및 이후0.5초의90% clean 유지다. 예정된 해제는 접촉 상실로 세지 않는다. 원래 음악 판정은 별도 유지한다.
- 원시 행동/관측/실제4substep을 모두 보존한다. 독립 감사는 원 native·관측·음악·안전·보상과 교사/교란/codec/회복을 재계산한다. 실제 상실·회복과 원 음악 성공을 모두 통과하고 마지막 교란 이후인 교사 보정 행만 내보낸다. 교란 자체는 시연 라벨에 포함하지 않는다.

관련 CPU 검사64개 통과: `cpu_final_v3.log`(16.494초). 별도 읽기 전용 검수에서 신규 평가/수집/감사/이관/내보내기 경계를 확인했고 잔여 actionable finding은 없었다. CPU의 합성 접촉 검사 성공을 native 회복 성능으로 해석하지 않는다.

## 실제 수집과 재감사

| 실행 | 조건 | 원 단음 유지/해제 및 안전 | 실제 교란 | 실제 상실/회복 |
|---|---|---|---|---|
| collect_native_v2/case_000 | 명목, seed7 | 성공 | 없음 | 0/0 |
| collect_native_v2/case_001 | held 허용창1.7~1.9초, seed11 | 성공 | 미실행 | 0/0 |
| collect_held_pulse_native_v1/case_000 | held 허용창1.9~1.95초, seed7 | 성공 | ring2 −0.01rad·0.05초,3제어tick | 0/0 |

각 실행은4초·240행동·960실제240Hz표본이다. 세 실행 모두 음2~2.5초 clean 유지100%, 해제2.8~3.3초 접촉 부재100%, 물리 실패0이었다. 부모/각 case 완료, source불변, physical flags, 금지호출/미pin import 없음과 runtime 무이상(CW0x37f·state_mutations=False)을 확인했다.

실제 최초 clean 접촉1.866667초·획득1.916667초여서 최초 허용창1.9초까지는 held 조건이 성립하지 않았다. 결과를 보존하고 새 protocol에서 허용창을 이동했다. 이 교란은 실제 적용됐지만 상실을 만들지 않았다. 따라서 회복 성공 자료는0건이다. 성공 기준을 완화하거나 원 음악 성공을 회복 성공으로 바꾸지 않았다.

v2 전체 감사는 실제 명목 원자료를 통과해 checkpoint 출처 이관에 사용됐다. 실제 pulse 원자료도 전체 재계산을 통과한 뒤 회복 시연0행으로 내보내기가 거부됐다(`pulse_export_v2.log`). 이 경우 `pulse_export_v2_runtime_json_audit.json`은 예상 거절로 completed=False지만 runtime anomaly=None이다. 유효한 dataset manifest/NPZ는 발행하지 않았다.

명목 반복 reset 비교에서 위치·속도·기타 회전·제어 목표는 같았으나 초기 접촉 feature 수/uncertain 목록/native contacts가 달랐다(`collect_native_v2/reset_comparisons.json`,5차이). 이를 reset 전체 동일이나 hidden cache 원인 확정으로 설명하지 않는다.

## 실행 중 발견·수정한 통합 문제

1. 신규 native의 이전 상대 import 경로 오류를 고치고 함수 내부 의존 import 경계 검사를 추가했다. 초기상태/조건 sidecar SHA 검사 누락도 검수에서 보완했다. v1 사전 검사 중단 로그·사유는 보존했다.
2. 실제 teacher replay에서 이전 codec 목표를 float32 native 제출 목표105로 복원하면 실제 float64 codec 이력과 약10⁻⁷rad 차이가 생겨 exact 감사가 실패했다. 원 파일/실패는 보존하고 `audit_v2`/`dataset_v2`를 추가했다. 원 행동으로 float64 requested/final81을 독립 계산하여 원 기록과 exact 비교하고 그 값을 다음 previous로 쓴다. 오차 허용치를 넓혀 통과시키지 않았다.
3. 내부화 전 B32 원본은 악보 처리 소스의 path/SHA/bytes 기록이 달라 현재 strict load에서 정확히 거절됐다. `evaluate_native_v2`, `evaluate_fresh_native_v1`, `evaluate_stochastic_native_v1`은 이 실패 보존본이다. 새 별도 출처 이관과 native 평가를 아래에서 구분한다.

## 참조 모델의 명시적 출처 이관

`reference_provenance_migration_v1/manifest.json`은 지원 원본B32 SHA `ed4408f945b47732988927428a2228281abe777ac13a2b0ad797e0e64e6ffde7` 한 개에 대한 이관이다. 실제 명목 capture의 전체 감사, 고정된 이전CAS/현재live 소스의 SHA·크기, 데이터7파일 완전 동일을 확인했다. 바꾼 필드는 `identity.architecture.contract.task.provenance.provenance`뿐이다.

모델·optimizer·RNG·업데이트32·나머지identity/config는 저장 후 exact roundtrip으로 보존됐다. 새 checkpoint SHA는 `8bedd8d9affc16406b3fb82667429615b8f13ec5e894d1dc576e940549edfd67`이며 원본을 덮어쓰지 않았다. 현재 전체 PPO identity를 별도 계산한 결과 차이0이었다(`migrated_identity_comparison.json`). 이관 자체는 성능 성공을 상속하지 않는다. 평가 전용 표시는 사용 범위이며 일반PPO loader가 학습 재개를 기술적으로 차단하는 것은 아니다.

## 이관 모델의 실제 평가

| 실행 | 방식 | seed | 원래 왼손 단음 조건·안전 성공 |
|---|---|---|---|
| evaluate_migrated_native_v1 | 같은 장면 반복reset·결정적 | 7,11 | 2/2 |
| evaluate_migrated_fresh_native_v1 | 새 interpreter/장면 첫회·결정적 | 7 | 1/1 |
| evaluate_migrated_stochastic_native_v1 | 같은 장면 반복reset·탐색 | 7,11 | 2/2 |

다섯 회 모두4초·240행동·960물리표본을 완료했고 clean 유지/해제 부재100%, 물리 실패0이었다. 교사 보정은 없다. strict load 후 명시seed 적용과 optimizer update32를 각 case에서 확인했다. 새 프로세스 batch의 child 결과/runtime SHA, 모든 부모/case 종료·금지호출/미pin import 없음·입력 해시·runtime 무이상·원본10파일/보관본·동결 소스25파일을 최종 재확인했다. 세부 기계 판독 결과는 `verification.json`이다.

같은 seed7의 새 프로세스 첫회와 persistent 첫회의 행동240×39는 exact 동일했다. 탐색seed7/11의 첫 행동은 다르며 최대절대차0.011402905였다. RNG 복원 뒤 seed가 실제 탐색 행동에 적용되는 연결을 확인한 것이다. 고정20조건 평가·초기자세 다양화·독립적인 통계 성능 비교·회복 향상을 검증한 결과는 아니다. strict_music 타현/양손/압력/음향 성공으로 설명하지 않는다.

## 보존과 다음 작업

기존 실행 입력 원본: `guitar_learning/archive/20261019_before_contact_recovery/manifest.json`. sidecar 감사 보완 전 원본: `guitar_learning/archive/20261019_before_recovery_sidecar_audit/manifest.json`. codec 보완 전 v1: `guitar_learning/archive/20261019_before_recovery_codec_v2/manifest.json`. 이번 source snapshot v1~v4와 모든 실패/중단/재시도 자료를 보존했다. 현재 권장 감사·내보내기는 v2이며 v1 source 파일은 실제 실행 pin 검증과 공통 native/reward 감사 재사용을 위해 원래 경로에도 유지한다.

다음은 안전한 편차 조건에서 실제 상실·회복이 있는 시연을 확보하는 일이다. 현재0건을 학습 자료로 쓰지 않는다. 그 뒤 회복 BC/native 평가, R1 준비 접촉 구간과 R2 획득 이력에 따른 해제 보상 자격을 각각 대조하고 단계 커리큘럼을 연결한다. 고정20조건 검증, 새 보상 Actor 초기화 계약, 목표 B·두 음 전환·오른손 결합·전곡은 남아 있다.

현재 단음은2.5초에 끝나므로0.5초 회복 유지까지 확인하려면 재접촉이2.0초 이하여야 한다. 실제 획득1.9167초 이후에는 약83ms의 여유뿐이다. 다음 수집에서 편차만 계속 키우기보다 별도의 긴 유지·회복 과제를 구성할 필요가 있다. 이 경우 새 과제/관측/보상 계약을 선언하고 원 음악 평가와 분리해야 하며, 이번 결과의 기준을 소급 변경하면 안 된다.
