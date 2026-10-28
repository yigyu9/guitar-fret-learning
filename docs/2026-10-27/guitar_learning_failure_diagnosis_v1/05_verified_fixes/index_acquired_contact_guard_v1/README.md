# 정상 획득 접촉 기억 guard 진단

원 frozen prefix300을 동일128환경에서 원 current-goal guard와 acquired-contact guard로 비교하는 **CPU 준비**다. 구현·입력은 이 폴더만 새로 작성했으며 기존 source/모델/준비/분석/영상은 바꾸지 않는다. root만 GPU를 직렬로 실행한다.

정상 candidate를 현재목표일 때만 기억하며 소실/wrong/unsafe/reset/failure 때 지운다. none에서 새 획득은 없고 이미 정상 획득한 접촉은 소실까지 유지한다. 양의 DIP 추가 목표증분만 억제하며 음수/0·다른104열·범위·4rad/s·PD·원 보상/음시계를 보존한다. N 주입이나4축 동결은 없다. 이는60Hz 관측 기억이며240Hz 연속접촉·피부전체분리·접촉쌍압력 인증이 아니다.

`probe.py`는 부모 strict `execution_scope`·base launch·원128평가기/3음환경/compact·cap105/90쌍 검증을 그대로 쓴다. 원 모델 계약/identity는 보존하고 `execution_override.json`에 새 실행 규칙을 따로 선언한다. 새 sidecar의 effective_candidate/eligible/blocked는 기억 gate이며 현재목표의 원값이라고 부르지 않는다. 원현재목표 입력과3기억은 별도 scalar열이다. 기존 current-goal verifier를 새 조건에 사용하지 않는다.

원 `report.json`·`diagnostic_report.json`·`training_contract.json`을 덮어쓰지 않는다. 새 `acquired_guard_report.json`·`execution_override.json`·`acquired_control60.npz`·원각음 `prefix_acceptance.json`을 추가한다. env0 기존60Hz 상세 trace만 유지하며 다른127 상세힘이나fullbody240Hz trace는 만들지 않는다. 실제 실패도128분모에 남긴다.

준비 명령(CPU):

```
CUDA_VISIBLE_DEVICES='' /home/ajou/miniconda3/envs/rl38/bin/python -B probe.py --prepare
```

native는 준비 독립검수 PASS·현재핀 확인 후 root만 `cpu_inputs/commands.json`의 두 명령을 각각 새 장면에서 실행한다. 기존out·symlink는 gate/native import보다 먼저 거부하고 원exclusive mkdir의 dev/inode소유권을 후처리 전에 검증한다. 모델/updates/RNG를 평가 전후 원fingerprint로 비교한다.

후속 실제분석은 baseline의 원300재현 일치/차이부터 공개한다. 각256시도/768음의 음악·해제·AND와각도/하중/손목·최초추가개입·변경전prefix를 분리한다. 관측 개선이 없더라도 자료를 보존하며 다른3축 누적·보상·자유기타/자연성 해결로 확대하지 않는다. 현재음악 실패를 비용critic 원인이라고 단정하지 않는다.
