# seed17 비용 발생의 잠정 관찰

**완료 보고가 아니다.** root의 후속10평가·외부 launcher 종료 확인 전, CPU에서 읽은 metrics 1~298회와 그 범위의 종료 episode 5,505개만 다룬다. 원자료·checkpoint·활성 소스·봉인 파일은 변경하지 않았고 GPU를 사용하지 않았다. 정확한 JSONL 앞부분 byte 수·SHA, 원자료 경로, checkpoint SHA, source SHA·함수 위치와 수치는 `PROVISIONAL_COST_298.json`에 기록했다.

최초 실제 실패 비용은 **201회 env81 한 건**이다(episodes.jsonl 3713행). 종료 사유는 `wrist_severe`, physical_failure=false, wrist_failure=true다. 96제어tick(1.6초)에 끝났으며, 비용9.316666603은 기본5 + 남은시간비용4.066666603 + 미정산 음 예산0.25로 구성된다. running_physics 비용은0이다. 마지막 readback의 Gz 안내 영역 초과는0.113432802m, severe_elapsed는0.1125초다. 이 값은60Hz 종료 경계의 마지막240Hz 표본이며 궤적 최대가 아니다. 일반 손목 누적실패와 달리 심각 이탈 판정은 초기3초 유예 중에도 작동한다. 어느 관절·접촉이 이탈을 일으켰는지는 이 episode 요약으로 확정할 수 없다.

| 구간 | 실제 비용 평균 | 비용 GAE advantage·출력·손실 |
| --- | --- | --- |
| 1~200회 | 모두0 | 검사한 mean/std/min/max·loss 모두 정확히0 |
| 201회 | 0.002274576807 = 9.316666603 / 4096 | 최초 nonzero; advantage max9.316666603, cost_value_loss0.276011020 |
| 202~298회 | 모두0 | 각97회에서 nonzero |

metrics의 `diagnostics.advantages.cost_raw`는 **즉시 비용이 아니라 GAE advantage**다. `compute_decision_gae`는 현재/다음 cost value로 bootstrap하고, critic은 해당 return을 학습한다. 따라서 한 번 실제 비용이 발생한 뒤 실제 비용 평균0인 구간의 nonzero advantage/value/loss를 새 실패 비용으로 세면 안 된다. 이 snapshot에서 `mean_failure_cost × transitions`의 합과 모든 episode 비용의 합은 모두9.316666603으로 정확히 일치한다.

저장된 cost head는 initial.pt와 evaluation_000200.pt에서 weight512개·bias1개 모두 정확히0이다. evaluation_000250.pt에서는 모두 nonzero이며 weight 최대절댓값0.020669181, bias 절댓값0.001610006이다. 201회 checkpoint는 없으므로 그 회차의 파라미터를 직접 측정한 것은 아니다. 201회부터 post-update critic 출력·손실이 바뀌었다는 로그와, 200→250회 저장 head의 변화만 직접 확인했다. 이것을 성과 변화의 인과효과로 해석하지 않는다.

판정·비용 근거는 현재 실행 pin과 SHA가 일치하는 `guitar_learning/gpu/simplified_finger_environment.py`의 `_safety`(185행), `_apply_failure_cost`(214행), `_episode`(250행)다. 비용 GAE·critic 최적화·진단의 위치는 `guitar_learning/training/decision_ppo.py` 9·44·107·149행, 실제 비용 평균 기록은 `guitar_learning/tool/experiments/short_finger_learning/runner.py` 166행이다. 최종300회 비용 감사와 전체 평가의 실패 포함128분모·연속통과 여부는 실제 종료 후 별도 자료로 확인해야 한다.
