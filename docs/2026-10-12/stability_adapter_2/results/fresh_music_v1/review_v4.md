# 음악 정책 초기 탐색 분산 및 제한 qualification 검수 v4

2026-10-15. 독립 change-reviewer 기록이다. 소비된 환경·실행기·이전 결과를 수정하지 않았다. [v3 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/review_v3.md)에 보존된 ±0.8 qualification 실패는 이번 결과로 대체하지 않는다.

## 요약 판정

문제없음. 신규 초기 탐색 조건과 ±0.2 qualification을 거쳐 B scratch 16갱신×256전이가 실제 완료되었고, 최종 checkpoint의 단회 평가도 완료되었다. 추가 Critical은 발견하지 못했다. **압현 유지·해제 후보는 완료되지 않았으며 단음 목표 접근의 실질적인 개선은 미미했다.** 구현과 제한된 학습 수행을 음악 과제 성공과 구분한다. 오류는 여전히 fatal이며 미완료 rollout을 PPO에 넣지 않는다.

## 신규 실행기 검수

[run_v4.py:14](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/run_v4.py:14)는 초기 Gaussian latent의 log standard deviation을 −3으로 설정한다. 초기 latent 표준편차는 exp(−3)≈0.049787이며, 이전 −1 조건과 다른 새로운 탐색 분포다. 분산 파라미터는 계속 학습 가능하고 tanh54 행동 및 환경의 관절 목표 범위는 유지된다. actor mean을 강제로 제한하는 경로나 기존 가중치 이식은 추가하지 않았다.

초기 profile은 attempt와 정확한 checkpoint 재개 계약에 포함된다. 명시적 own-music checkpoint를 불러올 때 새 초기값을 먼저 만든 뒤 저장된 model 전체를 복원하므로 학습된 log_std를 −3으로 덮어쓰지 않는다. 환경은 검수된 v3이며 물리·guard·PPO·기타 보상과 오류 처리에는 추가 변경이 없다. 신규 launcher는 자기 v4 module을 실행한다.

신규 두 테스트가 full tanh 행동 권한, log_std의 학습 가능성, checkpoint의 학습된 −2.7 복원, 다른 초기 profile의 재개 거부를 확인했고 통과했다. 앞서 검수한 31개와 합쳐 총 33개 CPU 테스트가 통과했다. 신규 실행기·초기화 테스트·진단v2 AST 검사와 launcher 문법 검사도 통과했다. 실제 [checkpoint_0000.pt](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/pilot_b16_v4/checkpoint_0000.pt)를 독립적으로 읽어 updates=0, 전체 model finite, log_std54개 모두−3, actor head의 weight/bias 6개 tensor 모두0임을 확인했다. 초기 actor mean=0은 profile 설명만이 아니라 실제 checkpoint로 확인했다.

## native qualification v2

[guard_qualification_v2/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/guard_qualification_v2/report.json)은 입력 변경 없이 전체 7개 조건을 통과했다. 사전 SHA 1,334개를 현재 입력과 독립 재대조하여 변경 없음을 확인했다. 신규 [replay_music_guard_v2.py:94](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/replay_music_guard_v2.py:94)는 replay 명령·prefix 개수 및 원래 실패 통과를 완료 predicate에 연결한다.

| 조건 | controls / physics steps | 확인 결과 |
|---|---:|---|
| 원래 실패한 B 명령 replay | 153 / 612 | 기존152개 native motion·목표·effort exact, 원래 physics611 실패 통과 |
| zero B 및 random ±0.2 B 각각 | 245 / 980 | 선언한 전체 B 시간축 완료 |
| zero C 및 random ±0.2 C 각각 | 251 / 1004 | 선언한 전체 C 시간축 완료 |
| zero D 및 random ±0.2 D 각각 | 475 / 1900 | 선언한 전체 D 시간축 완료 |

alignment 원자료 8,380개에서 선택된 후보의 COM·support gate 최대값은 0.008535099m/s로 기존 0.01m/s 이하였다. 모든 선택은 current였고 previous fallback의 native 실사용은 이번 qualification에서 없었다. 원래 physics611의 current COM/support 잔차는 각각 0.000778946/0.000054587m/s였다. previous COM은 원래와 같은 0.010418709m/s로, v3가 일관된 current 후보를 선택하여 원래 실패를 통과했음을 확인했다.

## 실제 제한 pilot 및 단회 평가

[pilot_b16_v4/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/pilot_b16_v4/report.json)은 16갱신, attempted=valid=accepted PPO steps=4,096, excluded/pending=0으로 완료되었다. commands 4,096개, transitions 4,096개, update records16개, episode_end16개를 독립 대조했다. 오류·금지 API·입력 변경은 없고, 1,332개 사전 입력 SHA도 불변이었다. 마지막 partial episode117의 물리700→704 control 경계가 일관된다. 최대 파라미터 변화는 0.004561866이고, 16개 완료 episode 모두 압현 유지·해제 후보 완료는 false다. 실행 경과 시간은 약218.99초다.

[eval_b16_v4/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/eval_b16_v4/report.json)은 최종 checkpoint0016을 seed9002에서 단회 deterministic 평가했다. attempt의 checkpoint 경로 및 사전 digest가 실제 pilot의 latest_regular_checkpoint와 일치함을 확인했다. initial/final updates는16이며 평가 중 파라미터 변화는0이다. 평가 controls를 누적 학습 전이 수에 더하지 않았다. baseline·학습·평가의 초기 native state 파일 SHA가 같았고, baseline B의 245개 실제 native motion·목표·제출 effort는 이전 baseline_b_v2와 모두 exact였다.

[analysis_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/analysis_v1.json)의 비교 수치를 전이 원자료에서 재계산했다. 같은 B 음의 가청 유지 구간에서 얻은 각각35개 marker-distance 관측의 평균을 사용한다.

| 관측 | zero baseline B | checkpoint0016 단회 평가 B |
|---|---:|---:|
| controls / 물리 시간 | 245 / 4.083333초 | 245 / 4.083333초 |
| 할당 finger marker와 프렛 목표 평균 거리 | 154.192236mm | 154.100654mm |
| reward 합 | 0.298103667 | 0.298292683 |
| 기타 허용 범위 cost 합 | 0.058081117 | 0.050199997 |
| 할당 접촉·기하 유지 시간 | 0초 | 0초 |
| 압현 유지·해제 후보 완료 | false | false |

거리 감소는 약0.091582mm로 미미하며 반복 평가의 효과·일반화·압현 성공을 주장하지 않는다. 같은 B event의 단회 평가이고 다른 곡/과제에 대한 held-out 성과가 아니다. stochastic 학습 중 marker 평균149.6865mm를 위 deterministic 비교의 성능 개선으로 대신 사용하지 않는다. 위치 범위 이탈은0이지만 회전 cost는 feasible upper bound를 사용하므로 cost 감소를 정확한 최단 회전거리나 실제 압현 성능의 개선으로 해석하지 않는다.

PPO의 실제 approx_kl 범위는0.033297803–0.416007161, clip_fraction은0.44140625–0.84765625였다. target_kl=0.03을 넘었다. [ppo.py:90](/home/ajou/yigyu/3/stability_adapter_2/fresh_learning_v1/ppo.py:90)의 검사는 epoch 전체 갱신 뒤 rollout 전체의 log-ratio를 평가하여 다음 epoch를 중단하는 조건이며 hard bound가 아니다. 작은 초기 분산의 실제 학습 진단 한계로 남기며 갱신 완료와 안정적인 음악 학습을 동일시하지 않는다.

## 영상·모션 산출물 확인

B baseline/단회 평가의 native 영상은 각 view124프레임, D baseline은 각 view239프레임이다. 실제 eval 대표 프레임 whole_body/00123.png와 hands/00090.png를 확인했다. humanoid 전신·기타·양손의 큰 구조는 보이지만 작은 줄/프렛 시각 요소와 압력은 명확히 확인되지 않는다. visual geom 경고를 전체 렌더 형상 완전성이나 정확한 줄 접촉 시각 인증으로 해소했다고 주장하지 않는다. 이 확인은 대표 두 프레임의 장면 범위이며 전체 영상의 모든 접촉을 시각 판정한 것이 아니다.

모션 내보내기의 초기 native q81/qdot81·기타 root body state와 각 전이의 실제 native_motion을 모두 재구성하여 출력과 exact 일치함을 확인했다. baseline B246프레임, 평가 B246프레임, D baseline476프레임이며, 최초 상태 한 프레임을 포함한60Hz native 궤적이다. 이미지 프레임 수 및30Hz 영상 재생 길이와 물리 시간·모션 표본 수를 구분한다. 원래 skeleton/assets를 필요로 하며 BVH/FBX retargeting 산출물은 아니다.

[baseline_d_v4/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fresh_music_v1/baseline_d_v4/report.json)의 475controls/7.916667초는 선택한8개 event 전체 시간축을 실행했다는 의미다. 맞춘 string target은0/15이고 압현 유지·해제 후보는 false다. D는 zero 기준 실행이며 학습된 구절 수행 결과가 아니다.

## 판정의 범위

위 qualification은 seed101의 replay·zero·bounded uniform random 분포와 각 선택 과제 길이에 대한 sampling 호환성 검증이다. Gaussian 표본은 ±0.2 안에 강제로 제한되지 않고, 학습 중 actor mean과 log_std도 변하므로 이후 정책의 모든 행동이나 학습 안정성을 보장하지 않는다. previous fallback의 native 분기와 다른 seed·악곡의 결과로 확대하지 않는다. torque Jacobian의 전체 정확성, solver의 원인, 압현·타현 후보 완료와 줄 압력·진동·음향은 인증하지 않는다.

qualificationv1 원본의 inputs_unchanged=false/all_cases_passed=false, ±0.8 세 조건의 both-candidate fatal, v2 pilot의 0갱신 실패는 그대로 보존한다. v2 qualification이 통과했다는 설명과 과거 실행 원본의 보존 판정을 구분한다. 초기 탐색 분포 변경은 새 조건이며 과거 실패의 수치 문턱 완화나 정상 학습 전이 치환이 아니다.
