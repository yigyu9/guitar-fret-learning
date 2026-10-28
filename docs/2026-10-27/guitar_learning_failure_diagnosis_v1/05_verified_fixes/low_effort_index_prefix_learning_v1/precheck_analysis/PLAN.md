# 검지 3음 학습 전 대조 분석 계획

소유 범위는 이 분석 폴더뿐이다. 부모 producer/learning/준비·기존 결과·활성 소스는 수정하지 않고 GPU/native 실행도 하지 않는다. root가 세 장면의 실제 종료를 통보한 뒤 `analyze.py --root-completed`로만 원자료를 읽는다. 현재는 결과를 생성하지 않는다.

- [x] 최소 분석기·완료 guard 작성, Python3.8 AST와 합성128원장/음악·해제분리/90%경계/실패포함/launcher·firstmask·currentgoal·DIP억제/rate 오류거부 자가검증. 기본 실행은 stdlib만 읽으며 `--self-check`는 합성 배열에만 NumPy를 사용한다. 실제 자료·GPU·native 읽기/실행0.

- [ ] reference/zero/random 각각128 첫시도, 총384시도·1152음과 실패를 모두 포함한다. 음악 성공과 A의 원 native release, 두 기준의 AND를 별도로 재계산한다. reference만 stage_ready가 train gate의 조건이며 zero/random의 달성0이나 실패0을 통과 조건으로 강제하지 않는다.
- [ ] 부모 gate·준비 review·현재 source/asset/input SHA, 실제 launcher3children 종료0, fixed scene 닫기·128환경 native105/cap0.25/90쌍·alias 복원·입력 전후를 확인한다. 원67행/선택3음·354tick/4physics 및 source 시계를 보존한다.
- [ ] 실제 원장 `notes[]` 세 음과 `prefix_release`, 원9항 보상을 보존한다. 음악은 각음 달성≥.90/평균clean≥.90/평균wrong≤.10·전체3음달성≥.90·reference fail0, release는 A released≥.90이다. 보상을 음별로 재분배하거나 60Hz 기하로 재지급하지 않는다.
- [ ] env0 60Hz 실제각/목표/추종gap·PIP/DIP·3마디 합력·손목을 음창별 요약한다. 원 prefix CPU 환경을 재사용해 원6gate/wrong 원인을 재구성하며 nearest tie/미저장 native sample·qd 한계와 불일치를 그대로 남긴다. 다른127환경 상세힘은 미확인이다.
- [ ] `current_goal_DIP60.npz`의128 firstmask/clock/currentgoal·guard eligibility·양의 DIP증분 억제·음/영 증분 보존·다른104열·memory/observation/rate 잔차를 저장범위에서 확인한다. raw guard 집계는 재시도 포함 전체 controls일 수 있으므로 first-attempt NPZ와 혼합하지 않는다.
- [ ] stdlib 자가검증/완료 guard → root 완료 후 actual CPU 실행 → 분석 소스+수치 통합 독립검수 1회. `results_v1/{review,verification,acceptance}.json`을 부모 train gate가 읽으며 reviewed_sha256/input_sha256/verified_input_sha256 schema를 유지한다.

출력은 comparison/acceptance/verification JSON·원384시도/1152음 CSV·한국어 RESULTS의 최소 집합이다. 필요한 그림만 실제 자료 확인 후 추가한다. 동일 seed7의128환경이며 NN 초기정책·학습성과가 아니다. reference만 참고 N 일정이 들어가고 정책에 N을 주입하는 성과로 보고하지 않는다. 몸체 순힘은 pair 압력·토크·피부 전체 분리 인증이 아니다.
