# 첫 하중 시점부터 증분 억제하는 단일 진단

root 승인 [PLAN.md](PLAN.md)을 따른다. 기존 contact_target_windup의 관찰 wrapper를 최소 복사하고, 봉인된 projection은 그대로 import한다. **제어 의미의 차이는 clock≥480 gate 제거 하나**다. `relax=False`만 허용하며 최초 현재 signed press-normal resultant>기존0.01N인 유효 control snapshot부터 A를 적용한다. 최초 하중을 영구 latch로 쓰지 않고 unloaded/reset/first-attempt 종료/기존 실패/비유한 상태에서는 원래 target을 통과시킨다.4개 substep 도중에는 제출 target을 바꾸지 않는다.

고정 baseline final300 checkpoint·원래218×128×4 executed-action tape·source clock480 고정 material point·팔 teacher/B/엄지035·PD/범위/4rad/s·보상/실패는 그대로다. 고정점이 최초 candidate witness라는 주장은 하지 않는다. teacher feedback 혼입·접선 변경이 남으므로 새 정책 성과나 자유 손 production 개선으로 해석하지 않는다. 힘은 body resultant, Jn 오차는 국소 선형 proxy다.

추가 target_control60.npz schema는 이전과 동일하다. 새 first_contact_report.json은 환경별 첫 gate/실제 target 변경 start clock을 구분하고, 실제 변경 직전까지 모든 physics30필드·모든 control필드를 source와 exact 비교한다. 명령 tape는 전체 첫 시도에 exact여야 한다. raw/base report는 덮어쓰지 않는다. 기존 out은 native import 이전 거부하고 원래 exclusive mkdir+dev/inode 소유 확인을 유지한다. 기존 original/2초뒤 억제/완화 raw 세 조건과 launcher는 준비 입력에 pin해 대조로 재사용한다.

CPU 준비 명령(프로젝트 루트):

```bash
CUDA_VISIBLE_DEVICES='' PYTHONPATH=. /home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/contact_target_first_contact/self_test.py
CUDA_VISIBLE_DEVICES='' PYTHONPATH=. /home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/contact_target_first_contact/prepare.py
```

CPU 검수 후 **root 내부 GPU 인계 전에는 실행 금지**다. 향후 root용 단일 실행 예시:

```bash
PYTHONPATH=. taskset -c 0-13 /home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/contact_target_first_contact/run_probe.py --out docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/contact_target_first_contact/run_01
```

128 첫 시도/218 control/872 endpoint 상한·전체실패분모·원래9지급/원장·native/model/RNG/updates/source핀/scene closed는 기존 sealed observer 감사 그대로다. 추가60Hz 약13.73MB와 원관찰을 합쳐100MB 미만을 검사한다. 예전 target_windup_report 대신 새 timing 계약을 first_contact_report에 명시한다. CPU 검사는 actual native prefix 동일성을 보장하지 않으며 후속 실행에서 확인해야 한다.
