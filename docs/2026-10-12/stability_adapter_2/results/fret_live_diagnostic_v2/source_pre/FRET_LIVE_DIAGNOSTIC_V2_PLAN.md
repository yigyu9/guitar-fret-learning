# Fret 진단 v2 — native 이미지 배열 저장

v1 계획의 좌표·관측·제어·준비2초·첫 원본 done까지 녹화를 그대로 유지한다. v1과 동일 재시험이 각각 0.866667초/0.833333초 뒤 native `write_camera_image_to_file` 호출에서 exit139로 중단됐다. 원인은 미확정이며 실패 입력 SHA는 모두 불변이다. 두 원본/partial 영상은 `results/fret_live_diagnostic_v1/`에 보존한다.

v2는 raw recorder의 파일 저장 경로만 바꾼다. 같은 Isaac Gym camera sensor의 `get_camera_image(IMAGE_COLOR)` 반환 RGBA 배열을 즉시 복사하여 PIL로 PNG 저장한다. 카메라·render 순서·센서·물리·PD·actor·goal·진단 수학은 그대로다. 기존 source 및 runner는 수정하지 않는다. native 배열 저장은 실제 Isaac Gym 픽셀이며 별도 시뮬레이터 렌더가 아니다. PNG encoding byte SHA는 이전 native writer와 다를 수 있으므로 비교는 초기/공통 프레임 RGBA 픽셀 및 전체 control/trace로 한다.

1. 새 recorder/wrapper와 문법·사전검수. 읽기 전용 검사/진단은 frozen v1 recorder에서 상속한다.
2. 새 `results/fret_live_diagnostic_v2/native/`에서 full native 실행. 실패하면 새 경로를 사용하고 원본 유지.
3. frozen analyzer로 분석·baseline exact control/trace 대조, 원본 카메라 픽셀 대조, 이미지/전체 영상·검토·보존 봉인. 관측 source tensor/목표/상태 불변이 필수다. 운지 실패를 영상 저장 성공과 혼동하지 않는다.

root 소유: 새 구현/실행/분석·main PLAN·최종 감사. 검수자는 별도 review.md만, Luna는 지정 README/FILE_INDEX만 소유한다. 이번 소단계는 보정 제어/학습/전체 회전집합 판정 없음.

- [ ] 새 저장 경로 사전 검토
- [ ] 원본 first done까지 전체 실행 및 진단
- [ ] baseline/픽셀/보존 검증·산출물·독립 검토

실행 소비 후 leaf/source를 수정하지 않고 완료 기록은 main PLAN에 추가한다.
