# 왼손 공동 정책 설계 독립 검수

**요약 판정: 문제없음.** 최종 설계 문서와 그림에서 수정이 필요한 오류를 발견하지 않았다. 이 판정은 문서의 정합성과 검증 계획에 대한 것으로, 네트워크 구현·학습 성공·실제 물리 성능의 인증이 아니다.

- Critical: 없음.
- Warning: 없음.
- Suggestion: 없음.

## 검수 범위

- [설계 원문](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_JOINT_POLICY_DESIGN_V1.md:1), [결과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_hand_learning_design_v1/README.md:1), [설계 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_hand_learning_design_v1/architecture.png), [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_hand_learning_design_v1/CHANGED_FILES.md:1).
- 메인 문서의 이번 추가 구간: [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:712), [모듈 README](/home/ajou/yigyu/3/stability_adapter_2/README.md:1901), [결과 모음 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:594), [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2350).
- Git status로 기존 작업이 다수 존재함을 확인한 뒤, 위 범위와 그 주장을 확인하는 근거 자료만 검토했다. 검수자는 이 파일 외의 문서·코드·설정을 수정하지 않았다.

## 확인한 계약과 근거

- [설계 원문:17](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_JOINT_POLICY_DESIGN_V1.md:17): 왼손33 단일 정책, held48, native81 단일 제출과 최종 양측66 권한을 구분한다. `native_name_partition.json`의 33/33/48 개수, left와 held의 비중복·합집합81, 오른쪽33의 held 포함 및 근거 파일 SHA를 읽기 전용 검사로 확인했다.
- [설계 원문:29](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_JOINT_POLICY_DESIGN_V1.md:29): PD 목표 유지와 실제 관절 고정을 구분하여 native81 실제 q/qdot를 관측 후보에 포함한다. 음악 event 시간·활성과 현재 detector/sustain 상태, 양측 접촉·조회 유효 마스크를 구분한다. 현재G 속도에 기타 회전도 반영하며, world actor-root 경계와 Pelvis 상대 관측을 혼합하지 않는다. 회전 허용집합 신호는 검증 전 사용하지 않는다.
- [설계 원문:44](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_JOINT_POLICY_DESIGN_V1.md:44): Actor/Critic은 독립된 D→256ELU→256ELU 구조이며 출력은 각각 평균33/value1이다. D와256/PPO의 효과가 미확정 제안임을 명시한다. 평균 head weight=0과 역tanh bias로 초기 deterministic 목표를 정의하고, 한계 경계값의 불가능성을 별도 처리하도록 한다.
- [설계 원문:57](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_JOINT_POLICY_DESIGN_V1.md:57): 절대 native 한계 목표, 60Hz control 주기당 한 번의 rate 제한, 240Hz physics의 네 step 동안 목표 유지, sampled action/log-prob와 실제 q_final/history의 분리가 일관된다. 기존 PI·엄지 servo·EMA 중첩은 자동 적용하지 않는다. 속도 한도와 이벤트 도달 가능성은 실행 전 검증 대상으로 남긴다.
- [설계 원문:67](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_JOINT_POLICY_DESIGN_V1.md:67): 음악 수행과 허용범위 유지가 함께 평가된다. 범위 내 초기점 복원 비용0, 영구 접촉 강제 없음, 원본 음악 판정 보존과 독립 지표 평가를 명시한다. 새 학습의 episode·준비 제어·clock 계약과 backend 차이는 pilot 전 확정하도록 한다.
- [설계 원문:79](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_JOINT_POLICY_DESIGN_V1.md:79): 기존 체크포인트를 검증된 자유 기타 전문가로 취급하지 않는다. 가중치/관측/action 호환 조건과 동일 budget의 scratch 비교, 유효한 성공 구간의 조건부 교사 활용 및 교사 의존0 가능성을 명시한다.

## 대조와 검증 한계

원문 SHA-256 `60e65b492f154b62e2ef17859525d716e17da815dc42a07f9e6bebff75657d1c`를 직접 계산하여 결과 README의 동결값과 대조했다. 기존 Fret 지속 운지2/35는 [전이 근거](/home/ajou/yigyu/3/stability_adapter_2/FRET_TRANSFER_FEASIBILITY.md:7), 직전 support 네 조건의 수치는 [원자료 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/README.md:24)과 일치한다. 이 기존 수치를 새 정책의 성능으로 설명하지 않는다.

2000×1400 설계 PNG를 직접 열어 읽었으며, native81 관측·Actor33·별도 Critic1·native 한계/rate 제한·33+held48 단일81 PD 제출·환경 feedback이 원문과 일치한다. 그림은 제안·미구현·미실행임을 표시하고 실제 native 렌더로 설명하지 않는다. 세 방법의 인용 범위도 공식 초록과 대조했다: [Residual RL](https://arxiv.org/abs/1812.03201), [Kickstarting](https://arxiv.org/abs/1803.03835), [Asymmetric Actor Critic](https://arxiv.org/abs/1710.06542). 해당 연구를 이 기타에서의 우월성 증거로 쓰지 않는다.

이번 검수에서 새 native 환경 생성·physics step·네트워크 forward/backward·PPO 학습은 수행하지 않았다. D manifest, 회전 허용집합, detector, 행동/초기화/rate 구현, 실제5초 행동 시험과 학습 성능은 원문의 후속 체크리스트에 남아 있다. 최종 보존 감사와 봉인은 root 담당이다.
