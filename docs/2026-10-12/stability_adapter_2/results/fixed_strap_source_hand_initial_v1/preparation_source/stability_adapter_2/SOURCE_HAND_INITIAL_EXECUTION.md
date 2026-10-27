# 손5관절 초기 배치의 직접 native 검증 실행

기존 FIXED_STRAP_SOURCE_HAND_INITIAL_PLAN.md의 한 후보를 실행한다. 목표는 원본 연주정책 범위에 접근하면서 자유 기타의 초기 이동·회전과 지지 손자세를 실제로 확인하는 것이다. 범위 안이라는 사실만으로 안정화 성공을 선언하지 않는다. Strap은 LA1.1018469719600776m로 유지한다. 앞선 no-strap 별도비교는 보존한다.

1. initial_middle3_alignment_v1에서 LH thumb1_x/y,thumb3,index1_x,ring1_x의 실제초기와유지목표를 각각 가장 가까운 source/native/normalized 교집합의float32 1ULP안쪽으로 바꾼다. 다른76초기각/유지목표·손목파형·G초기p/q·PD/root/하체/몸통목표는 유지한다. 새 trial과 숫자검증을 먼저 저장한다. 기존5관절변경은 최대약0.66rad이며작은팔보정으로설명하지않는다.
2. 원본 runner를 바꾸지 않고 새 entry의 runtime 초기audit로 fresh native실제상태의 human–G/cross-hands/필터정책 self1188/palm상향/81q와PD·G초기동일성을 검사한다. Finger1다축의미검증FK를사용하지않고이전 source_state/FK_pose_matches를전달하지않는다. 물리0step/read-only 검사다. 새로운gate의선행숫자준비통과와geometry검증은구별한다. 기존legacy source/FK gate 명칭은 output adapter가 direct_native_source_gate로표시하고옛scope는출처로보존한다.
3. Gate거절은1초기화0step 실제t0이미지/짧은partial영상·이유·겹침pair를보존한다. Gate통과는같은초기화로1200step5초/두151frame30fps스트랩영상을기록한다. 별도초기화로통과장면을재연하지않는다. 원래의중력/contact/nativePD/수동strap,몸통9PD×2/√2,최종66권한을유지한다. 기타고정·손부착·시작후pose덮어쓰기·학습은추가하지않는다.
4. 기타goal오차/후기변화·실제관절범위/접촉·손자세를대조해다음조정방향을정한다. Source범위가실제연주가능성/해부학적자연성을인증하지않는다는한계를명시한다. Sol분석후Luna가native이미지/영상과설명을정리하고독립검수와보존기록을남긴다.

- [ ] 숫자후보준비 및 사전보존
- [ ] 직접native gate 구현·코드검수
- [ ] 같은초기화0step거절 또는5초실행
- [ ] 실제결과분석·시각화·검수·다음결정

실행소스/메인계획은 /home/ajou/yigyu/3/stability_adapter_2, 결과는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1 에저장한다. 기존입력/자산/결과는수정하지않고새파일만사용한다. 성공기준은임의확정하지않는다.
