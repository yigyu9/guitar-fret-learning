# 논문 주장과 현재 근거 — 2026-10-19

| 본문주장 | 직접근거 | 해석범위 |
|---|---|---|
| Root 고정·하체유한·105/97/8·자유 기타 |[기준config](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/inputs_spine_margin035_v1/baseline_v1.json) · [준비값](/home/ajou/yigyu/3/paper/initial_pose/current_v3/VALUES.md)|학습실제입력;새자세후보자동승계아님|
| 초기 자세개별시험 |[V3결과](/home/ajou/yigyu/3/paper/initial_pose/current_v3/README.md)|다섯개별시험;모든동작같은실행연속성공아님|
| 손별BC 각4/4 |[손별평가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_local_skills_v1/README.md)|한 음·동일준비상태;동시joint성공별도|
| 1132/569관측·39출력 |[joint환경](/home/ajou/yigyu/3/guitar_learning/joint/environment.py) · [정책](/home/ajou/yigyu/3/guitar_learning/joint/policy.py)|두 Actor/중앙reward·cost Critic|
| 실제840전이·PPO 1회 |[report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_joint_v1/ppo_smoke_v1/report.json) · [episode](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_joint_v1/ppo_smoke_v1/episodes.jsonl)|업데이트 전2episode·음악수렴아님|
| 저장 모델안전7초·공동0/1 |[평가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_joint_v1/ppo_evaluation_v1/result.json)|strictload/native한회;다중seed아님|
| 두 Actor실제업데이트 |[독립실행검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_joint_v1/runtime_review_v1.md)|초기→최종가중치/Adam변경;성능향상아님|
| 전곡67음·1969tick·재타현가정 |[task](/home/ajou/yigyu/3/guitar_learning/song/task.py) · [시간표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/score_schedule_v1.json)|구현목표;전체곡성공아님|
| 전곡4096전이·8업데이트·안전완주2회 |[최종보고](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/training_v2/report.json) · [목표집계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/training_v2/song_report.json)|목표134개에서LH2/RH2/협응0, 전곡 음악 성공0/2. 학습 중 수집분|
| 현재500관측·선택이전 |[song환경](/home/ajou/yigyu/3/guitar_learning/song/environment.py) · [이전](/home/ajou/yigyu/3/guitar_learning/song/transfer.py)|공통460물리열·40새열0;원출력 동등성아님|
| 오디오·운지기본경로 |[전처리](/home/ajou/yigyu/3/tab2fingermapping/README.md)|입력생성구현;전체종단간성능아님|


사람모션유사성·음향·현압력·다곡/다중seed일반화·Root자유균형·전곡 숙련을뒷받침하는결과는현재없다. 결과를추가할때설정·분모·타이밍창·정지/동작구간·정확한checkpoint와수집/업데이트후평가를함께확인한다.
