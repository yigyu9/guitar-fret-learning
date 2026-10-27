# OM 시각/충돌 비교 제작 근거

[완성 비교 그림](../../result/guitar_visual_vs_collision.png) · [결과 설명과 한계](../../result/documents/00b_guitar_visual_collision_comparison.md)

- `render.py`: 원본 OM v3 자산을 별도 정지 장면에 불러오는 native 촬영 코드. 원본 XML·메시는 바꾸지 않는다.
- `inputs_before.json`, `capture.json`: 촬영 입력 전체 SHA, native body별 shape 수·filter·contact/rest offset, 카메라·배치·촬영 PNG SHA. G:body 63개 shape 확인.
- `native.log`: 실제 native 실행과 시각 geom 로드 오류6개 보존.
- `native_arrays.npz`: visual/collision 각 카메라의 원본 depth·body segmentation 배열.
- `plot.py`: 원본 카메라 화면과 segmentation 겹침, 공통 바디 픽셀의 깊이 차이 과학 그림 생성.
- `analysis.json`, `plot.log`: 모든 depth 통계·source XY 표본오차·해석 범위. 최대값과 경계의 큰 차이도 보존.
- `figure_drafts_v1/`: 제목 간격 조정 전 그림과 제작 코드. 최종 그림은 result에 있다.
- `PLAN.md`: 작업 범위와 검증 목록.
- `verification.json`: 최종 원본 불변·PNG 열기·통계·문서 링크 검사.

렌더는 rl38 Python에서 Isaac Gym을 NumPy보다 먼저 import하고 그래픽 장치0, CPU PhysX, GPU pipeline OFF, 물리0step으로 실행했다. 비교 전용 actor만 fix_base/disable_gravity로 배치했다. contact/filter 값은 `paper/object/evidence/native_shape_reference.json`의 실제 저장 참조를 적용/readback했으며 지지 제어·mass·학습을 재현하는 장면은 아니다.

촬영 재실행은 새 버전 디렉토리를 사용한다. native 원본 PNG는 result/images/guitar_collision_comparison_v1에 있으며 plot은 이 PNG를 별도 비교표로 조립한다. 원자료가 이미 존재하면 덮어쓰지 않는다. 실제 운용 환경의 절대경로와 Isaac Gym GPU 장치가 필요한 프로젝트 내부 제작 자료이며 독립 배포 번들은 아니다.

프로젝트 루트에서 사용한 환경:

```bash
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python \\
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \\
PYTHONDONTWRITEBYTECODE=1 \\
/home/ajou/miniconda3/envs/rl38/bin/python -u \\
  docs/2026-10-19/meeting/supporting/guitar_collision_comparison_v1/render.py
```

그림은 `MPLCONFIGDIR=/tmp/meeting_guitar_collision_matplotlib`를 사용해 `plot.py`로 만들었다. 수치와 그림은 임의3D 모델 복원이나 AI 이미지 생성 결과가 아니다.
