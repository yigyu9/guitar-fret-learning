# 논문 서술과 프로젝트 근거

논문 제목: **From Audio to Full-Body Guitar Performance with a Freely Moving Instrument**

2026-10-12의 프로젝트 기록을 여섯 부분의 초안과 연결한다. 구현과 평가 설정은 현행 코드와
실제 실행 자료를 우선하고, 과거 설계·계획·정정본은 해당 실험의 조건에 맞춰 사용한다.
본문의 결과 표와 조건 설명은 이 색인의 원문에서 확인할 수 있다.

2026-10-13에 제공된 과거 DIGIT 원고와의 대조는 [별도 검토 기록](/home/ajou/yigyu/3/paper/legacy_draft_review.md)에 정리했다. 이 원고는 문제의식과 설명을 보강하는 역사 자료로 사용하며, 현재 성능의 근거로 사용하지 않는다. 추가한 전사 특징·음표 구간화는 [특징 추출](/home/ajou/yigyu/3/tab2fingermapping/conformer/feature_extractor.py)와 [기본 전사 코드](/home/ajou/yigyu/3/tab2fingermapping/conformer/transcribe.py), 프렛 영역 설명은 [현행 Fret 기하·판정](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py)을 근거로 한다.

## 입력과 개별 연주 기술

| 서술 | 근거 | 사용할 범위 |
|---|---|---|
| 오디오→탭·ACE 코드→운지의 기본 경로 |[pipeline.py](/home/ajou/yigyu/3/tab2fingermapping/pipeline.py), [Stage1 README](/home/ajou/yigyu/3/tab2fingermapping/README.md) |오프라인 구현 흐름. 원평가를 확보하지 않은 과거 F1을 전체 시스템 성능으로 사용하지 않음 |
| 탭의 줄·프렛을 유지하는 finger 배정 |[assign.py](/home/ajou/yigyu/3/tab2fingermapping/fingermapping/assign.py), [ALGORITHM](/home/ajou/yigyu/3/tab2fingermapping/fingermapping/ALGORITHM.md) |프렛 간격·교차·바레·유지 규칙. native 관절·IK 도달성 인증과 구별 |
| 대표 Jazz1 입력의 출처 |[manifest](/home/ajou/yigyu/3/data/song_bundles/02_Jazz1-200-B_solo/manifest.json) |`provenance={}`. 자동 전사·annotation·수정 범위를 추가 추적해야 함 |
| Canonical PlayEvent와 공통 목표 |[events.py](/home/ajou/yigyu/3/tab2body/full/events.py), [G0 상태](/home/ajou/yigyu/3/full/03_implementation/STATUS.md) |CPU compiler·계약과 실제 지속 양손 물리 연주를 구별 |
| Fret420/30/6, Strike303/30/1 |[Fret 계약](/home/ajou/yigyu/3/tab2body/fret_v2_contract.py), [Strike 계약](/home/ajou/yigyu/3/tab2body/strike_v2_contract.py), [Fret 모델](/home/ajou/yigyu/3/tab2body/learning/fret_v2_model.py), [Strike 모델](/home/ajou/yigyu/3/tab2body/learning/strike_v2_model.py) |현행 source 사양. 현재 공동825/81/1과 구별 |
| 대표 Fret의 전체곡 무teacher 결과 |[Fret035000 원자료](/home/ajou/yigyu/3/fret/training/runs/20260911_1710_02_Jazz1-200-B_solo/videos/fret_035000_rollout.events.json) |`episode_metrics.f1_l=0.29298245906829834`, sustain2/35. 한 deterministic 평가이며 학습 평균·다중seed와 다름 |
| 후속 Fret 재학습의 실패 분석 |[Fret047500 원자료](/home/ajou/yigyu/3/fret/training/runs/20261001_2232_02_Jazz1-200-B_solo_synergy/videos/fret_047500_rollout.events.json) |F1·지속·손가락별실패. 평가 계약이 다른 source 결과와 통계적 우열 비교하지 않음 |
| 대표 Strike의 독립 반복 평가 |[Strike010000 평가](/home/ajou/yigyu/3/strike/training/runs/20260920_Jazz1_sync_baseline/evaluations/strike_010000.full_song.eval.json) |F1=1, TP2688/FP0/FN0,42 single gestures×64cases. strict_gate=false·wrong termination 억제,50ms창과 case protocol 명시 |
| 높은 평균 F1와 곡 단위 실패의 차이 |[과거 Strike023000 평가](/home/ajou/yigyu/3/strike/training/runs/20260911_2235_02_Jazz1-200-B_solo/evaluations/strike_023000.full_song.eval.json) |평균 지표와 clean full-song rate의 차이. 최신 source의 결과로 합치지 않음 |

## 현재 공동 제어와 물리

| 서술 | 근거 | 사용할 범위 |
|---|---|---|
| 전신 장면과 root·하체 fixed, 상체81 |[실제 학습 구조](/home/ajou/yigyu/3/docs/2026-10-12/Meeting/06_StabilityAdapter2_현재_학습구조.md), [native 관절 계약](/home/ajou/yigyu/3/stability_adapter_2/environment_contract_v1.py) |Full-Body의 조건 설명. 전 관절 학습·자유 보행 주장과 구별 |
| 825→512→256→81 Actor, scalar Critic |[joint_policy](/home/ajou/yigyu/3/stability_adapter_2/joint_policy_v1.py), [음악 관측](/home/ajou/yigyu/3/stability_adapter_2/joint_learning_observation_v1.py), [현재 구조 설명](/home/ajou/yigyu/3/docs/2026-10-12/Meeting/06_StabilityAdapter2_현재_학습구조.md) |548+191+81+5의 실제 관측. base739·이전820·설계105action과 구별 |
| frozen source nominal과 bounded residual |[nominal guard](/home/ajou/yigyu/3/stability_adapter_2/deadline_support_nominal_v1.py), [residual codec](/home/ajou/yigyu/3/stability_adapter_2/deadline_bounded_residual_v1.py) |팔±0.15rad/왼엄지±0.10rad nominal, 그룹별 추가cap. 원본 행동 완전 재현이 아님 |
| 현재 기타 위치·상대속도와 origin/COM |[encode·relative_motion](/home/ajou/yigyu/3/stability_adapter_2/environment_contract_v1.py), [point_kinematics](/home/ajou/yigyu/3/stability_adapter_2/strap.py) |기타 병진·회전 반영. native COM속도를 origin속도와 혼합하지 않음 |
| 공동 음악 clock와 bracket crossing |[dual_music_clock](/home/ajou/yigyu/3/stability_adapter_2/dual_music_clock_v1.py) |240Hzendpoint bracket·50ms tolerance. 원본 source phase·permission 동등성 인증과 구별 |
| 현재 pilot reward와 PPO |[pilot](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v1.py), [안정성4배](/home/ajou/yigyu/3/stability_adapter_2/deadline_stability_reward_v1.py), [하한·배율](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v4.py), [guarded PPO](/home/ajou/yigyu/3/stability_adapter_2/deadline_guarded_ppo_v3.py) |실행한 dense/pulse pilot. 상세 reward v4 전체 적용으로 설명하지 않음 |
| 기타 actor-root 허용상자와 SO3 upper proxy |[범위 설계](/home/ajou/yigyu/3/stability_adapter_2/PLAYABLE_ENVELOPE_CONTRACT.md), [현재 회전 처리](/home/ajou/yigyu/3/stability_adapter_2/deadline_rotation_v3.py) |위치범위/회전허용집합/초기SO3변화 각각 구별. proxy를 정확 최단거리로 쓰지 않음 |
| 수동 tension-only 스트랩 |[strap law](/home/ajou/yigyu/3/stability_adapter_2/strap.py), [실행 owner·force guard](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v4.py) |13점·L0≈1.101847m·6000N/m·120N·s/m·300N cap. 계산장력과 힘센서 측정 구별 |

## 자유 기타의 실제 실험

| 실험 묶음 | 권위 결과와 원자료 위치 | 본문에서의 해석 |
|---|---|---|
| 개별 Strike 최소2초 준비와 첫done |[Strike2초 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/README.md) |적시타현과 잘못된타현/원본실패종료. 곡완주와 공동음악성공으로 사용하지 않음 |
| Fret 손가락과 팔 지지 분리 |[Fret arm hold](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/README.md) |초기이탈과 압현성공을 분리. 팔 유지 진단을 최종 연주 제약으로 승계하지 않음 |
| 기존 고정 길이 스트랩 Fret 비교 |[Fret strap](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/README.md) |PLAY계산장력0N·압현실패 조건. 전체 strap 효과로 일반화하지 않음 |
| 동결된 양손의 자유 기타 연결 |[dual runtime](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/README.md) |공통clock·관절owner·joint진단 연결과 음악성공 구별 |
| 스트랩·안전 실패를 분리한 학습 |[strap fallback](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/README.md) |관측·ABI·보상·종료 조건이 바뀐 pilot. 과거 no-strap결과와 단일요인우열로 쓰지 않음 |
| 병렬 수집과 생산 학습 |[parallel 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/README.md), [완료검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/completion_verification_v1.json) |CP316→320·음악0/42·관측된 이탈 변화. 수집동작검증과 benchmark 속도우열·학습성능 구별 |
| 검증한5개 초기 pose bank |[noisy 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/README.md), [검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_pose_noise_v1/verification_v1.json) |32제안 중 통과노이즈4+기준1, fixed index평가음악0/42. 연속균일분포·분포성공률이 아님 |
| 상체 전경과 오른상완 초기지지 |[upper-arm 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/README.md) |상수 PD의 무연주5초 비교. 늦은정착을 초기유지로 해석하지 않음 |
| 척추 굽힘과 왼손 철수 |[정정README_V2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/README_V2.md), [손목·손접촉보완](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1/right_hand_contact_audit_v1.json) |처음부터 철수한초기조건, strapON. 손목·손접촉이 있었던 사실과 원하는지지실패를 구별 |
| 현실 비율 바디 |[형상결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/README.md), [정정그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v2/README.md) |자산·배치·strap route가 함께 바뀐 비교, 연주정책 미연결 |
| 어쿠스틱 외관 |[외관결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/README.md) |시각 표현 개선과 물리 제어 성능을 구별 |
| OM 도면 바디 |[OM결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/README.md) |native형상·물성·실제5초, 초기이동 이후 정착. 현행 학습 전체에 적용된 모델로 설명하지 않음 |
| 6현 표시와 기타 집중 시점 |[현표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/README.md), [집중카메라](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_focused_view_v1/README.md) |영상 표시와카메라 변경. 줄의물리·반력·음향모델 아님 |
| OM 가슴·상완 지지 후속 |[계획v4](/home/ajou/yigyu/3/stability_adapter_2/OM_AXILLA_INITIAL_POSE_PLAN_V4.md) |최신main은비교계획단계. 완료된음악·겨드랑이지지성과표에 넣지 않음 |

각 결과의 숫자는 [Result](/home/ajou/yigyu/3/paper/05_result.md)의 조건과 분모를 함께 읽는다.
숫자의 raw key와 비교 조건은 해당 결과의 analysis·verification·controls·trace에서 확인한다.
검사 통과 개수, 영상 생성, 학습 update 횟수는 음악 이벤트 성공 횟수와 별개의 값이다.

## 관련 연구의 근거

문헌의 공식 제목·저자·년도·DOI와 원문 링크는
[Related Work 참고문헌](/home/ajou/yigyu/3/paper/02_related_work.md)에 모았다.
비교는 논문과 저자 자료에서 확인한 악기·모델·입력·학습 조건을 사용한다.
프로젝트의 과거 분석에 있는 “최초”, “노벨티”, 모션 prior의 필요성에 대한 단정은 그대로 승계하지 않는다.

## 추가 근거가 필요한 주장

- 자동 오디오 전사에서 시작한 자유 기타 연주의 전체 성공률과 입력 오류 전파.
- 같은 초기 상태·종료 조건·평가 계약으로 측정한 source·nominal guard·학습 residual의 차이.
- 한 음의 실제 공동 성공에서 전환·구절·곡으로 확대되는 음악과 지지의 동시 성능.
- 여러 seed·검증된 초기 분포·별도 곡의 평균·분산·실패율과 곡별 정책 학습 비용.
- 현재 joint bracket과 source permission·phase의 차이, sounding-state·유지 판정의 검증.
- 실제 몸통·팔·허벅지·손의 지지 기여를 판별할 측정과 형상·route 변경의 분리 비교.
- 사람 데이터 또는 적절한 사용자 평가에 근거한 자연스러움.

초기초안은 이 항목을 후속 실험으로 남긴다. 기존자료의 빈칸을 추정한 성능 숫자로 채우지 않는다.
