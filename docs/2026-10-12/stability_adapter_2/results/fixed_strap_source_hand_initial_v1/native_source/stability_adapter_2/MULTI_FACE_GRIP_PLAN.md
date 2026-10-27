# 왼손의 엄지후면·손가락전면·손바닥옆면 초기 grip

사용자 요청을 다음 소단계로 우선한다. 직전 STRAP_FIVE_SECOND_PLAN은 보존하며 아직 미실행이다.
왼손 엄지는 기타 넥 −Z 후면, index/middle/ring/pinky는 +Z 줄·프렛 전면,
손바닥은 기존 파란 +X 테이퍼 옆면을 지지하는 초기각을 탐색한다.
좌표는 기타 local frame이며 세계 Z와 구별한다.

## 계획과 검증 기준

- [ ] 기존 source face-used neck와 실제 hand collision mesh에서 facet 내부 추적점을 선정한다.
  전면은 프렛·줄을 포함한 source 최외곽 높이를 확인하고 후면법선은 명시 −Z로 둔다.
  비활성 thumb_pad capsule이나 *_top marker를 접촉면으로 사용하지 않는다.
- [ ] 왼팔12 초기각은 기준 대비 최대±0.15rad, 왼손21 초기각은 native hard range 안에서
  세 굴곡 seed로 FK 탐색한다. 몸통9/오른팔·손/하체/root/기타 초기 p·q는 유지한다.
  손바닥 위쪽반구 proxy를 필수로, +Z 선호와 옆면에 가까운 평행을 부드럽게 둔다.
  추적점은 유한 패치 안쪽을 선호하고 모델한계/사람–기타/양손/비인접 왼손 내부 교차를 검사한다.
- [ ] source 검사를 통과하는 최대2후보와 기준을 각각 실제 Gym5초 실행한다.
  FK는 제안일 뿐이며 fresh native t0 body pose/패치gap/교차를 확인한다.
  초기 배치가 거절되면 실제 초기값·t0 영상과 이유를 partial로 보존하고 정상5초라고 하지 않는다.
- [ ] 엄지/각손가락/손바닥의 실제 접촉 행, 기타 초기p/q의 최대·종료오차,
  몸통 실제 움직임과 자기충돌을 분석하고 모든 초기값·전신/손영상·설명 문서를 남긴다.

목표는 각 면을 동시에 짚는 초기 배치이며 단순한 finger hull 근접만으로 잡았다고 선언하지 않는다.
source 후보 기준은 각 facet 추적점의 지정면 거리3mm 이내, 손바닥 위쪽proxy>0,
교차공통반경>1e−7m 행 없음이다. 이 수치는 후보선별용이며 cooked clearance/안정성공 기준이 아니다.
thumb1 등 native 다축 회전은 expmap 가설로 제안하되 실제 초기FK와 반드시 대조한다.

첫 비교는 기존 기본PD(kp/kd1배), 절대LA1.1018469719600776m와 기존 왼팔12
상수 목표보정을 유지한다. 새 손가락 초기각을 초기 PD 목표에도 반영한다.
연주에 쓸 양쪽Thorax→손가락66 최종 목표 경로는 유지하며, 이번에는 왼쪽33축의 초기배치만 조정한다.
새 지속 grip feedback이나 gain 확대는 이번 비교에 추가하지 않는다.

기타자유·중력·원본 수동strap/root하체물리고정/몸통초기목표/self-collision ON을 유지한다.
기타고정·손강제부착·지속pose덮어쓰기를 사용하지 않는다. source-only FK 갱신은 native 상태쓰기와 다르다.
code/trial은 stability_adapter_2, raw/로그/이미지/영상은
docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v1에 보존한다.
sealed 실행 후 완료체크는 메인PLAN.md에 남긴다.
