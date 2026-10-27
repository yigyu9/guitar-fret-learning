# 기타 안정성 비중을 높인 실제 학습

2026-10-12 사용자 요청에 따라 **위치·회전 이탈 비용을 각각4배로 올려 실제 CUDA 학습을 시작했다.** 스트랩 ON/OFF는 각각 별도 실행한다. 기존 계획·소스·체크포인트·영상을 보존했다. 아직 기타 안정화나 연주 성공을 달성한 것은 아니다.

## 새 보상과 정책 초기화

| 항목 | 이전 초당 raw 계수 | 새 초당 raw 계수 |
| --- | ---: | ---: |
| 기타 위치 허용범위 밖 Huber 비용 | −2 | **−8** |
| 기타 회전 범위 밖 upper-distance proxy Huber 비용 | −1 | **−4** |

범위 내 비용은0이다. 초기 한 점으로 강제 복원하지 않는다. 압현·타현·sounding·음악 이벤트·몸통·목표 변화율의 기존 계수는 유지했다. 예를 들어 한 축에서5cm 이탈한 경우 위치 비용은 raw −1/초→−4/초다. 전체 reward scale0.1과60Hz 적분은 그대로다.

control당 raw 하한을−2→−8로 낮춰 강화한 비용이 이전 하한에 잘리는 것을 방지했다. 안전 종료 비용도 새 하한으로 남은 구간을 정산한다. **최종 전체 scalar 보상 자체가4배인 것은 아니다.** 두 이탈 항만4배이며 음악·기타 항과 floor/안전 정산은 별도로 합쳐진다. raw component·unfloored·정산 후 raw·scaled를 각각 기록한다.

원본 ON92회·OFF127회 체크포인트의 Actor·log_std·RMS를 그대로 이관했다. 실제 t0+32개 관측에서 action/latent/log_prob 오차0이었다. 새 보상이므로 Critic·Adam·새 갱신 카운터는 새로 시작했다. 상체81·825관측·512→256·몸통 작은 목표 범위·고정root/하체·self-collision·원본 스트랩 길이·준비2초·Fret035000/Strike010000 연결은 유지한다. 이전 보상의 정확한 재개가 아니라 정책 이관이다.

## 실제 실행 검증

순수 검사5개와 [실제 runtime 대조](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/runtime_verification_v2.json)가 통과했다. 실제 controls의 위치/회전 비용이 새 계수로 계산됐고 raw ledger 오차는 두 조건 모두0이었다. 실제 baseline 가중치 불변·금지 API 없음·스트랩 ON13회/물리step 및 OFF힘0·입력SHA·영상SHA도 확인했다.

검증 기록 시점의 새 보상 갱신은 ON6회/1536전이, OFF1회/256전이다. 두 실행 모두 실제 최적화가 수행됐다. 이후 계속 바뀌는 진행 상태는 `progress.jsonl`, 각 `training.jsonl`과 `.exit.json`으로 확인한다. launcher는 Python 실제 종료 코드를 보존하며, 현재 최종 종료 기록은 아직 없다.

이전 ON 실행은 마지막118회 로그 뒤 프로세스가 없어졌으나 최종 보고서가 없어 종료 원인을 확정할 수 없다. OFF는 보상 전환을 위해 중단했다. 검증된 원본 체크포인트·입력 불변성은 [전환 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/transition_v1.json)에 보존했다. ON92/OFF127의 학습 이력이 다르므로 이후 결과 차이를 스트랩만의 효과로 해석하지 않는다.

## 이관 직후 초기 평가와 실제 영상

아래 평가는 **새 보상 학습 전의 이관 정책**이다. 강화한 보상에 따른 성능 개선 평가가 아니다.

| 조건 | 실제 평가 경과 | 종료 | 위치 범위 밖 표본 | 음악 성공 |
| --- | ---: | --- | ---: | ---: |
| ON | 7.5667초 | 오른 팔꿈치 실제 속도99.66rad/s로 안전 종료 | 53.52% | 0 |
| OFF | 16.3667초 | 계획한 전체 구간 완료 | 95.11% | 0 |

ON은 짧게 종료됐으므로 표본 이탈률을 OFF 전체 구간과 직접 비교하지 않는다. 두 조건 모두 현재 안정화·음악 성공 기준에 미달한다. 영상은 실제 종료까지이며 가짜 정지 프레임으로 전체 곡 길이를 채우지 않았다.

![스트랩 ON 이관 직후 초기 평가: 안전 종료까지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/long_on_v1/evaluations/initial_000000/native/episode_0001/media/whole_body.mp4)

![스트랩 OFF 이관 직후 초기 평가: 전체 구간](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/long_off_v1/evaluations/initial_000000/native/episode_0001/media/whole_body.mp4)

![ON t=0 실제 Isaac Gym 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/long_on_v1/evaluations/initial_000000/native/episode_0001/media/frames/whole_body/00000.png)

초기 기타와 양손 배치·원본 스트랩 경로를 보여준다. 주황색은 실제13지점을 투영한 케이블 경로이며 천 스트랩 mesh/두께/처짐을 구현한 모습은 아니다.

![ON t=7.5667초 마지막 실제 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/long_on_v1/evaluations/initial_000000/native/episode_0001/media/frames/whole_body/00227.png)

기타가 아래로 기울고 손 지지를 잃은 실패 장면이다. 이 이미지가 평형 유지의 성공을 뜻하지 않는다. 실제 관절 속도 안전 조건으로 평가를 끝냈다.

## 계속하는 학습과 마감 설정

새 보상에서1회 갱신 평가, 이후30분마다 체크포인트 및 실제 평가 영상을 저장하도록 실행했다. 한국시간11:40 학습 cutoff, 최종 평가11:59 마감 설정은 유지했다. native/최적화 호출 자체는 비선점이므로 시각을 hard deadline으로 인증하지 않는다.

현재 보상은 명시적인 pilot이며 전체 계획의 모든 보상·판정 인증을 완료한 버전이 아니다. 다음 평가는 위치 범위 밖 비율·최대 이탈·회전·안전 종료와 음악 성공을 함께 비교한다. 제어권·gain·초기 상태·스트랩 길이를 추가 변경하지 않고 먼저 강화된 보상의 경과를 본다.

- [x] 새 보상·새 ABI·Actor/RMS 이관 구현 및 순수5검사
- [x] 두 실제 초기 평가·raw ledger 대조·두 조건 실제 PPO 갱신
- [x] [사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/review_preflight_v1.md)
- [ ] 후속30분 평가·마지막 체크포인트·안정성 및 음악 결과 판단

[메인 소단계 계획](/home/ajou/yigyu/3/stability_adapter_2/STABILITY_PRIORITY_TRAINING_V1.md:1) · [변경 파일의 절대 경로·실제 줄 번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_priority_training_v1/CHANGED_FILES.md:1).

보존 메모: 첫 offline 검증 producer는 NumPy bool JSON 직렬화로 결과 파일을 쓰지 못했다. 원본v1과 실패 기록을 보존하고 v2에서 Python bool로만 변환했다. 물리·학습·보상 수식은 바꾸지 않았다. 완료된 초기 평가의 검증 범위와 진행 중 학습을 구별한다.
