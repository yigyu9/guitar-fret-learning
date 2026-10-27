# 사전 검수 — 같은 초기값의 몸통 PD 강화

요약 판정: **문제없음. Critical 0 / Warning 2 / Suggestion 0.** 선언된 body9 PD 변경을 적용한 bounded 5초 ON10 진단을 막는 코드/계약 오류는 발견하지 않았다. 실제 두 블록 받침·안정성 결과는 미검증이다.

- [설정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/config_v1/static_body4_ON10.json:1)은 기존 ON10과 같은 candidate/path SHA를 유지한다. 변경은 새 native_reference와 SHA, body_kp_scale2→8, body_kd_scale√2→2√2 및 body_PD_factor4다. Thorax10N·나머지 제어값은 같다.
- 새 reference의 실제 변경은 Torso/Spine/Chest9 stiffness1200→4800, damping212.1320343017578→424.2640686035156뿐이다. 다른72행·기존 다른 모든 필드가 exact이고 effort9는300을 유지한다. reference digest도 일치한다. 과거 native_initial_state는 초기 선언의 역사 자료이며 현재 실행 측정값이 아니다.
- [runner3:40](/home/ajou/yigyu/3/stability_adapter_2/run_right_block_cradle_v3.py:40)는 이전 PD 기대값에서 body9의 K×4/D×2만 계산하고 실제 PD 전체와 exact 대조한다. LearningScene construction의 config scale 적용 및 reference dtype 비교와 맞는다. float32 damping 계산도 실제 reference와 일치함을 확인했다. initial_values에는 이전 reference가 아니라 실제 PD를 저장하도록 바꿨다.
- 기타 fullstate/rootlower/finger42·q_ref/model·질량·FK/source gate와 기존24 EFFORT/57 POSITION·단일81·토크 cap·leftwrist/오른 지원 경로는 그대로다. camera·capture/encode 실패 보존 및 60Hz sample의 finite/속도50rad/s 초과·기타20cm/35° 중단을 유지한다. runner3 AST는 통과했다.
- 기존 분석기는 initial_verification.invariants를 검증하므로 선언된 PD 변경과 호환된다. 현재 실제 실행의 actual PD/readback 및 원자료 입력 SHA는 후속 검수에서 확인해야 한다.

Warning 1 — 유한 native POSITION PD 강화는 실제 몸통 자세 고정이 아니다. effort300을 유지하므로 요청 포화와 실제 오차가 남을 수 있으며 안정화를 보장하지 않는다. body 움직임과 초기근접 상실이 동반 관측됐어도 이 실험 전 원인분리는 하지 않았다. 실제 q/qdot·접촉·기타 위치/회전을 보고 판단해야 한다.

Warning 2 — 이전 OFF0/ON10의5초 완주 및 후반 정착은 두 블록 지지 성공이 아니다. Thorax0/상완 희소 접촉과 LH:thumb3–넥 접촉·허벅지 접촉을 구분한다. 강화 조건 역시 왼손/허벅지 기여를 배제한 받침 인증, cooked 전체 안전 또는 팔꿈치 동작 검증으로 확대하지 않는다. 동일 강화 조건의 정지/동작 비교는 별도의 실제 결과가 필요하다.

검수는 native 계획V3·runner diff·새 config/reference 전체 필드 및 digest·float32 gain 산술·분석기의 PD 판정 경로에 한정했다. 추가 native/학습/추론과 다른 담당 소스/결과 편집은0이다.

검수 SHA256:

- 계획V3: `2515c080b3222f8916875fbbe4a40428d5ad3f517a70cbebe193a1af32266c14`
- runner3: `98202fc34b7fafeb29fa9cafaa7079d7ef4fffc5cd81217dc6f6ab27c63e998c`
- config: `c2537ae4d1bf44623bb3bd12e3d4e5504963def9598f9a695b87fd11c189cce6`
- reference: `415eda3cca0a2adee556f245a293cd379ad084cd18537814c0694d1ff8a504cc`
