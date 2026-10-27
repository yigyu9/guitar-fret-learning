# 손바닥 source 평면 정렬 독립 검수

검수일: 2026-10-07. 범위는 이번 분석기·계획·검증 측정·최종 그림과 결과 문서다.
검수자는 저장 자료와 순수 수학만 확인했으며 native 실행·source query·물리 재생을 하지 않았다.
이 기록 외 코드·원자료·다른 작업자 파일·이전 동결 리뷰는 수정하지 않았다.

## 요약 판정

**문제없음.** 미해결 Critical / Warning / Suggestion 없음.

## 확인 근거

- 두 면의 outward normal은 서로 마주 보는 `n_p≈−n_g`가 목표다. `acos(clip(−dot))`와 signed 선택점-to-plane gap, patch 중심까지의 접선 거리 계산·world 변환·단위를 확인했다. 법선 대향각을 전체 SO(3) 각도나 해부학적 손바닥 방향으로 해석하지 않는다.
- SciPy 회전으로 세 조건 75개 저장 pose를 독립 재계산했다. 최대 차이는 dot 3.33e−16, 법선 간격 1.07e−13 mm, 접선 거리 5.68e−14 mm다. Target polygon의 평면 편차는 6.11e−20 m였다.
- 초기 대향각은 약 0.00001123°, signed gap은 0.050075 mm다. 이는 과거 hull–patch 최단거리 0.049807 mm와 다른 지표다. Tracking 종료의 4.750409° / 40.495078 mm / 26.445653 mm 및 OFF·bias 표값이 원자료와 일치한다.
- 입력 9개 실제 SHA, 세 구조 검사, 최초 producer 복원 사본 SHA를 확인했다. Facing hemisphere는 관측 항목으로 분리돼 있으며 정상성 gate가 아니다. 이번 분석의 native 초기화와 physics step은 모두 0이다.
- 최종 3-panel PNG를 직접 확인했고 producer·measurement·output SHA가 manifest와 일치한다. 축·범례·전체 0–0.1초 범위와 signed gap 표시가 맞다. README의 native camera 이미지는 기존 capture 재사용이며 새 촬영이나 별도 cooked 형상 검증이 아니다.
- 결과 README·CHANGED_FILES·VISUAL §58의 숫자·정의·실제 링크를 확인했다. 검증된 자료라는 표현과 새 제어 미구현 경계가 명확하다.
- Normal-only 2자유도와 전체 상대회전 목표는 중복 강제가 아닌 후속 별도 비교안이다. 법선축 회전은 연주 목표가 제어하고 안정화 orientation 항은 벌점을 주지 않는 제안이다. Soft 면 정렬은 관절 한계·충돌 회피·palm-up 조건보다 우선하지 않으며 실제 controller는 아직 구현·시험하지 않았다.

## 검토한 SHA-256

| 항목 | SHA-256 |
|---|---|
| analyze_palm_plane_alignment.py | 1b09a7e5ce34d0fb5c235aad5d3cb588cd4abfd47cd623eb6bfe092b5f461f0a |
| plot_palm_plane_alignment.py | 087f4cc6a18278075708fd2e3ef56a7cabb24b86f0f78f4a7a1c7cdae2a524dc |
| validated/measurements.json | 7bf4a5b7b1b6383642fcc0719f8a53a83f93d7d1208946aefb09c627252c7d09 |
| artifacts/palm_plane_alignment.png | cb3d30e9b64bd70c04dbcd892a7bb8379131312aacb268bb5a4869414e4573bf |

## 최종 검수

남은 finding은 없다. 초기 정렬이 이미 좋다는 관측은 평행성만 추가하면 손바닥 접촉이나 기타 안정성이 확보된다는 근거가 아니다. Source facet 관측은 cooked 접촉·압력·지지력 인증이 아니다. 이 검수 기록을 동결한다.
