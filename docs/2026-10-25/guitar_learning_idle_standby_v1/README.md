# 실제 대기 구간의 B 권고 복구 — v18

2026-10-25. v17 영상에서 아래로 펴진 손가락은 중지였으며, 최고 모델의 대표 env0 한 곡에서 B 보상 합계가0이었다. 사용자 승인에 따라 대기 권고가 실제 쉬는 구간에 적용되도록 조건을 수정했다. 약한 권고의 크기·손가락 움직임 비용0·B 중심/대역은 유지했다.

## 변경

| 조건 | 이전 v17 | 현재 v18 |
| --- | --- | --- |
| B 전용 시간 보호 | 본인 press−2..end, 바깥 .25초 fade | 본인 press−.35..end 경계 포함0, 바깥 .15초 fade |
| 근접/비유한 거리 제외 | 본인 전체 곡 목표, 지난/먼 미래 포함 | 본인 목표 중 press−2..end에 있는 목표만 |
| 접촉 제외 | finger1/2/3 몸체 netload 단독 또는 본인 목표 candidate/wrong | 관련 목표의 이전/현재 candidate/wrong만; 목표별 시간 필터 후 손가락별 OR |
| 비유한/4cm 경계 | 전체 곡 목표에 적용 | 관련 목표에만 적용, 4cm 경계 포함 |
| B 크기 | 손가락별 최대 .0025/s, 고정4분모, 전체 .01/s | 동일 |

가까이 접근한 본인 목표는 기존2초 준비창에서 계속 보호하고, 압현 직전 .35초~음 끝은 거리와 무관하게 권고를 끈다. 지난 음·먼 미래 음은 B 제외 판정에서 빼고, 단순 몸체 하중은 제외 근거로 쓰지 않는다. 관측 idle4·목표 선택기·추종의 원래2초 준비 안내는 유지한다. 빈곡0·곡에 없는 손가락 idle1·실패 tick의 양성 보상 억제도 유지한다.

보상 버전은 `gpu_tensor_song_reward.v18`, B helper는 `gpu_finger_preparation_rate.v3`, 에피소드 진단은v2다. actor 전용 분기와3331값 curriculum은 v18을 인식한다. 진단은 실제 helper의 time/contact/near/nonfinite 마스크를 직접 집계한다. 중복해 겹치는 제외 시간을 더해 전체 시간으로 해석하지 않는다.

B는 자동 복귀 제어·강제 경유 자세·벌점이 아니다. 다른 손가락의 직접 gate를 끄지 않지만 전체 정책에 대한 간접 영향0이나 자연스러움 향상을 보장하지는 않는다. .35초/.15초는 첫 적용 값으로, 압현 성능과 동작 품질은 후속 장기 학습으로 확인해야 한다.

## 보존과 호환성

[변경 전473개 원문 보관 목록](/home/ajou/yigyu/3/guitar_learning/archive/20261025_before_idle_standby_v1/manifest.json)을 먼저 만들고 원문 SHA를 검증했다. [변경 파일](changed_files.json) · [현행456개 Python SHA](source_manifest.json). 이전 결과·보관본은 덮어쓰지 않았다.

실제 v17/v18 small16 실행의 계약을 비교해 보상 버전과 B 항 이외의 전체 계약이 같음을 확인했다. 같은 seed의 초기 모델72개 텐서도 정확히 같았다. 물리·제어·PD·힘·관절 한계·관측544/24/8·음 판정·성공·추종·PPO·손가락 비용0은 유지했다. [검사](unchanged_contract_verification.json).

보상 정의가 달라져 **v17 이하의 strict resume는 거부**한다. 자동 Actor 이전을 추가하지 않았다. 새 학습은 fresh v18로 시작하고, 동일한 전체 계약의 v18 저장본만 재개한다. 관측 차원이 같다는 이유로 이전 성과나 optimizer 상태를 그대로 이어받지 않는다.

## 저장된 영상 자세에 대한 비교

대표 v17 best/env0의 같은 자세1970개 중 reset을 제외한1969개60Hz 끝점을 사용했다. 실제 지정 distal 패드와 source 압현면·유한 프렛 셀까지 거리를 재구성했다. 접촉 하중/candidate/wrong 기록이 없어 **시간·기하 기반 허용 비율은 접촉 제외 전 상한**이며 실제240Hz 보상을 복원한 결과가 아니다.

| 중지 기준 | 이전 | 새 조건 |
| --- | ---: | ---: |
| 시간 기준 대기 가능 | 26.61% | 61.66% |
| 시간·기하 기준 대기 가능 상한 | 18.44% | 51.70% |

[상세 비교](saved_pose_gate_comparison.json) · [생성 도구](support/replay_gate.py). 새 정책을 학습해 얻은 자세 개선이나 이전 정책의 실제 보상 증가를 뜻하지 않는다.

## 검증

- GPU 관련 CPU 회귀 **278개 통과**. [검사 로그](cpu_gpu_tests.log).
- 독립 검수의 관련12개 모듈147개 검사와221시점/7목표에 대한4,420개 scalar 대조를 통과했다. 경계·중첩·지난/먼 미래 목표·손가락별 적용·4cm·NaN/inf·실제 진단 마스크·비변조를 확인했다. [독립 검수](independent_review.json). 이 검사는278개와 일부 겹치므로 합산하지 않는다.
- 새 실제 GPU: small/16환경/H32/65업데이트·33,280전이, 종료16개 모두 물리 안전 시간축 완주. CRC/EOF·전이 회계·ID 참조·원시 평균·체크포인트 SHA·입력 pin·정상 종료 검사를 통과했다. 기본250회 간격이므로 초기/최종2개만 저장했다. [로그 검사](gpu_smoke_inspection.json) · [원 보고서](gpu_smoke/report.json).
- 각 종료곡 평균 B 적용 가능 시간은 검지8.77초·중지10.82초·약지11.84초·소지20.19초였고, 평균 실제 B 기여는 각각 약 .01970/.01383/.01578/.01190였다. 손가락별 합계와 기존 보상 성분 합계의 최대 차이는 float32 적분 반올림에 따른 약7.02e−8이다. [실제 진단 요약](gpu_standby_summary.json). 제외 원인 시간은 겹칠 수 있다.
- 실제 v18 65→66회 재개: metadata 이외 모델·양 optimizer·모든 난수·curriculum 포함 상태가 정확히 복원되고 모델과 양 optimizer가 갱신됐다. 실제 같은 크기의 v17 저장본은 상태 변경 없이 거부했다. [재개·거부 검사](checkpoint_verification.json) · [재개 로그 검사](gpu_resume_inspection.json).

확장 checkpoint/logging 관련 CPU56개 중55개 통과, **기존 실패1개**를 별도로 기록했다. `test_left_curriculum_runtime.py:218`은 기본 실행을 CPU512로 가정하지만 실제 기본은 GPU544다. 해당 테스트와 `training/start.py` 모두 변경 전 SHA와 같고, CPU를 명시하면 왼손512/오른손500을 반환한다. 이번 보상 변경의 회귀로 분류하거나 관련 코드를 바꾸지 않았다. [확장 검사 로그](cpu_checkpoint_logging_tests.log) · [독립 재현](independent_review.json).

이번 GPU 실행은 보상의 연결·안전한 저장·재개 검증이다. 67음 연주 성능, 손가락의 자연스러운 복귀, 수렴·일반화는 아직 검증하지 않았다. v18 장기 학습은 실행하지 않았다.

## 실행 예시

```bash
python -m guitar_learning.train \
  --hand left --song 05_BN2-131-B_solo \
  --physics gpu --device cuda:0 --size large --num-envs 1024 \
  --horizon 32 --updates 2000 --checkpoint-every 250 --seed 7 \
  --out /home/ajou/yigyu/3/runs/left_song_idle_standby_v18_01
```

새 출력 경로에서 시작한다. 위 장기 명령은 다음 실행 예시이며 이번 작업에서 실행한 명령은 아니다. 보상 상세는 [현행 보상 문서](/home/ajou/yigyu/3/docs/2026-10-26/왼손보상구조/04_손가락추종과자세.md)를 따른다.
