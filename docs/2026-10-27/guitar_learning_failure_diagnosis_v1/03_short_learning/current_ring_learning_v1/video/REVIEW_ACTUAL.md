# 마지막 약지 평균정책 영상 독립 검수

요약 판정: **문제없음 / PASS**. Critical·Warning·Suggestion 지적 없음. 이 판정은 영상과 원 평가의 재현·무결성에 관한 것이며, 해당 마지막 평균정책의 학습 성공을 뜻하지 않는다.

- 준비 입력679개와 별도 준비검수 문서2개, 실제 실행/결과 및 QA 파일을 포함한 고유718개 SHA를 확인했다. 기록된 프로세스 PID1548096/start_ticks12821008·종료코드0·terminal·입력변경 없음과 정상 장면 종료를 확인했다. 원 checkpoint SHA는9cedf526743e017475f6e5dfa7bf58f5d302999f3ba0e4875744bdb31920728b다.
- 영상 재실행의 원128 첫시도 평가 JSON은 기존 마지막300 평균평가와 정확히 같다. env0 모든 비힘 trace 필드도 같고, 순힘 최대차이3.814697265625e-6N은 사전1e-4N 허용오차 이내다.220개 control endpoint와880개 물리step, poses의 q/target/body_state를 원 trace와 직접 비교했다.
- 영상 코드의 실제 runtime snapshot 비교는 모델·actor/value optimizer 두 개·update·costweight를 포함한다. 실행 보고서의 trainer_unchanged·학습갱신0·encoder hand/fullbody 각각0·카메라/runner/factory/loader alias 복구·오류 없음이 일치했다. 검수자는 checkpoint를 로드하거나 live trainer를 새로 실행하지 않았다.
- 두 mp4 각각 ffprobe count_frames로 H264·1280×720·30fps·110프레임·컨테이너3.667초를 확인했다. 두 파일 전체를 hardware acceleration 없이 CPU decode하여 모두 종료0·오류출력 없음이었다.
- 각 영상 frame0/29/49/69/89/109의 총12개 실제 프레임을 추출해 직접 확인했다. 정방향이며 전신은 머리와 양발을 포함하고, 손 확대는 왼손과 넥이 화면에 보인다. `qa/hand_contact_sheet.png`, `qa/fullbody_contact_sheet.png`와 원 추출 프레임·media_checks.json에 검수 근거를 남겼다.

영상은 성과와 무관하게 사전지정한 마지막300 **평균행동**의 env0 첫시도다. 원 전체 평균평가의 달성은0/128이며 확률정책의52/128 사례 영상으로 해석하지 않는다. 개별 카메라 샘플12개의 시각 검수와 두 전체 파일의 미디어 decode 검증은 구분한다.30Hz 프레임은60Hz 제어의 짝수 끝점이고240Hz 물리상태 전체나 실제 접촉쌍/압력/소리를 보여주는 증거가 아니다. 고정기타·교사보조·약지·source54·seed7 범위이며 다른 손가락/seed·자유J33·원67음의 미완료 요건을 대신하지 않는다.
