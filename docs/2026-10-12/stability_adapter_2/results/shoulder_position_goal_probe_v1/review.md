# POSITION 어깨 pulse 독립 최종 검수

요약 판정: 문제없음. Critical 없음 / 미해소 Warning 없음 / 미해소 Suggestion 없음. 현재 단계의 구현·저장 원자료·분석·native 영상·최종 문서 검수를 완료했다.

- OFF/X/Y/Z 네 실행 모두 실제 1,200 physics steps, 151 camera frames, 7개 계약을 확인했다. 조건당 raw states 155개는 step 0,1–4,8…1200이다. 조건 간 초기 native 상태·PD properties는 exact다. 제출 시점 0·4의 81개 native 목표 readback과 저장 표본을 대조했고, pulse는 해당 한 축에만 float32 nominal +0.02rad를 적용한 뒤 baseline 목표로 복원했다.
- `analyze_shoulder_position_goal_probe_v2.py:28–62`의 16개 step1–4 행을 원자료에서 독립 계산했다. 전체 81축 q/velocity/total-force 차이, R_Thorax–R_Shoulder parent-relative 회전 차와 초기 보정된 Exp(Bq) FK가 일치한다. 최대 FK 오차는 1.832856932×10⁻⁵°다. 새 분석기 AST Python3.8 문법 검사도 통과했다.
- Step4 scalar DOF 응답 행렬은 summary와 exact다. 자기 좌표 반응은 X +0.001144283, Y +0.001002938, Z +0.000881344rad이며 off-diagonal 변화도 있다. 이 행렬은 body 회전의 x/y/z 벡터가 아니다. 짧은 연성 반응만으로 POSITION 목표 chart/축 교환·큰 tracking error의 단독 원인을 인증하지 않는다.
- Native 입력 closure OFF 1,069/X 1,070/Y 1,074/Z 1,074개를 각각 당시 목록으로 대조했다. 각 조건에서 현재 1,067/1,068/1,072/1,072개와 `source_before`의 exact archived 2개로 모두 해결됐으며 unresolved는 0이다. 실행 사이 추가된 파일을 과거 실행의 입력으로 소급하지 않았다. 별도 분석 입력 33개는 현재 SHA 및 before/after가 일치한다.
- 네 조건의 전신/손 영상 8개 모두 실제 파일 SHA와 ffprobe 1280×720, 151 frames, 30fps, 5.033333초를 확인했다. OFF 초기 전신·X 종료 손 PNG를 직접 보았고 README/CHANGED의 절대 링크와 native 이미지 출처를 확인했다. 첫 4-step 반응은 30fps 영상보다 저장 원자료로 판단한다.

해소된 Warning: README:5–13의 scalar DOF q 변화 표를 shoulder-relative body 회전으로 설명한 문구를 수정하고 parent-relative/FK 값을 별도로 구분했다. 수정 전 README는 `doc_before_final_coordinate_wording/`에 보존됐다. 후속 EFFORT 미실행 문구도 별도 phase의 진행/검수 범위로 좁혔고 수정 전 문서는 `doc_before_followup_status/`에 보존됐다. 사전 검수의 getter finite/layout 및 cleanup 보존 수정도 실행 소스에 반영됐다.

확인 SHA256: runner `e2932dc577a0698e7bd3a5ac3c97ac76b617acc303ebf1bb41111d95bb25abad`, wrapper `336c61faafac5c86cd03284a251f2b12a840fd895bed7edd05aff75f6a65b7cd`, 분석기 v2 `aeecc17e04beba358632f92d5352c9dc4700347709e193300e031a9f32b0d0d5`, 분석 요약 `2c7a78d4d284dd1c5c757822ca96a4e45505d50e7a57bda377232cfc0b85d954`.

검수는 저장 자료·순수 NumPy/SciPy 계산·SHA·AST·ffprobe·이미지 확인 범위이며 추가 native 초기화/physics는 0회다. Getter force는 합성 total force이고 drive 전용 토크가 아니다. Mass matrix는 읽기 전용 참고이며 제어·정확한 virtual inertia 인증에 사용하지 않았다. 연주·지속 지지·학습 성공과 후속 EFFORT 결과 및 root의 최종 보존 감사는 이 완료 판정에 포함하지 않는다. 이 review는 동결한다.
