# 검지128환경 낮은 상한 진단

root만 GPU를 실행한다. `probe.py --prepare`의 CPU 검수와 최종 봉인 뒤 `cpu_inputs/commands.json`의 precheck 세 명령부터 순서대로 실행한다. 원검지row1 teacher/reference112를 유지하며 reference/zero/random 각각128환경 첫시도, 총384시도(실패 포함)다. 같은 seed7의128환경이지128seed가 아니다. 비NN 공급자는 검수된 이전 `Actions` 그대로다. Gaussian mean0/std0.1711710544767014를 선택4만 tanh하고 다른 명령은 ShortPool의 원팔안내/비선택B/엄지035가 담당한다.

새 명시128 검증은 constructor 직후 physics step0에서 native105 모든 PD 필드를 각128환경에서 직접 다시 읽는다. 원 `cap.private_contract/expected_properties/effort_loader`만 재사용하고 기존4/135/180 검증의 수를 바꾸거나 우회하지 않는다. 바뀌는 필드는 비엄지16 POSITION effort0.25Nm뿐이다. 나머지89축/엄지5축·PD·전체범위·4rad/s·90충돌·손목v3·보상9·실패·원gamma/PPO/cost head를 유지한다. 실제 controller caps까지 일치한 뒤 ShortPolicy 생성 전에 `contract.native_backend.diagnostic_native_effort`를 삽입한다.

runner/runtime의 ShortPool alias와 runner/finger_skill_runner의 두 `_pins` 경로만 child scope에서 연결하고 finally 복원한다. 학습은 원 `runner.run/_train`, 평가는 원 `_evaluate`, 영상은 기존 `03_short_learning/support/render_short_finger.py`를 연결한다. policy architecture가 전체 계약을 복사하므로 저장본의 strict identity에 낮은 상한이 남는다. 기본20Nm 경로는 이 모델을 strict load할 수 없다. 원 source/metadata/state/optimizer/RNG 검사를 완화하지 않고 과거 모델을 이식하지 않는다. 기본 J33/production20과 활성 패키지는 수정하지 않는다.

128사전 확인의 독립 검수 경로는 **`precheck_analysis/results_v1/review.json`**, 연결 verification에는 `completed`, `input_sha256`, `verified_input_sha256`가 필요하다. root의 **`01_precheck_launcher.json`**은 `completed:true`, `returncode:0`, reference/zero/random 순서의 `children` 세 개(`control`,`returncode`)를 기록한다. 각 실행의 `diagnostic_report.json`과 전체128 원장을 검증하고, 원PLAN의 reference 달성/clean≥90%·wrong≤10%·물리/손목실패0 및 zero달성≤10%를 재계산한다. random128도 모두 공개하며 새 문턱은 추가하지 않는다. 이 검수 PASS 전 train/evaluate/render는 native import 전에 거부된다. 선행40시도 검수도 입력 gate이며 소지 성과를 검지의128통과로 상속하지 않는다.

`--execute train`은 사전gate 통과 뒤 새300업데이트(1,228,800전이)를 실행한다. `--execute evaluate --update 0|50|100|150|200|250|300`은 자체 train 폴더의 새 동일계약 checkpoint만 원strict 경로로 평가한다. `--execute render --update N`도 같은128환경의 원short renderer를 호출한다. 실제 고정평가 결과 뒤 root가 모델을 선택하고 촬영한다. 초기0은 `initial.pt`,300은 `final.pt`다. 임의의 checkpoint나 다른환경수/소스 옵션은 제공하지 않는다.

출력은 새 `runs/precheck_*`, `train`, `evaluation_*`, `native_video_*`이며 기존 출력과 상위 symlink를 거부한다. 원 학습/평가/영상 보고서는 보존하고, wrapper의 `diagnostic_report.json`이 추가적인 상한·입력·alias·장면닫기 검증 결과다. 닫기 오류는 보존하고 원실패를 덮지 않으며 전체오류는 root에 전달한다. `diagnostic_inputs_after.json`은 실제 로드 소스와 입력의 전후 SHA를 확인한다. 봉인 후 PLAN을 포함한 입력은 변경하지 않는다.

env0 첫시도의 상세 trace는60Hz이고 다른127환경 전체 하중을 뜻하지 않는다. 몸체합력은 접촉쌍 압력·240Hz 최대하중이 아니다. 고정기타/유한팔안내의 제한과제이며 자유기타·다른손가락·전곡·자연스러움·학습통과는 아직 미확인이다.
