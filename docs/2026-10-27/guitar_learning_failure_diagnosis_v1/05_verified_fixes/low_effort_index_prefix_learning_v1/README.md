# 검지 원곡3음 조건부 fresh F4

새 schema의 PrefixPolicy/환경을 사용하고 원 runner.run/_train·collector/PPO/save/load와 실제128cap 검증을 재사용한다. NN은 첫tick부터 선택4축을 제어하며 staged teacher는 손목만 움직인다. N trajectory는 비NN reference 대조에만 주입한다. 현재goal은 각env precontrol 원시계에서 끝나지 않은 [4,7,8] 중earliest이며 해당candidate & ~wrong일 때 DIP 양의 추가목표만 억제한다. negative와 나머지104축·native범위/rate/PD·9보상/실패는 원경로다.

CPU `probe.py --prepare`와 독립검수·최종봉인 후 root만 `cpu_inputs/commands.json`의 precheck3개를 실행한다. CLI는 `--execute precheck --control reference|zero|random`, `--execute train`, `--execute evaluate --update 0|50..300`이다. train/evaluate는 새384비NN사전대조의 독립 actual PASS 및 reference stage_ready 전에는 gate에서 거부한다. actual 분석 review/verification/acceptance 경로는 `precheck_analysis/results_v1/`이며 분석은 별도작업자 소유다. train/eval은 fresh B cost-head0 시작과 freshFalse strictload를 구분한다.

음악 music_passed, 원A native release_passed와 AND stage_ready를 분리한다. reference/zero/random 실제 성과/실패를 전부 보존하고 NN initial0과 혼동하지 않는다. 기존B와 model-only 초기73tensor가같아도 과제/손목/guard/노출이 바뀐 결합조건이라 cost-only 인과비교로 부르지 않는다. 실제 새128압현/해제/학습성과는 아직미검증이다.

출력은 기존경로/symlink를 거부하고 source/settings/cap/원모델 strict계약을 유지한다. 각 precheck/eval은 전체128 첫시도(실패포함)의3음 compact/9보상, env0 상세60Hz와 전128작은currentgoal/DIP sidecar를 저장한다. 학습은 pergoal 제어카운터만 추가하고 전128×105몸체시계열을 늘리지 않는다. 기존단음renderer CLI는3음 metadata에맞지않으므로 학습/선정후 별도최소adapter를 검수하기전 사용하지 않는다. GPU는root만 실행하며 이 폴더밖 기존소스/봉인/결과를 변경하지 않는다.
