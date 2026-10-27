# 약지·소지 검사 최종 문서·확대 영상 검수

요약 판정: **문제없음.** 실제 검사 결과의 국소 운동·복귀 확인과 남은 추종 오차를 구분했고, 확대 영상 v2의 원자료 대응 및 매체 검증도 통과했다.

## 범위

최종 phase README와 새 `learned10_closeup_video`의 report/presentation/입력 pins/pose audit/실제 MP4, `video_v2_qa.json`을 확인했다. 앞선 `review_results.md`에서 검산한 36개 검사·2개 native 원자료를 다시 분석하지 않았고, README의 주요 수치를 검산된 `analysis.json`과 대조했다. GPU·native physics·GL·Renderer·기존 main은 실행하지 않았다. CPU SHA·JSON 대조·독립 ffprobe만 수행했다.

## 확대 영상 v2

- **1,487개 입력 SHA**와 실제 MP4 SHA `fe78ad20cb1ddffa3cd40e7d82bba1b3ff2e1a95aabff5095a3b87165f515625`가 report·QA와 일치한다. 원자료·활성435소스·이전881파일 봉인 입력도 유지됐다.
- 독립 ffprobe로 **H.264 / 1280×720 / 60fps / 720프레임 / 12.000000초**를 확인했다. 이는 실제3초 검사 네 개를 연결한 영상이며 추가 물리·보간·학습은 없다.
- 선택 case **5/10/14/17**은 원래 native 여유 규칙과 같다. 전체720개 audit 행의 case/clip/source frame601..780/source clock이 정합한다. 기록된 pose 오차는1e-9 이내이고 renderer clock0·새 물리0·손 화면 projection guard가 통과했다.
- 각 audit 행의 projection을 제외한 모든 필드는 보존된 v1 audit과 정확히 같다. v2는 카메라의 손 중심 범위만 바꿨으며 원래 동작·자세 선택을 바꾸지 않았다. neck 전체가 화면 안에 있다고 확대 해석하지 않는다.
- root의 처음/중간/끝 및 release preview QA 파일이 실제로 존재하고 기록된 실행 exit0·매체 결과와 일치한다. 가독성의 시각 판단은 root QA 범위다. 이 검수는 새 GL context를 생성하거나 pose readback을 다시 실행하지 않았다.

## README 결과와 한계

주요 표의 learned10 ring2 목표−0.20000/실제−0.19958rad, pinky1_z 목표+0.20000/실제+0.13982rad, pinky3 실제+0.19904rad가 검산된 분석과 일치한다. 실제 이동량이1초 pulse 뒤0.5초 유지한 endpoint 기준이라는 설명도 맞다.

두 자세에서 실제 target 이동0.05rad 이상인 방향은 각각12개이고 그 방향으로 실제 q가 움직였다는 결과와, 나머지 방향의 native 한계·무여유를 구분했다. 복귀 후 시작 q 대비 잔차 최대 prepared0.000429rad / learned10 0.01530rad를 남겨 완전한 실제 자세 복원으로 주장하지 않는다.

소지 기저축은 prepared에서 유지 끝 q−target≈−0.09922rad의 추종 오차가 남는다. learned10의 시작 오차+0.09682→유지 끝+0.03664rad를 함께 제시해 이동량 비율69.9%를 절대 목표 미달로 오인하지 않는다. 목표 유지 오차0과 실제 q의 정확한 고정·추종도 구분했다.

소지3의 유지 구간120개 native 표본 norm0 및 복귀 후 양성 재발을 접촉 합력의 변화로 기술하고, norm0을 모든 접촉쌍·압력의 부재로 인증하지 않는다. 8축 coordinated target의 준비 reference 도달도 전체 준비 q/body 복원이나 후반 무접촉을 뜻하지 않는다고 명시했다.

N18 prefix와 이전 N1024 영상의 작은 시작 차이·고정 case ID·두 자세·0.2rad/s의 짧은 국소 운동 범위를 유지한다. 따라서 '시험한 상태에서 빠져나올 수 없는 고정 끼임이라는 근거를 확인하지 못했다'는 제한적 결론은 자료에 맞으며, 모든 자세의 끼임 부재·완벽한 운동·학습 개선을 인증한다는 주장은 없다.

Critical / 수정이 필요한 Warning: 없음.

이 검수 문서만 새로 작성했으며 작성 종료했다. 활성 소스·기존 도구·기존 검수·원자료·과거 봉인 결과는 수정하지 않았다.
