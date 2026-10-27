# 전체 상체 공동 정책 v2 독립 검수

**요약 판정: 문제없음.** 최종 설계·그림·설명·메인 추가 기록에서 수정이 필요한 오류를 발견하지 않았다. 이 판정은 문서 정합성에 대한 것이며 구현·물리 응답·학습 성능을 인증하지 않는다.

- Critical: 없음.
- Warning: 없음.
- Suggestion: 없음.

## 검수 범위

[설계 원문](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_JOINT_POLICY_DESIGN_V2.md:1), [결과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_learning_design_v2/README.md:1), [그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_learning_design_v2/architecture.png), [행동 이름 후보](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_learning_design_v2/upper_body_action_manifest_candidate.json), [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_body_learning_design_v2/CHANGED_FILES.md:1)과 이번 메인 추가 구간만 검토했다. 추가 구간은 [PLAN:737](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:737), [모듈 README:1910](/home/ajou/yigyu/3/stability_adapter_2/README.md:1910), [결과 README:601](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:601), [VISUAL_REPORT:2359](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2359)다. 검수자는 이 review.md 외의 파일을 수정하지 않았다.

## 확인한 근거와 계약

- [설계:14](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_JOINT_POLICY_DESIGN_V2.md:14): 몸통9+목/머리6+왼쪽33+오른쪽33=81의 이름·순서·비중복 및 source SHA를 저장된 native `joint_names`와 직접 대조했다. 정책이81 전체 목표를 소유하고 상체 held 채널은0이며 root/하체는 행동에서 제외된다. 몸통·머리의 작은 움직임은 soft 선호로 명시하여 행동 제외나 실제각 고정과 구분한다. 저장된81관절 PD 속성은 모두 POSITION driveMode=1 및 양의 stiffness이며, 이 확인을 새 물리 응답 검증으로 해석하지 않는다.
- [설계:36](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_JOINT_POLICY_DESIGN_V2.md:36): Actor는 D→512ELU→256ELU→평균81/log_std81, 별도 Critic은 D→512ELU→256ELU→value1이다. [기본 모델](/home/ajou/yigyu/3/tab2body/learning/models.py:211), [Fret-v2 fusion](/home/ajou/yigyu/3/tab2body/learning/fret_v2_model.py:49), [Strike-v2 fusion](/home/ajou/yigyu/3/tab2body/learning/strike_v2_model.py:54)의512→256 근거와 일치한다. 외부 [Humanoid SAC 설정](https://github.com/isaac-sim/IsaacGymEnvs/blob/main/isaacgymenvs/cfg/train/HumanoidSAC.yaml)의512/256과 [Humanoid PPO 설정](https://github.com/isaac-sim/IsaacGymEnvs/blob/main/isaacgymenvs/cfg/train/HumanoidPPO.yaml)의400/200/100도 공식 원문과 대조했다. 네트워크 폭 일치로 checkpoint 호환이나 최적 성능을 주장하지 않는다.
- [설계:40](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_JOINT_POLICY_DESIGN_V2.md:40): 초기 mean head weight=0과 역tanh bias, 초기값의 한계 경계 처리, native 한계 목표와 제어 주기당 한 번의 rate 제한이 명확하다. sampled action/log-prob·요청 목표·실제 제출 목표/history를 구분하고 기존 PI/EMA를 자동 중첩하지 않는다.
- [설계:48](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_JOINT_POLICY_DESIGN_V2.md:48): 전체81 실제 상태·양측 손/피크·음악 event/detector/tracker·접촉과 유효 마스크가 관측 후보다. 현재G 속도에 기타 병진/회전을 반영하고, world actor-root 범위와 Pelvis 상대 body-center 범위를 혼합하지 않는다. D manifest와 회전집합 판정은 미완료이며 검증 전 완성된 신호로 취급하지 않는다.
- [설계:58](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BODY_JOINT_POLICY_DESIGN_V2.md:58): 압현/타현·기타 범위·자연스러움을 분리해 평가한다. 음악 과제가 압현부터 시작해도 행동 차원81을 유지한다. 범위 내 초기점 복원 비용0, 영구 접촉 강제 없음, 원본 음악 판정 보존과 교사 의존0 가능성도 일관된다. 실제 행동 시험·backend·준비/clock/episode 종료 계약은 pilot 전 검증 대상으로 남긴다.

## 대조 결과와 검증 한계

동결 원문의 SHA-256은 `1478002dbc12b67428d6a9f172e26656db20841f4f8f4774658c147bc9cf8b6b`이며 직접 계산한 값과 결과 README가 일치한다. 설명의 원문 끝 행 표시는 최종64–73행으로 확인했다. 2000×1400 PNG를 직접 열어 전체81 관측·Actor81·별도 Critic1·native 한계/rate·단일81 PD 제출·환경 feedback을 대조했다. 그림에는 held 상체 채널이 없으며 제안·미구현·미실행 표시가 있다. 메인 추가 기록도 v1의33/held48/256→256 제안을 과거 이력으로 구분한다.

이번 검수에서 새 native 환경 생성·physics step·네트워크 forward/backward·PPO 학습은 수행하지 않았다. 관측/행동 manifest 구현, 현재 환경과 이름·한계 대조, 회전집합·분포·rate/제출 구현 검사, 실제5초 행동 시험과 학습 성능은 후속 작업이다. 기존 파일 보존 감사와 최종 봉인은 root 담당이다.
