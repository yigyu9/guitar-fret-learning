# 기타 모델 비교 제작 자료

완성본은 [비교 이미지](../../result/images/00_guitar_initial_and_current_native.png)와 [설명](../../result/documents/00_guitar_model_comparison.md)에 있다.

- `render.py`: 두 원본 자산을 같은 Isaac Gym 환경에 불러와 촬영하는 코드
- `inputs_before.json`: XML·전체 선언 메시·촬영 코드의 실행 전 SHA256
- `native.log`: 실제 실행 로그와 로더 경고
- `capture.json`: 자산 경로·배치·카메라·실행 후 SHA·모델별 화면 영역
- `verification.json`: 결과 이미지·원본 불변·표시 범위 확인
- `PLAN.md`: 이번 촬영 범위와 확인 목록

프로젝트 루트에서 다음과 같이 실행했다. 기존 결과가 있으면 중단하므로 재촬영은 새 버전 경로를 사용한다.

```bash
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
PYTHONDONTWRITEBYTECODE=1 \
/home/ajou/miniconda3/envs/rl38/bin/python -u \
  docs/2026-10-19/meeting/supporting/guitar_model_comparison_v1/render.py
```

원본 XML과 메시를 직접 읽으며 변경하지 않는다. 모델과 입력을 별도 복제한 독립 배포본은 아니다. Isaac Gym 그래픽 장치가 필요하다. 원본 자산의 출처는 [자산 안내](../../../../../tab2body/assets/README.md)와 [OM 도면·파생 형상 출처](../../../../../stability_adapter_2/assets/om_body_geometry_v3/ATTRIBUTION.md)를 따른다.
