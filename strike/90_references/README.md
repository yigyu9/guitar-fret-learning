# 참고 자료

- [Xu guitar 오른손 pick 구현 분석과 이식 결정](LEGACY_GUITAR_PICK_ANALYSIS.md):
  물리 피크 부재, swept marker detector의 재사용/수정 범위, reference·checkpoint 한계와 S0/V2 경계.
- `../../PROJECT_CONTEXT.md`: 프로젝트 결정과 최신 상태.
- `../../docs/archive/plans/task_strike_design.md`: Xu 오른손 환경을 해설한 기존 이식 초안.
- `../../related_work/guitar/env.py`: `ICCGANRightHand` 원본 구현.
- `../../related_work/guitar/cfg/right.py`: Xu 오른손 goal/style 가중치와 discriminator 설정.
- `../../related_work/guitar/assets/right_hand_guitar.xml`: 27DOF 부유손, 빈 `RH:pick` marker와 string endpoint.
- `../../related_work/guitar/assets/right_hand_motions.yaml`: RH scale/strum reference 목록.
- `../../related_work/guitar/assets/motions/scale.json`: 약 39.6 s, 120 Hz RH scale reference.
- `../../related_work/guitar/assets/motions/strum.json`: 약 2.32 s, 120 Hz RH strum reference.
- `../../related_work/guitar/pretrained/right_hand`: 레거시 27DOF 정책. 현재 30DOF actor에 direct load 금지.
- `../../related_work/guitar/dataset/README.md`: raw mocap 구성과 CC BY-NC-ND 4.0 사용 조건.
- `../../docs/guitar-paper-ko.md`: Xu 논문 국문 정리.
- `../../tab2body/env/README.md`: 공유 환경·좌표·충돌·제어 계약.
- `../../tab2body/assets/guitar_asset.xml`: string marker와 `G:pluck_range` 실제 기하.
- `../../tab2body/assets/smpl_mpl_hands_body.xml`: `RH:pick`과 우손 체인.
- `../../tab2body/_gen/strike_report.json`: 정적 초기 도달성 참고값. 동적 성공 증거는 아님.
- `../renders/strike_zone_reference.png`: 실제 string endpoint와 후보 strike 영역 시각화.

## 사용 원칙

- Xu의 재사용 핵심은 **이전→현재 pick marker의 swept 궤적과 유한 string segment**다. 레거시처럼
  `t`만 보지 않고 `0≤s≤1`, 방향, 속도, zone, depth, goal-independent re-arm을 추가한다.
- 레거시에는 물리 plectrum과 pick CONTACT/LOAD가 없다. S0는 marker의 one-shot `RELEASE`를 쓰며
  물리 pick은 [보류 조건](../04_deferred/README.md)에 따라 V2로 분리한다.
- Xu RH reference는 pick/strum style prior의 출발점으로만 사용한다. clip과 raw CSV 모두 전용
  pick marker·attack timestamp가 없으므로 release oracle이 아니다.
- floating-hand clip과 27DOF checkpoint는 현재 어깨 이하 우팔, 30DOF action, p/i/m/a
  fingerstyle 인간 분포를 보증하지 않는다. trajectory teacher/retarget/진단에는 쓸 수 있지만 actor
  direct load는 금지한다.
- 레거시 parent-frame quaternion 버그는 고정 기타가 가린 호환성 유산이다. 현재
  `base.to_guitar_frame`을 유지하고 G1/G2를 위해 버그를 복원하지 않는다.
