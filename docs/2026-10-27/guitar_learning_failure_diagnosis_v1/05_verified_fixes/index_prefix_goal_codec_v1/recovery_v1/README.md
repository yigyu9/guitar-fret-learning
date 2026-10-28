# Goal fit 저장본의 명시적 회복 평가

원 fit은 exit1이다. codec.py:221의 finally 입력감사가 import하지 않은 sys.modules를 참조했고, 원 inputs_after.json/goal_codec_report.json은 없다. 이 실패·누락·원2023준비/source는 그대로 두며 재학습·보고서 소급작성·원모델 metadata/bytes 변경을 하지 않는다.

새 CPU 감사는 원1000개 유한손실·원6구간/분할/계획goal label·fresh73동일·저장73유한/54불변/허용19변경·critic/std/cost2zero/PPO0와 빈optimizer·새GoalPolicy strict identity·모든 원 inputs_before SHA를 검산한다. 저장 후 실제 원소스의 strict reload/checks와 parameter_invariants 기록이 먼저 있고 그 뒤 유일한 finally NameError라는 원문/실제파일 순서 근거를 확인한다. 원 종료 보고서가 없으므로 정상완료로 재분류하지 않는다.

CPU에서는 원 CUDA RNG checkpoint load 거부를 유지한다. /tmp의 cuda_rng만 제외한 투영본으로 CPU identity/model/optimizer/RNG 복원 범위를 검산하며 실제 native full CUDA restore로 부르지 않는다. 원 checkpoint SHA 70e40d1cb80a90a2636fd7d1babb4870bd82333d900c667fa136bac233ef9327은 그대로다.

새 gate는 원 probe.gate('fit')의 reference128·음악/해제/stage_ready·독립PASS·입력검증을 그대로 수행한 뒤 단일 알려진 후처리 오류에 대한 새 CPU감사/준비review PASS를 요구한다. evaluate 한 개만 허용한다. 원 source.launch('evaluate')와 원 GoalPool/GoalPolicy/metadata/full trainer.load를 그대로 사용하고 gate와 output 두 별칭만 finally복원하는 scope로 연결한다. 출력은 recovery_v1/runs/evaluate, 원 checkpoint 경로는 그대로다. 새 fit_recovery_report.json이 원 parent exit1과 회복 평가 완료를 분리하며 원보고서를 고치지 않는다.

준비검수/freshgate 뒤 root만1회 NN-only128 평가한다. NNfirsttick/referenceN0·원현재목표DIPguard/4rad/s/full범위/PD/cap.25/native105/90쌍/손목/원9보상/원90% 기준은 유지한다. 음악성과·자연스러움·압력·자유기타/J33/PPO 성공은 아직 미검증이다.

문법검사 외 stdlib symtable의 referenced-global 이름을 module assigned/imported/builtins와 비교하는 좁은 검사를 새3파일에 적용한다. 일반 linter 대체로 주장하지 않는다. 원 codec의 미해결 sys 하나는 수정하지 않고 보존한다.
