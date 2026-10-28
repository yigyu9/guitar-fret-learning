# Wrist qpos-J v2 검지 native precheck 준비

root 승인 범위: 새 native_precheck/만 소유, GPU는 root만 후속 실행한다. 기존 source/raw/실행봉인은 보존한다. 현재 활성 구현 작업자가 완료하기 전 최종봉인/검수를 하지 않는다.

- [x] 안전 CPU: 기존 old jobs[:4]의 child/output만 변경한 dryplan, existing output·깨진symlink no-native 거부.
- [x] 활성 구현 완료 후 CPU: v2계약/teacher/reference/원래상수·fresh초기73tensor 모델 비교/oldcheckpoint strict거부·현재source핀.
- [ ] 독립 change-reviewer 검수와 최종봉인.
- [ ] root 단일GPU 직렬: fresh bootstrap1update→그 own initial.pt만 reference/zero/random 각4첫시도.

기존 other_finger jobs()/validate()/baseline.run_child를 재사용한다. 원래indexteacher/reference bytes·.5°cap·2초ramp·3초onset·PD/range/보상·4substep·clock·failed포함4분모를 유지한다. 추가 capture 없이 원래 env0/60Hz trace만 저장한다. 다른env/240Hz힘이나 policy학습성과를 주장하지 않는다. 새 sidecar report는 기존 report를 덮어쓰지 않고 모델/RNG·eval updates0·전체pin·장면종료를 확인한다. bootstrap의1update는 초기모델 생성을 위한 원래 절차이며 업데이트후 final은 평가에 사용하지 않는다.

oldsource 실행 결과는 과거검증/원자료와 archive/20261027_before_wrist_position_jacobian_v2 매핑으로만 비교한다. 현재트리에서 old.validate를억지로통과시키지 않는다. old checkpoint의 현재strict거부는 유지한다. 원래 oldinitial73tensor와 fresh73tensor의 모델값 비교는 fulloldload/성과상속을 뜻하지 않는다.

최종 CPU 단계: 동결된 v2 source에서 prepare --active-complete 실행. 수학/short-learning18tests PASS,oldcheckpoint source strict거부,seed7 CPU73model/key집합 동일,기존out/symlink 보호 PASS. compact native fixture를 명시 extra pin했고 현재685pins다. 독립 prep 검수를 요청하며 GPU는 아직 실행하지 않았다.
