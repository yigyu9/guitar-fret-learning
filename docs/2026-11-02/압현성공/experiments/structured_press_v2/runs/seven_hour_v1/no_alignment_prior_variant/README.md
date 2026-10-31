# 초기 팔 정렬 출력 prior를 제거한 전축 학습 대조군

현재 full33 fresh 학습 대조군과 같은 **601열·33활성축·원래 v9 초기 분포**를 사용하고, 최초 정책 생성 시 `core.support_head.bias[:12]`만 IK 팔 정렬값에서0으로 바꾼다. 다른 초기 가중치·표준편차·난수 소비·보상9항·실패 조건·물리·PPO 규칙은 유지한다. 새 schema는 `guitar_learning.no_alignment_prior_policy.v1`이며 settings와 architecture의 `no_alignment_prior`가 필수다. 새 모듈 자체도 live 입력 pin에 포함한다.

실제 로봇 초기 자세, 관절 기준각, 목표 프렛·줄·기하, ideal hold를 포함한 기존 추가 관측은 바꾸지 않는다. 출력 bias의 사전 정렬만 제거하므로 “아무 사전 정보도 없는 학습”은 아니다. 이는 정적 출력 prior 대 실제 공동 학습의 추가 대조이며, 과거557열 production 모델을 완전히 재현하는 실험은 아니다.

학습된 bias를 고정하거나 매 step0으로 덮지 않는다. 새 모델 생성 시0으로 시작한 뒤, strict resume/load는 저장된 모든 가중치와 optimizer/RNG를 정상 복원한다. 별도 A/B 이전은 허용하지 않는다. 아래 evaluate는 이미 free-v9인 저장 모델을 그대로 평가한다.

## 실행

이 폴더의 `runtime`을 작업 디렉토리로 사용한다. 기존 Isaac Gym Python 환경과 GPU 작업 순서를 유지해야 한다. 이 작업에서는 GPU를 실행하지 않았다.

```bash
python -B -m guitar_learning.tool.experiments.no_alignment_prior train --geometry guitar_learning/assets/structured_press_v2/catalog.json --song virtual_finger_v9_index_s3_f4 --stage free_v9 --size large --num-envs 64 --updates 100 --seed 7 --out ../runs/100/train
python -B -m guitar_learning.tool.experiments.no_alignment_prior evaluate --checkpoint ../runs/100/train/J/initial.pt --num-envs 32 --out ../runs/100/evaluate_initial
python -B -m guitar_learning.tool.experiments.no_alignment_prior evaluate --checkpoint ../runs/100/train/J/final.pt --num-envs 32 --out ../runs/100/evaluate_final
python -B -m guitar_learning.tool.experiments.no_alignment_prior train --geometry guitar_learning/assets/structured_press_v2/catalog.json --song virtual_finger_v9_index_s3_f4 --stage free_v9 --size large --num-envs 64 --updates 100 --seed 7 --resume ../runs/100/train/J/final.pt --out ../runs/200/train
python -B -m guitar_learning.tool.experiments.no_alignment_prior evaluate --checkpoint ../runs/200/train/J/final.pt --num-envs 32 --out ../runs/200/evaluate_final
```

최초 학습 후 `report.initial_prior_audit`는 실제 full33 대조군의 initial.pt와 비교해 팔 bias12개를0으로 바꾼 경우에만 전체 모델 tensor가 같고 CPU/CUDA RNG도 같아야 한다. 불일치는 오류로 처리한다. 기본 비교 대상은 `index_full33_seed7_v1/100/train/J/initial.pt`이므로 다른 seed/size의 실행은 이 대응 실험 범위 밖이다. strict resume에서는 fresh 비교를 다시 적용하지 않는다.

CPU 검사는 초기 모델의 tensor 차이가 지정된 bias12개에 한정되고 난수 소비가 같으며, 초기 forward의 손가락 평균·전체 공분산·가치 예측이 같고 팔 평균만 달라지는지 확인한다. 학습된 bias의 strict 저장/복원, 원래 schema 거부, 필수 settings와 factory 정상/오류 복구도 검사한다. CUDA 초기화 비교는 실제 GPU 실행 후 확인한다.

`copy_manifest.json`은 기존3148개 원문 출처, `source_seal.json`은 새 모듈·검사까지 포함한 원문 SHA, `validation.json`은 CPU 검증 결과를 기록한다. 원래 runtime과 다른 실험의 봉인 파일을 수정하지 않는다. 단일 검지 목표·seed7의 절차 비교이며 결과는 생산 코드에 자동 반영하지 않는다.
