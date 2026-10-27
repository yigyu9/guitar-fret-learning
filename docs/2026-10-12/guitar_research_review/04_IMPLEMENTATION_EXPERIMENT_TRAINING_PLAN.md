# 구현·실험·학습 진행 계획

> 기준일: 2026-10-09 (KST)  
> 요청: 기타 연구 현황 정리에서 멈추지 않고 구현, 실험, 학습으로 이어간다.

## 목표

정리 문서에서 확인된 가장 큰 공백인 Fret·Strike 연주 prior와 자유 기타 물리의 연결을
검증 가능한 작은 단계로 진행한다. 기존 연구 경로와 자산을 보존하고, 물리 실험과 학습의
결과를 성공·실패·환경 제약까지 포함해 재현 가능하게 남긴다.

## 선택한 시작점과 고려한 대안

- **이번 착수 경로:** 2026-10-08까지의 사용자 중단은 새 요청으로 재개 권한을 얻었다. 고정 기타
  조건의 손 관절 탐색만 반복하지 않고, 저장된 정적 기타 배치 30개를 고정된 사람 자세에서
  추가 screening했다. 이후에는 source 적합 손 자세·팔 및 기타 위치를 함께 조정하는 후보와
  고정 기타 G0를 비교한다. `PlayingTargetBridge`가 범위 밖의 현재 hold를 거절하는 계약은
  유지한다.
- **병행 경로:** CPU에서 source action/observation/history 계약과 학습 데이터·체크포인트
  재현성을 확인한다. 기존 PPO 학습은 CUDA 및 GPU PhysX를 요구한다. 이 실행에는 NVIDIA
  driver/device가 없어 CPU 학습 smoke가 resource preflight에서 거절됐으며, 목표 시뮬레이터와
  다른 synthetic 학습을 임의로 성과로 계산하지 않는다.
- **후속 대안:** lean `stability_adapter/`의 33D 접근·그립 단계, 개별 Fret/Strike skill 개선,
  고정 기타 G0, 음원 입력부터 전체 물리 연주까지의 통합 중 하나를 잔여 병목과 실행 가능성에
  따라 선택한다. 서로 다른 두 StabilityAdapter의 action/초기조건 계약은 섞지 않는다.

## 단계 및 완료 기준

1. **재진입 점검** — 소비된 입력·checkpoint·기존 결과의 상태와 학습 장치 가능성을 확인한다.
   신규 결과 디렉터리는
   `docs/2026-10-12/stability_adapter_2/results/` 안에 별도 phase로 만든다.
2. **후보 공간 확장** — 이미 수행된 관절 범위·정적 배치 비교를 합쳐 다음 수정 대상과 상대
   배치를 제안한다. 무학습 geometry screen은 native source admission과 구분한다.
3. **무학습 물리 실험** — 새 초기 pose는 fresh native admission 실패를 0-step으로 기록한다.
   통과할 때만 5초 actual
   PhysX를 실행하여 고정 strap·자유 기타 기준과 기타 위치/방향, 실제 손 각도, 충돌/접촉을
   함께 기록한다. 기존 baseline과 동일 조건으로 비교하고 다음 진행 여부를 기록한다.
4. **연주 연결/학습** — 실제 실행 가능한 경우에만 task observation, checkpoint 정규화·후처리,
   clock, actor, 단일 최종 PD target, history echo를 잇는다. 우선 frozen prior + zero residual
   재생 기준을 검증한 뒤, residual 학습은 평가 자격이 있는 source checkpoint와 물리 baseline이
   모두 준비됐을 때 작은 pilot부터 수행한다.
5. **종단 간 재평가** — 오디오→탭/이벤트→Fret/Strike→동기화→물리 기타를 단계별로 실행하고,
   각 단계별 정량지표와 실패를 분리한다. 앞단 계약 성공을 전체 물리 연주 성공으로 확대하지 않는다.

## 현재 재개 지점

2026-10-08 결과물을 다시 대조한 결과, source 범위 후보 1건의 fresh native 형상 gate가
엄지2–기타 겹침으로 0-step 거절됐고, 이어진 thumb2 7개 source sweep·thumb1 기저부 4개
native gate·wrist 13개 source sweep·팔 74제안/68개 geometry sweep도 실행된 상태다.
이 경로는 여러 손 각도/팔 변화에서 교집합이 남는 제약을 보여주므로 같은 작은 각도 검색을
반복하지 않는다. 이어서 실제 기타 배치·연주 prior 연결 같은 별도 축을 평가한다.

이번에는 고정된 사람 자세로 기존 시각 제안 30개의 source signed-gap screen을 새로 구현했다.
왼손만 source overlap이 보고되지 않은 후보는 `audience_yaw+10deg` 1개였지만, 오른손·오른팔을
포함한 전체 human–guitar 겹침 후보는 0개였다. 상세 방법·수치는 [실험 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_pose_geometry_screen_v1/README.md)에
있다. source screen은 native cooked contact 인증이 아니므로 새 물리 rollout을 하지 않았다.

`torch 2.4.1+cu121`에서도 `cuda.is_available()`가 false이고 `nvidia-smi`가 NVIDIA driver에
연결되지 않는다. Strike 1-env CPU smoke는 training resource preflight에서 CUDA 요구로 멈춰
PPO update 0, run 결과 생성 0이었다. 더해 기존 Fret/Strike 대표 후보 네 개 모두 strict G0
qualification이 false여서 학습 가능한 자유 기타 연주 prior pair도 아직 없다. 자세한 값은
[training preflight](/home/ajou/yigyu/3/docs/2026-10-12/guitar_research_review/training_preflight.json)에
기록했다. 학습, source actor 추론, 실제 연주 연결은 미완료다.

## 실행 체크리스트

- [x] 재진입 대상 계획·source 결과·checkpoint qualification·실행 장치 확인.
- [x] 기존 기타 정적 제안 30개의 CPU source signed-gap screen/semantic 분석 구현 및 수행.
- [ ] source/native admission 통과 후보가 없어 fresh 5초 PhysX phase 미실행.
- [x] Strike CPU smoke preflight에서 GPU 필수 거절을 확인하고 PPO update 0을 기록.
- [ ] source prior 재생부터 residual 학습까지 가능한 다음 구현 단위를 완료한다.
- [x] 연구 흐름 계획에 새 방법 비교·화면 실험 결과·학습 장치/qualification 제약을 보충.

## 보존 및 판단 원칙

- 기존 consumed source/계획/입출력/실험 phase를 덮어쓰지 않고 모든 신규 산출물을 새 phase에 저장한다.
- checkpoint qualification, 관절 범위, 충돌 제약, 초기 기타 world pose를 우회하거나 사후 수정하지 않는다.
- 학습과 물리 실험은 별도 변수로 기록한다. GPU 부재나 simulator 오류는 결과로 남기고, CPU 가능
  계약 검증 및 비학습 실험까지 계속한다.
- 각 단계의 성공은 그 단계에서 실제 측정한 범위까지만 주장한다.
