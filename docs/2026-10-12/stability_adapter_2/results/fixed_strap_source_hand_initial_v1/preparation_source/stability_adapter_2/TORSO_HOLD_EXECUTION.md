# 몸통9 PD 유지와 native 충돌형상 비교 실행 계약

직전 source/actual 진단과 TORSO_HOLD_AND_NATIVE_COLLISION_PLAN을 따른다. 사용자 자율진행 승인에 따라 추가 질문 없이 진행한다. 기존 source·실행·계획·출력은 SHA exact 보존한다.

1. palm_patch_priority_diagnostic_v1의 동일 trial/proposal로 native 초기환경 한회만 생성해 physics0 상태를 조회한다. 일반 whole_body/hands와 동일시점 hands_collision API 카메라 이미지를 저장한다. 실제 strap 경로를 동일 helper로 표시하고 raw PNG도 보존한다. Native shape/body/filter/offset와 selfcollision matrix, 초기state/PD/Python target을 query/render 전후 대조한다. Camera collision 표시만으로 cooked 최단거리·관통 없음을 인증하지 않는다.
2. 새 runner는 같은 trial/proposal를 재사용한다. Torso_x/y/z, Spine_x/y/z, Chest_x/y/z stiffness600→1200·damping150→float32(150×√2)=212.1320343으로만 변경한다. 나머지72 관절 properties·effortcap300·driveMode·초기81q·기존81 목표/G p/q·LA·양팔손gain/solver는 그대로다. PD setter 전후 native state/target 유지와 readback을 확인한다. Root와 하체 물리fixed, 자유 기타와 passive strap, 주요66권한은 유지한다.
3. 실제 새5초 한회/1200step·초기0초 포함151frame/30fps·전신/손 두영상과 raw/frame/route/SHA를 보존한다. 기존 baseline은 완료된 palm_patch_priority_diagnostic_v1 원자료로 비교하며 재실행하지 않는다. State/pose overwrite·기타목표힘/고정·손 강제 부착을 넣지 않는다.
4. Native 원자료 world p/q·root/lower·300 update/old81목표·장력법칙을 재계산한다. 기존 feature/early-motion analyzer를 exact-copy 보존한 새 variant에서 requested patch 근접/SDK pair residual과 Chest/팔 vector를 대조한다. 개선 여부에 따라 다음 관절/strap/feedback 단위를 결정한다. 초기source support 실패와 source/native증거 차이를 유지하고 성공기준을 임의 확정하지 않는다.

- [ ] physics0 초기 일반/충돌형상과 readonly query
- [ ] body9 gain만 변경한 한5초/스트랩 두영상·불변성
- [ ] raw/SDK/early-motion 재계산·그림·문서·보존감사

초기 gain 변경은 실제몸통 drift4.231250°와 사용자의 최소몸통움직임 목표에 근거한다. Damping비율은 scalar heuristic이며 결합몸통의 critical damping 인증이 아니다. Controller학습 구조는 결과/물리 제약을 확인한 뒤 정한다. Luna/독립검수 도구한도일 경우 Sol/root 산출물·자체검증을 분리 기록한다.
