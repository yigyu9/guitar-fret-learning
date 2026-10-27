# 현재 OM 기타의 줄·프렛·타현 영역

2026-10-19 사용자 요청으로 기초 노트를 현재 모델 규격으로 고치고 실제 Isaac Gym 카메라 이미지를 생성했다. 권장 이미지는 `images_v2`, 원본 native 촬영은 `native_v5`다.

![현재 기타의 줄·프렛·타현 영역](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_model_visualization_v1/images_v2/guitar_regions.png)

| 이미지 | 설명 |
|---|---|
| [전체 기타](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_model_visualization_v1/images_v2/guitar_overview.png) | 1번 고음 E부터 6번 저음 E까지 색으로 구분한 6현·22프렛·타현 Y 범위 |
| [프렛 확대](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_model_visualization_v1/images_v2/fret_detail.png) | 22개 와이어의 실제 위치와 번호, 너트→12프렛 310.682 mm·→22프렛 447.000 mm |
| [타현 확대와 깊이 단면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_model_visualization_v1/images_v2/strike_detail.png) | 실제 판정 Y 범위와 별도 XML 보조 박스, 현 아래 깊이 1~15 mm |

## 모델과 표시 조건

실행 원본은 [현재 OM 기타 XML](/home/ajou/yigyu/3/stability_adapter_2/assets/om_body_geometry_v3/guitar_asset.xml)이다. 원본 XML과 전체 69개 mesh 선언, 사용한 측정·타현 코드 및 producer의 SHA256을 실행 전에 기록하고 완료 후 재대조했다. 공용 자산이나 기존 실험 파일은 수정하지 않았다.

장면에는 기타만 있고 휴머노이드는 없다. 원래 기타 actor는 `fix_base_link=False`, 중력 ON을 유지했다. 물리 적분은 **0회**이며 초기 정적 형상을 촬영했다. 표시용 XML은 mesh 경로와 색상·투명도만 바꿨다. 불투명한 `G:pluck_range`가 현을 가리지 않도록 표시용 사본에서만 숨겼다. 판독을 돕는 6개 줄·22개 와이어의 별도 native 표식도 추가했다. 이 표식은 학습 환경이나 접촉 판정에 사용하지 않는다.

기타를 불러올 때 생성된 root 원점 오프셋을 실제 body pose로 읽고 정규화된 quaternion으로 기타 로컬 좌표를 복원했다. 너트·22프렛·12개 현 끝점, 총 **35개 마커**의 XML 대비 최대 오차는 약 **5.33×10⁻⁸ m**다. 촬영 전후 기타 native 상태가 같음을 확인했다.

컬러 native 화면에 실제 마커 좌표를 카메라 view/projection으로 투영해 선·번호·영역을 덧그렸으며, 최종 그림은 카메라 화면을 90도 회전해 지판을 세로로 배치했다. 좌표 주석은 가려짐을 제거해 보여주는 설명 표시다. 오른쪽 아래 깊이 단면은 렌더가 아닌 좌표 설명도이며, 기타 바디의 실루엣·정적 화면은 실제 Isaac Gym 촬영이다.

## 타현 영역의 의미

- 주황 면: 현재 `StrikeContract`의 Y=-385~-255 mm를 6현 외곽 사이에 현 높이로 투영한 표시다. 면 안의 모든 점이 타현 판정을 받는다는 뜻은 아니다. 실제 교차는 각 비평행 유한현에 대해 따로 검사한다.
- 실제 깊이: `string_z - pick_z`가 1~15 mm. 현 Z=12.3 mm 기준 피크 Z는 -2.7~11.3 mm다. 횡속도 0.05 m/s 이상과 재무장 조건도 별도로 적용된다.
- 청록 점선: XML `G:pluck_range`의 보조 박스다. X=±28 mm, Y=-414~-242 mm, Z=-1.2~13.8 mm이며 실제 판정 범위와 다르다.

이 정적 그림은 현 진동·음향·접촉 성공·안정적인 연주를 검증한 결과가 아니다.

## 원자료와 재현

| 자료 | 경로 |
|---|---|
| 갱신한 기초 노트 | [guitar-basics-notes.md](/home/ajou/yigyu/3/docs/guitar-basics-notes.md) |
| 수정 전 원문 | [guitar_basics_notes_before.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_model_visualization_v1/guitar_basics_notes_before.md) |
| 권장 native producer | [render_native_v5.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_model_visualization_v1/render_native_v5.py) |
| 원본 카메라·마커·입력 SHA | [capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_model_visualization_v1/native_v5/capture.json) |
| native 실행 로그 | [native_v5.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_model_visualization_v1/native_v5.log) |
| 실제 원본 카메라 화면 | [전체](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_model_visualization_v1/native_v5/overview_raw.png) · [프렛](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_model_visualization_v1/native_v5/frets_raw.png) · [타현](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_model_visualization_v1/native_v5/strike_raw.png) |
| 좌표 주석 producer | [annotate_v2.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_model_visualization_v1/annotate_v2.py) |
| 영역 좌표·주석·그림 SHA | [annotations.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_model_visualization_v1/images_v2/annotations.json) |

native 실행은 NVIDIA GPU 접근이 가능한 `rl38` Python과 프로젝트의 Isaac Gym Preview4를 사용한다. `PYTHONPATH`는 프로젝트와 `isaacgym/python`, `LD_LIBRARY_PATH`는 rl38/lib, Vulkan ICD는 NVIDIA 설정을 사용했다. 재실행할 때는 producer를 보존하고 `--out`에 존재하지 않는 새 경로를 지정한다.

v1은 MJCF importer의 절대 mesh 경로 처리로 종료했고, v2는 world 좌표와 기타 로컬 좌표를 구분하지 못한 검사에서 중단했다. 실패 소스·attempt·로그를 그대로 보존했다. v3부터 정규화한 실제 기타 root frame을 사용했고, v4는 구도, v5는 native 표식 가독성을 개선했다. images_v1의 숫자 부호 글꼴 문제는 새 annotate_v2와 images_v2에서 ASCII 부호로 수정했다.

native 로그에는 식별자가 없는 `Could not load visual geom` 메시지 6개가 있다. 어떤 원본 시각 요소인지 로그만으로 단정하지 않으며, 표시를 명확히 하기 위해 별도 native 표식과 측정 좌표 주석을 사용했다. 전체 시각 요소가 원본과 동일하게 렌더됐다는 주장이나 물리 충돌 형상 검증은 하지 않는다.

## 검증 결과

프렛 표 22행·native 마커 35개·원본 입력 SHA 73개·주석 입력 9개와 문서 링크 37개를 대조했다. 독립 change-reviewer는 보존된 원자료·producer·최종 그림을 검수했고 Critical·Warning·Suggestion 없음으로 보고했다. 검수자가 GPU 촬영을 재실행한 것은 아니다. root의 [최종 검증 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_model_visualization_v1/final_verification.json)에 확인 범위를 남겼다.
