# V2 native video 준비 독립검수

2026-10-28 **PASS**. 검수 중 GPU/native 실행0. 이는 실행 준비 코드·원입력의 검수이며 아직 생성되지 않은 MP4의 실제 픽셀·재생·frame 수를 인증한 결과가 아니다. root가 `review.json` SHA를 준비 seal에 연결한 다음 실행해야 한다.

검수 범위는 `render.py`, `cpu_check.py`, 실제 참조하는 V2/V1 공유 실행 경로와 camera/encoder helper다. 준비 seal의502개 입력을 전부 재해시했고 불일치·읽기오류가 없었다. CPU fixture, source preflight, 두 Python 구문 검사가 모두 통과했다. source env0 원trace의354×105 q/target,354×106×13 body, clock4~1416을 확인했다. 원 V2 deterministic 조건은128개 고유env 첫시도 완주, stage_ready=true, all3=124/128, 해제128/128이다. 이것을128/128 음악성공으로 바꾸어 주장하지 않는다.

native step 이후 capture를 호출하고 원 base loop가 이후 reset하는 순서를 확인했다. env0 first attempt를 고정하며 camera helper의 physics_step==4*control_tick 검사가 reset/누락을 거부한다. 짝수 control endpoint만30fps로 기록해354controls→177frames이고,1280×720 camera/encoder 설정이 일치한다. 두 영상은 원 V2 scripted reference 경로로 실행되며 NN·checkpoint·PPO를 호출하지 않는다. 원 기타/물리 제어와 reference action은 공유하고 graphics device/camera만 추가한다.

실행 후 q/target/body_state/candidate가 원 V2 NPZ와 완전히 같고128개 episode ledger 전체가 원 V2와 같아야 PASS가 기록된다. 별도 capture의 q/target/body_state도 실행trace와 exact여야 한다. 354controls/177frames 불일치나 trace/ledger 차이는 `video_verification.json`을 실패로 남기고 예외를 전파한다. 카메라/FFmpeg 실제 결과가 없으므로 이 후검증을 생략할 수 없다.

추가 stdlib fixture로 encoder 오류 시 partial capture 저장과 scene close 후 오류 전파, camera 생성 오류 시 원예외 유지와 acquire hook 복원을 확인했다. 기존 `cpu_check.py`의 step→capture 순서·9보상·capture pipe 오류 후 행 보존·V2 alias 오류복원 검사도 통과했다. `execution_scope`가 base HERE/SCHEMA/support를 복원하고 외부 finally가 geometry hook을 복원한다. 기존 출력 파일을 덮어쓰지 않는 배타적 생성 경로도 확인했다.

현재 actionable finding은 없다. 원자료·활성소스·seal은 검수자가 수정하지 않았다. root는 review SHA를 연결하면서 이미 pin한 PLAN/code/input을 바꾸지 않아야 한다. 실제 실행 이후에는 `report.json`의 completed/closed/cleanup/input audit, `capture.json`, `video_verification.json`, 두 MP4의 실제177frames/5.9s/30fps/1280×720과 픽셀을 함께 확인해야 한다.
