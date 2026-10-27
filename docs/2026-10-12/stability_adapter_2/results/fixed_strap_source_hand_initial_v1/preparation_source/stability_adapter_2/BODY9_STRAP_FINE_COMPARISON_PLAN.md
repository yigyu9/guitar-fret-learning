# 몸통9 PD×2 유지 기준에서 스트랩 -2mm 비교 — 다음 단위

현재 small_wrist_motion_v1의 동일 초기 humanoid81/G p·q·기존 PD목표/몸통9 gain×2와 작은손목파형을 유지하고, 절대 passive strap rest length만1.1018469719600776→1.0998469719600776m로2mm 줄인다. 현재 초기 route길이1.0858332748277348m 기준 slack은16.013697→14.013697mm로 여전히 양수이며, 시작 시 cable law장력0이다. 실제 native 초기 route를 다시 확인한다.

목적은 초기14mm대 이탈을 줄이면서 손목 움직임 중 유지도 확인하는 것이다. 이전 몸통 gain이 다른 strap 시험 결과를 이 새 조합의 결과로 승계하지 않는다. 케이블 rest length는 trial 전체에서 상수이며 stiffness6000N/m·damping120Ns/m·cap300N을 그대로 쓴다. 기타 초기 p/q를 이동하거나 목표로 끌어당기는 힘은 추가하지 않는다.

1. 원본 trial/proposal의 SHA를 확인하고 새 경로로 복사한다. 새 trial의 initial_settings.strap_rest_length_m만 변경하고, 선언 row의 trial path/SHA·절대LA와 입력closure를 갱신한다. source anchor/초기81/기존81목표/나머지 trial값은 exact 동일이어야 한다. 기존 initial source/FK admission을 유지하며 native t0 상태·모델/목표/strap을 확인한다.
2. run_small_wrist_recorded_diagnostic의 동작 계약을 유지해 같은5초를1회 기록한다. L_Wrist_x 파형0.005rad/1Hz,60Hz와 최종66권한·실제 selfcollision/자유G/root하체고정/몸통목표를 유지한다. 초기값·스트랩 전신/손151frame과 partial/오류도 보존한다.
3. small_wrist_motion_v1와 동일한 fullmax/종료초기오차·2~5초 변화범위·실제손목응답·strap법칙 장력·contact를 비교한다. 이동/회전 중 하나만 좋아지는 tradeoff도 그대로 남긴다. 개선이 없으면 더 짧은길이를 무조건 반복하지 않고 초기 humanoid 자세의 과도구간/실제 지지점과 p/q보정 권한을 다시 검토한다.

- [ ] 변경1필드/새선언의 입력 보존·사전검사
- [ ] 같은 동작으로 한5초·초기값·실제스트랩영상
- [ ] 초기 이탈/동작 유지·형상/contact·실제PNG/원자료 검토

이 계획은 미실행이다. 최종 연주목표+안정화보정 관계를 설계한 뒤 학습구조를 결정한다. 한작은손목 시험으로 전반 연주성공을 선언하지 않고 WAIT→REACH→GRIP→TRANSPORT를 필수 선행과정으로 두지 않는다.
