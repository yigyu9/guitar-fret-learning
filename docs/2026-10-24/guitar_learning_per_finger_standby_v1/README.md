# 손가락별 약한 B 대기 보상 — v17

이전 v16은 손가락 하나가 준비·접촉·목표 근접 상태이면 손 전체 B 보상을 껐다. v17은 검지·중지·약지·소지를 따로 판단한다. 예를 들어 약지가 연주 중이어도 쉬는 다른 손가락이 각자의 제외 조건에 해당하지 않으면 B 권고를 받는다. 엄지 보상은 이번 변경에 포함하지 않았다.

## 현재 동작

각 손가락 f에 대해 다음을 계산한다.

```text
G_f = idle_f × NOT(contact_f OR near_f)
R_standby_rate = 0.01 × sum_f(G_f × B_quality_f) / 4
```

- 시간: 본인에게 배정된 음의 press−2~end에는 본인만 0이며, 창 바깥 0.25초의 fade를 유지한다.
- 접촉: 본인의 첫·중간·끝마디 중 하중 0.01N 이상, 또는 본인 배정 목표의 이전/현재 candidate·wrong가 있으면 본인만 0이다. 다른 손가락의 접촉은 직접 차단하지 않는다.
- 근접: 본인에게 배정된 모든 곡 목표 중 패드 거리가 4cm 이하이거나 비유한 값이면 본인만 0이다. 이 검사는 시간창 밖의 목표도 포함한다. 미등장 손가락은 시간 idle 1이며 배정 목표가 없으므로 거리 차단도 없다. 빈 곡은 전체 0이다.
- 크기: 고정 4분모를 유지하므로 손가락당 최대 +0.0025/초, 손 전체 최대 +0.01/초다. 쉬는 손가락이 줄어들어도 남은 손가락의 계수는 커지지 않는다.
- 자세: 같은 B 투영 중심·관절별 ±15도 평탄 대역·밖 30도 scale의 부드러운 감쇠다. 범위 밖 새 벌점·강제 관절 목표·필수 경유 자세는 없다.

실패 tick의 양성 보상 억제, 240Hz 적분, 기존 approach 계수 1을 유지한다. 관절 분담은 계속 0이고 LH21 움직임 비용도 0이다. 엄지·벌림 보상, 관절 한계·PD·제어·초기 자세·물리·PPO·접근·압현·성공 판정은 변경하지 않았다. 본인 준비/접촉 중 직접 자세 보상은 없지만, 공유 정책과 물리 상호작용을 통한 간접 영향이나 성능 효과는 새 학습 없이 보장하지 않는다.

## 코드와 저장 계약

[finger_reward.py](/home/ajou/yigyu/3/guitar_learning/gpu/finger_reward.py)의 `finger_preparation_reward`는 `contact[N,4]`와 손가락별 `gate[N,4]`를 사용한다. [environment.py](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py)는 마디 하중과 목표 소유 손가락별 접촉 사건을 N×4로 모아 전달한다. [specialist_policy.py](/home/ajou/yigyu/3/guitar_learning/skills/specialist_policy.py)와 [curriculum_runtime.py](/home/ajou/yigyu/3/guitar_learning/song/curriculum_runtime.py)는 새 버전에서도 손가락별 Actor와 3331값 단계 상태를 유지한다.

GPU 왼손 보상은 `gpu_tensor_song_reward.v17`, 대기 보상은 `gpu_finger_preparation_rate.v2`다. 상태544·event24·priority8·행동39와 단계3331은 같아도 보상 계약이 달라 v16 이하 checkpoint의 strict resume는 거부한다. 새 v17 학습 또는 동일한 v17 전체 계약의 저장본만 엄격히 복원한다. CPU 왼손·오른손의 보상은 기존 경로를 유지한다.

## 검증과 보존

관련 CPU **28모듈 279개 검사**가 통과했다. 이 중 손가락별 대기 전용 16개는 시간/접촉/근접 독립성·고정 분모·B 품질·경계·겹침·부재 손가락·빈 곡·비유한 거리·무효 자세·입력 불변, 실제 tensor 환경의 마디 하중·이전/현재 사건·뒤섞이고 반복된 목표의 귀속·240Hz 적분, v17 저장복원과 같은 차원 v16 거부·거부 전 정책/optimizer/RNG/단계 상태 보존을 확인했다. [검사 목록](cpu_tests.json)을 따른다.

첫 회귀 실행의 press-learning 3건은 기존 손 전체 대기 보상 0이라는 기대를 새 동작에 맞춰 수정한 뒤 모두 통과했다. 원래 실패 기록은 `cpu_regressions.json`·모듈 로그에, 재검사는 `targeted_cpu_tests.log`에 남겼다. 행별 float32 회전의 한 ULP 차이에 대해서만 standby 비교 허용 오차 1e−11을 사용하고, 추종·행동 비용의 기존 정확 비교는 유지했다.

변경 전 **451개 Python과 문서·검증 기록을 포함한 471개 원문**은 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261024_before_per_finger_standby_v1/manifest.json)에 보존했다. 기존 v16 학습·영상과 과거 보고서·시각화 원자료는 수정하지 않았다. 이전 검사를 새 검사로 상속하지 않는다.

- [소스 감사](source_audit.json)
- [최종 검증](verification.json)
- [독립 검수](independent_review.md)
- [현재 보상 설명](/home/ajou/yigyu/3/docs/2026-10-26/왼손보상구조/README.md)

이번에는 CPU로 구현과 저장 계약을 검증했다. v17 GPU/native 실행·새 학습·자연스러움 및 압현 성능 비교는 수행하지 않았다. 기존 v16 체크포인트의 손 모양이 이 코드 수정만으로 바뀌는 것은 아니다.
