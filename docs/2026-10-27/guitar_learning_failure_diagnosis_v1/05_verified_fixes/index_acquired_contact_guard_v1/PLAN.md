# 정획득 접촉 기억을 쓰는 DIP guard: 단일 후속 진단 계획

상태: **root가 CPU 최소구현·준비를 승인, GPU/native 실행0**. 이 폴더만 수정한다. 기존 prefix 학습/1602봉인·14개 actual 분석 검토파일·모든 원자료/활성 소스·영상 준비는 바꾸지 않는다. 실행은 독립 CPU 준비검수 뒤 root가 직렬로 결정한다. none에서 새 획득 금지/기존 정상 기억 소실까지 유지 정의도 승인됐다.

## 질문과 보존 조건

frozen prefix final300의128첫시도에서 A는128/128이지만 B7/B8은0/128, A native release도0이었다. env0에서 A end 뒤 현재목표는 B7로 바뀌고 B candidate0이어서 기존 guard가 DIP 양의 목표증분을 막지 않았다. A candidate가 저장 해제 창6끝점/이동26끝점에 남은 가운데 DIP는 약27→89도, PIP는52→10도로 바뀌었다. **이미 정상 획득했던 접촉을 관측상 잃기 전까지 기억하는 것만** 추가하면 마디 분담·해제·전환이 어떻게 달라지는지 묻는다. 현재 actual 분석은 독립검수 중이며 이 수치를 확정 성과로 확대하지 않는다.

비교는 frozen300 동일 checkpoint의 (1) 원 current-goal guard, (2) 아래 acquired-contact guard 각128첫시도·3음384기회다. 같은 seed7·고정 기타·원67행/선택4→7→8·354tick·4physics/60Hz·wrist v3/동일 일정·모델/PD/0.25Nm/90쌍·codec/4rad/s/범위·관측/보상/종료를 유지한다. 참고 N 각도, full4freeze, force cap, 보상/문턱/손목/gain 변경은 없다. 새로운 actor 학습이나 이전은 하지 않는다.

250은 A 전부터 B 위치의 candidate가 켜진 채 B만 달성했다. 이를 고착시킬 수 있는 **아무 미래음 candidate의 무조건 OR**는 금지한다. 현재목표로 정상 획득한 이력만 새 gate에 사용한다. 이 시험 하나로 다른3축 목표 누적, 해제 보상, 물리 lag나 자유 기타를 해결한다고 주장하지 않는다.

## 기억과 유한한 제어 규칙

환경별 선택3음의 bool 기억 `M[N,3]`만 둔다. 현재목표 선택은 원 코드의 precontrol score `< end`인 가장 이른 선택음이며 press/onset의 새 gate를 추가하지 않는다. 원 guard처럼 준비 중 현재음의 정상 candidate도 획득 가능하다. scalar-only 부모 sidecar에는 각3열을 개별1D 필드로 기록한다.

각 precontrol에서 원 전체 snapshot/old·raw target의 finite, reset, 기존 failure 보호를 먼저 적용한다. `C_j = candidate_j & ~wrong_j`, 안전한 행 `S`라 하면:

```
M_new[j] = S & C_j & (M_old[j] | (present & current_goal == source_j))
hold = any(M_new) & (raw_DIP > old_DIP)
final_DIP = old_DIP if hold else raw_DIP
```

즉 관측 candidate 소실 **또는 wrong 등장** 때 해당 기억을 지우고, 현재음일 때만 다시 획득한다. nonfinite/reset/prior-failure 행의 기억은 지우며 개입하지 않는다. partial reset은 해당 행만 지운다. 한 음의 off가 다른 음의 기억을 지우지 않도록3bit로 보존한다.

`current_goal=-1`에서는 새 획득이 없고 safe-gather A값을 사용하지 않는다. **이미 획득한 접촉은 none/tail에서도 정상 관측이 유지되는 동안 기억한다**는 안이다. 이것은 '소실까지 기억'의 일관된 확장이며 root 검토 항목이다. 원 B7/B8 공유 gap에는 새 release 조건을 만들지 않는다.

양의 DIP 목표증분만 막는다. 음수/0 증분, 다른104 native 열, 실제 q/qd는 그대로다. 원 raw codec는 한 번만 호출하고 old target은 그 호출 전에 clone한다. 반환 target alias와 controller target 메모리·scene 제출이 같아야 한다. 기존 bounds/old±4/60과 dtype 기반 원 검사를 유지하며 추가 backlog·실제q 즉시대입·복구 solver가 없다.

이 기억은 **60Hz precontrol cache**다. 같은 control 사이240Hz 접촉이 끊겼다 돌아오는 경우는 놓칠 수 있어 연속접촉·피부분리·접촉쌍 압력 인증으로 쓰지 않는다. 원 native released/release_s는 변경하지 않는다.

## 최소 연결과 계약의 구분

- 재사용: `low_effort_index_prefix_learning_v1/probe.py`의 `execution_scope`/strict loader·base launch/cap128 verifier, `learning.py`의 `LearningPool`/원128 evaluator/3음 compact·환경, `index_candidate_dip_guard_v1/probe.py:target_filter`의 원 codec/유한·메모리·104열·속도 검사와 관찰 패턴.
- 새 seam은 pool의 `targets()`와 행별 reset 기억뿐이다. 모델은 원 checkpoint/원 training_contract/원 `_identity`로 엄격히 로드한다. **새 execution_override 선언**에 guard 의미·기억·부모/자체소스·checkpoint SHA를 별도로 pin하며 실제 평가 report에 표시한다. 원 모델 계약이 새 gate를 선언했다고 위장하지 않는다.
- 기존 `LearningPool.step()`은 `pending.final_target_rad`와 실제 scene/observation을 assert한다. 기존 `targets()` 뒤 target만 바꾸면 이 검사가 깨지므로, 최종 pending을 새 guard의 실제 final로 일관되게 연결해야 한다. 원 native codec를 두 번 실행해서도 안 된다.
- 원 `precheck_analysis.guard_audit()`는 `blocked = current_candidate & ~wrong & ... & positive_delta`를 검사한다. 새 조건을 이 검증기로 통과시킬 수 없다. baseline은 원 검증 그대로, 새 조건은 현재음의 원 candidate/wrong와3기억/획득·소실·유지 원인을 분리한 작고 명시적인 검증을 쓴다. 기존 검증/원문은 고치지 않는다.
- `prefix_learning_report`의 current-goal scope와 기존 candidate/eligible/blocked 필드 의미도 그대로 새 조건의 증거라고 부르지 않는다. 원 base 장면/입력/strict report는 보존하고 새 override report에 실제 규칙·scalar 기록 의미·복원/장면닫기를 명시한다. 부모 `launch()`를 통째 복사하지 말고 기존 `execution_scope`+base launch를 쓰는 동안만 pool seam을 scoped 교체/복원하는 최소 경로를 검토한다.

checkpoint weights·trainer updates는 같아도 override 후 target_error/물리상태가 달라지면 이후 정책/팔 feedback 명령도 달라질 수 있다. 이는 닫힌 루프 평가이며 개입 이후 action tape 동일성을 요구하거나 주장하지 않는다. 실제 변경 전 환경별 prefix는 원 기록과 엄격히 비교하되 baseline 재실행 자체의 native bitexact를 미리 보장하지 않는다.

## 기록·검증·분기

- [x] 현재 learning actual 독립 PASS `59295b114d5fbc0f9992d5857ea71e3aa5601e96a46fbcbd60050ce7a0d5b2a6`를 확인했다. 준비 gate에서 이 review/원검증입력·frozen300을 pin한다. 기존 결과의 PASS는 분석 정확성이지3음 음악 통과가 아님을 보존한다.
- [x] CPU 합성 검사: 미래B만 candidate이면 획득0, 현재A획득→goalB/A유지, Aoff/wrong→기억소실, 정상B획득, none, nonfinite/priorfailure/reset/partialreset, 음수/0·104열 exact, target alias/codec1회·rate/bounds·새 scalar pending/sidecar, finally 복원·기존out/symlink 거부. constructor/evaluation primary오류와 secondary close/fingerprint오류 보존도 검사했다. 실제 scene/observation 일치는 원 step assertion을 보존하고 GPU 후 확인한다.
- [ ] 새128두조건 source/model/task/자산/재료/105 native 속성·90쌍/close·입력 전후를 확인한다. baseline ledger/요청/행동/guard/env0 물리와 원 frozen300의 실제 일치/불일치를 보고한다. 모델·updates와 RNG를 기존 fingerprint 패턴으로 확인하고 새 act/RNG 호출을 추가하지 않는다.
- [ ] 기존 bounded first-attempt60Hz sidecar에 current/remembered 후보·3기억·hold 원인·최초추가개입 clock만 더한다. 기존 env0 trace와 원3음 ledger/released·9보상을 재사용한다. 새 fullbody240Hz trace나 임의 힘/기하 문턱은 없다.
- [ ] 모든256시도/768음·실패를 포함하고 음악/release/AND, 원각·목표/range·PIP/DIP·관절별 음수명령, 손목/3마디순힘, A획득 여부와 해제창을 분리한다. 추가개입이 없으면 도달한 gate가 없었다고 보고하며 효과를 만들어내지 않는다. 개선돼도 자연성·낮은 총하중·일반 제어 채택으로 확대하지 않는다.

CPU 구현은 원 policy identity를 그대로 두면서 새 runtime override를 별도 표시한다. 영상 준비의 독립검수가 먼저이며 그 뒤 같은 change-reviewer에게 이 준비 검수를 연결한다. GPU 실행은 준비 인계 후 root가 별도로 결정한다.
