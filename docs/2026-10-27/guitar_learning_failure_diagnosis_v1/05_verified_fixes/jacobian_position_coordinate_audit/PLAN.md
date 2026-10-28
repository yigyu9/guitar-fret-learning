# qpos·native qd·wrist Jacobian 좌표 감사

상태: root 승인 범위의 **CPU 조사와 관찰 준비만** 진행한다. GPU는 root의 후속 인계 전 금지한다. 소유권은 이 새 폴더뿐이며 활성 소스·기존 raw/봉인·gain 실험은 보존한다. 설치된 native velocity 좌표는 아직 확정하지 않는다.

- [x] CPU: 원본 검지 영상 env0의 시계·qpos/FK/body·COM 원점속도·중앙 qpos 차분/native qd를 분리 검산.
- [x] CPU: local spherical_joint.py의 quat2expcoord 함수를 AST로만 읽어 qpos exp-coordinate 근거 확인(예제 실행/import 금지).
- [x] CPU: precontrol q[k−1]/body[k−1]와 next goal/delta[k] 정합 및 FK qpos-J DLS/원래clip 차이 기록.
- [x] 단1조건 관찰 wrapper: 원래 index_reference/4환경/own initial checkpoint/teacher/control/PD/힘/범위/정책·실패·보상·clock 불변.
- [x] before ShortPool.step startclock476/596/716/776에만 q/qd/body/COM/전체 human nativeJ clone(각4×65×6×105), bounded 약3MB.
- [x] CPU strict/pin·출력보호·관찰시각/형/복원·원래validator 재사용 검사와 독립 change-review.
- [ ] root만 후속 GPU 실행, 실제 동시-frame nativeJ 확보 뒤 qpos-J와 velocity-J의 frame/row/column/COM 비교.

1단계는 기존 `native_video_index_reference/poses_env0000.npz`와 실제 metadata·teacher·prepared035의 full_fk를 사용한다. raw는60Hz endpoint이며 같은 row의 wrist feedback은 직전 control-start 상태에서 계산됐다. control tick120/150/180/195의 feedback을 비교할 precontrol clock은476/596/716/776다. qpos 중앙차분은 시간 평균 근사이며 native qd와의 차이를 곧바로 좌표 오류로 확정하지 않는다.

FK Jacobian은 qpos perturbation에서 world 위치와 `Rp*Rm.inv()`의 world angular derivative로 구한다. 손목 원점 실속도는 body의 COM velocity에 `omega×Rbody(−COM)`를 더한다. nativeJ의 linear 행도 같은 원점으로 바꾸어야 하며 각속도 행과105열/손목 body−1 행을 명시한다. 현재 q→FK pose 일치는 velocity 좌표 일치를 증명하지 않는다. local quat2expcoord의 position 예제는 설치 qpos 의미의 근거이며 velocity frame의 증거로 확대하지 않는다. 외부 PhysX 버전 문서를 설치 Preview4의 증명으로 쓰지 않는다.

2단계는 기존 strict runner·run_child·other_finger validator를 재사용해 원래 initial.pt reference 평가 한 번만 관찰한다. action·target·gain·damping·trajectory·native 상태를 덮어쓰지 않고 원래 step을 정확히 한 번 호출한다. 새 v계약은 관찰만이며 원래 checkpoint/config identity 검사를 완화하지 않는다. bounded clone과 hook만 새 pin에 추가한다. existing out은 native import보다 먼저 거부하고 원래 exclusive output의 dev/inode 소유권 안에서만 새 capture/report를 쓴다.

모델·업데이트·RNG·초기 checkpoint·소스/자산/teacher·원래4시도 원장·scene closed를 검사한다. 시각/형/finite/샘플수·원래4substep 및 원장/분모를 보존하고, 원래 평가·영상과의 실제 동일성 여부를 별도 기록한다. 오류는 새 output에 보존하고 숨은 rerun을 하지 않는다. CPU로 충분하지 않은 nativeJ 좌표는 미확인으로 남긴다. 좌표 변환·생산 코드 수정·gain 탐색·기존 결과 소급 재분류는 이 작업에서 하지 않는다.

CPU 준비 독립검수 PASS: review_policy_load. 네 시점 actual observer class fixture 및 실패/reset mask·전체clone 독립성·원래670pin/73tensor·출력/깨진symlink 보호 재검산 통과. 최종봉인 뒤 root의 단1조건 실제관찰만 남았다.
