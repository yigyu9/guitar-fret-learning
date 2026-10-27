# 실제 기록 계층에 맞춘 10 fps 래퍼 교정

V5 사전 CPU 검사는 원 StrapTrialRecording 구조를 흉내 냈으나 실제 수평 전신 runner는 이를 GymTrialRecording으로 바꾼다. 실제 계층은 StringTrialRecording → GymTrialRecording의 두 층이며 Gym에는 raw 속성이 없다. recording_v2의 세 번째 raw 접근은 실제 생성 시 AttributeError를 일으킬 코드 오류다. 실제 시뮬레이터를 시작하기 전 발견했으며 기존 producer5·recording2·preflight5는 그대로 보존한다. V5 사전 기록 검사를 실제 기록 성공으로 채택하지 않는다.

1. 새 recording_v3는 실제 두 층 self/strap만 fps10·interval24로 설정하고 동일한24step 필터와 중복 방지를 사용한다. 실제 runner처럼 String의 Strap 클래스를 GymTrialRecording으로 바꾸는 CPU 생성 경로를 검사한다. 실제 원 생성자를 실행하되 파일 출력은 새 임시 디렉토리에 두며 카메라 capture는 모의로 바꿔 호출 주기만 검사한다. 수치240Hz·목표60Hz는 접근하지 않는다.
2. 새 prepare_v6/preflight_v6/press_v6/combined_v6에서 source5의 수치 명세·경로·복귀 범위를 그대로 유지하고 실제 두 층 기록 검사를 교체한다. source5 검사를 소급 성공 처리하지 않는다. runtime_v3와 Motion4/run4/analyze5의 전신 제어 조건과 검증 구간은 완만 복귀 계획대로다.
3. 독립 검수 후 실제16초 압현부터 실행한다. 실제 capture.json의161개 고유 표본·24step 간격·끝점·render 상태 불변과 ffprobe10fps/161개/16.1초를 확인한다. 원 V4와 첫13초 수치 exact가 렌더 간격 변경의 물리 영향도 확인한다. 이후 결합 동작과28초 해제의281프레임도 동일하게 검사한다. 프레임 재생 길이는 종료 표본 한 장을 포함하므로 물리16/28초와 각각0.1초 다르다고 기록한다.

- [ ] 실제 Gym 생성 경로 CPU 검사와 새 source6
- [ ] 새 래퍼 검수와 실제 영상·수치 prefix 검사
