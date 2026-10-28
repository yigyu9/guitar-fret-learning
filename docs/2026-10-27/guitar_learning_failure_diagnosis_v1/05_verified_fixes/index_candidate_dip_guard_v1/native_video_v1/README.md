# 검지 DIP guard 실제 영상 준비

`render.py --prepare` → 독립 준비검수/최종봉인 → root만 `render.py --execute` 순서다. 출력은 새 `runs/guard/`이고 기존 경로/symlink는 gate/native import 전에 거부한다. 아직 native 영상/픽셀·codec 정합은 미검증이다.

원 renderer·B300 strict/fresh=False·128cap/90pairs·동결된 guard observer를 재사용한다. 새 renderer/물리/목표/카메라 변경은 없으며 output과 superset pins만 새로 연결한다. 전128 DIP sidecar를 남기되 전체 관절/몸체 상세와 영상은 env0 첫시도뿐이다. 원 renderer는 평가 callback을 호출하지 않으므로 evaluator의 RNG/모델 fingerprint가 수행됐다고 기록하지 않고, renderer 자체의 strict load/model unchanged/checkpoint SHA/updates300/scene·encoder 종료를 검증한다.

기존 B300 `native_video_000300/{hand,fullbody}.mp4` 두 영상은 출처와 기존 QA SHA를 확인해 대조로 재사용한다. 새 영상은 guard 실행이지 무개입 B300 정책성과나 새 학습·전체128 영상·자연스러움/해제 인증이 아니다. actual 종료 뒤 별도 qa/에서 221끝점/220decode/8대표PNG와 원평가 sidecar·원trace 정합을 검수한다.
