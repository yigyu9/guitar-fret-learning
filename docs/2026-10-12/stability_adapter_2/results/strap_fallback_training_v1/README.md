# 기타 이탈 대응: 원본 스트랩 OFF/ON 비교와 학습

2026-10-12. 스트랩 ON을 우선 후보로 두고 OFF 비교 학습도 진행한다. 원본 길이·탄성·감쇠를 그대로 사용했으며, 기타는 자유 물체다. 고정·강제 손 부착·지속적인 pose 덮어쓰기는 사용하지 않는다. **현재 결과는 안정화 및 연주 성공 기준을 만족하지 못한다.**

## 완료된 초기 비교

두 조건은 같은 실제 초기 상태와 같은 정책·정규화 값에서 시작했다. Fret035000·Strike010000 baseline을 함께 사용했다. PREP 2초를 포함한 실제 전체 평가 구간은 16.3667초다.

| 측정 | 스트랩 OFF | 스트랩 ON |
| --- | ---: | ---: |
| 초기 기타 원점 대비 최대 이동 | 1.143 m | 0.584 m |
| 초기 quaternion 대비 최대 회전 | 121.20° | 96.50° |
| 위치 허용범위 밖 제어 표본 | 84.01% | 84.62% |
| 음악 성공 이벤트 | 0 / 42 | 0 / 42 |
| 실제 평가 종료 | 전체 구간 | 전체 구간 |

스트랩은 큰 이동을 줄였지만, 범위 내 유지·자연스러운 회전·음악 성공을 해결하지 못했다. 이 수치는 현재 환경의 **기타 actor 원점**과 현재 허용범위를 사용한다. 팀원의 바디 중심 기준 허용범위에 대한 인증 결과로 해석하지 않는다.

![실제 Isaac Gym 전신 비교: 왼쪽 OFF, 오른쪽 ON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/comparison_whole_body.mp4)

[손 확대 비교 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/comparison_hands.mp4) · [원본 카메라 프레임과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/README.md:21) · [측정 그래프와 정의](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v2/README.md:13).

![초기 비교의 실제 측정 그래프](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v2/measured_traces_external_legend.png)

그래프는 허용범위 밖 위치 거리, 초기 대비 회전, 적용 장력 명령을 보여준다. `last_applied_tension_n`은 관측 시점의 **직전 물리 적분에 제출된 케이블 장력 명령**이며 센서 접촉력이 아니다. 산출물 v2 README:23의 ‘다음 적분’ 표현은 이 문장의 정의로 정정한다. 소비된 원본 문서는 보존했다.

## 스트랩과 제어 구조

- 원본 자연 길이 1.1018469719600776 m, 강성 6000 N/m, 감쇠 120 N·s/m, 장력 상한 300 N. 길이 조절은 하지 않았다.
- 실제 초기 경로 길이 1.0735773343407773 m로 약 28.27 mm 느슨하다. 늘어난 경우에만 힘을 적용한다. 기타 양 끝 및 Chest·L_Thorax의 기존 경로에 반력을 함께 적용한다.
- 기존 820차원 상태에 스트랩 사용 여부·경로 길이·자연 길이·길이 변화율·현재 활성 장력 5개를 추가했다. 정책은 825 입력, 512→256, 상체 81개 제어다. 몸통 목표 제한과 변화율 제한은 유지한다.
- 기존 820 정책을 새 입력 열의 가중치 0으로 확장해 초기 동작·가치·정규화를 대조했다. 두 모드의 새 학습은 각각 빈 Adam 상태에서 시작했으며, 이후 같은 모드의 새 체크포인트만 정확히 이어받는다.
- 유한한 실제 관절 속도가 안전 상한을 넘으면 실제 종료를 기록하고 새 환경에서 수집을 이어간다. 비유한 물리 상태는 학습 실패로 남긴다. 조기 안전 종료로 음의 보상을 회피하지 못하도록 남은 구간을 고려한 패널티를 적용했다.

## 짧은 학습과 실제 reset 검증

각 조건에서 실제 PPO 12회 갱신, 학습 전이 3072개를 완료했다. 초기·1회·12회 체크포인트마다 실제 Isaac Gym 영상을 저장했다. baseline 가중치와 실행 입력은 보존되었다.

12회 평가에서 OFF는 4.55초에 오른 팔꿈치 실제 속도 99.55 rad/s로 안전 종료했다. ON은 16.3667초 전체 구간을 실행했지만 위치 범위 이탈 95.62%, 음악 성공 0회였다. **OFF의 짧은 구간 이탈률을 ON의 전체 구간 이탈률과 직접 비교하지 않는다.**

[실제 reset 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/reset_probe_v2/report.json)는 OFF 체크포인트에서 같은 4.55초 종료를 재현하고, 같은 수집기가 새 초기 장면에서 남은 27개 전이를 수집했음을 확인했다. 총 300개 진단 전이이며 추가 최적화는 0회다. 최초 진단 v1은 입력 ABI가 달라 로드가 거절되었고 물리 적분은 0회였다. 실패 기록도 보존했다.

앞선 `deadline_training_v1/long_run_v3`는 9회 갱신·2304개 전이 이후 안전하지 않은 상태 검사로 중단되었다. 당시 로그에는 정확한 관절 속도가 없으므로 이번 오른 팔꿈치 수치를 이전 실패 원인으로 단정하지 않는다.

## 진행 중인 정오 마감 학습

`long_on_v1`과 `long_off_v1`은 각각 위 12회 체크포인트에서 새 물리 에피소드로 이어서 실행한다. CUDA 정책·PPO와 CPU PhysX를 사용한다. GPU 드라이버 재설치는 필요하지 않았다.

30분마다 체크포인트와 실제 평가 영상을 저장하고, 한국시간 11:40 학습을 끝내 마지막 영상을 11:59까지 만들도록 설정했다. 프로세스 상태와 최근 실제 갱신은 [진행 확인 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/long_progress_verification_v1.json)에 있다. 진행 중인 학습의 성공이나 정오 산출물 완료를 미리 판정하지 않는다.

장기 실행의 `initial_000000.pt`는 실행 시작 시 저장한 파일명이다. 내부 학습 이력은 **갱신 12회·전이 3072개**이며 처음부터 학습한 0회 정책을 뜻하지 않는다. 각 평가의 실제 학습 이력·종료 원인은 `evaluation.json`과 native `report.json`으로 확인한다. 안전 종료 영상은 마지막 실제 프레임에서 끝낸다.

현재 `strap_fallback_pilot_v3`는 마감용 진단 보상이며 전체 계획의 모든 보상 항목을 구현·인증한 버전이 아니다. 특히 음악 성공 0회이므로 연주 학습 완료로 부르지 않는다. 다음 판단은 스트랩 ON의 범위 내 유지, 왼손 지지 및 음악 이벤트 개선을 실제 체크포인트 평가로 확인하는 것이다.

## 검증과 보존

- [x] 원본 스트랩 고정값 ON/OFF 구현 및 초기 정책 동일성 검사
- [x] 순수 검사 native 11개·warm start 3개 통과, 실제 CUDA 확장 검사
- [x] 두 조건 12회 갱신·6개 실제 평가·안전 종료 후 실제 reset 확인
- [x] 영상·그래프·원본 프레임 보존 및 별도 검수
- [ ] 30분마다 장기 학습 체크포인트와 실제 평가 완료
- [ ] 마지막 체크포인트·영상·음악 성능 판단

[실행 및 산출물 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/review_v2.md) · [시각화 보완 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/review_v3.md). 변경 파일의 실제 위치는 같은 디렉토리의 `CHANGED_FILES.md`에 기록한다. 기존 stability_adapter와 소비된 실험 파일·실패 기록은 수정하거나 삭제하지 않았다.
