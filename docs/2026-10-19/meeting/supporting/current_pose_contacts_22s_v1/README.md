# 현재035/v14 준비 완료22초 접촉 표시

[완성 합본](../../result/current_initial_pose_contacts_22s.png) · [설명과 개별 그림](../../result/documents/01f_current_pose_contacts_22s.md)

- `annotate.py`: 원본 native PNG와 같은 시각의 저장 접촉/pose/카메라 행렬로만 점을 투영한 코드
- `inputs_before.json`: 원본 PNG·저장 상태·states240/contacts240·카메라·원 capture·코드·폰트 SHA
- `contact_evidence_22s.json`: 원자료11행·두 body 특징점의 world 변환·좌표 일치 오차·부위별 양성/0응답 구분·동일 시각 카메라 행렬
- `report.json`: 투영 좌표와 시점·입력 불변·원본 PNG의 당시 SHA 대조 결과
- `verification.json`: 최종 PNG 열기·접촉 집계·수치·파일 링크와 원본 불변 확인
- `PLAN.md`: 범위와 확인 목록

원본 데이터는 그대로 보존했다. 새 물리·학습·모델 렌더를 실행하지 않았으며 새 표시 이미지만 result에 저장했다. 원 녹화에서 위 시점은 없으므로 정면/측면의 실제 원본을 사용했다. 재생성은 새 버전 폴더를 사용한다. 코드가 현재 프로젝트 절대경로와 저장 원자료를 참조하므로 독립 실행 배포본은 아니다.

프로젝트 루트에서 다음 명령으로 생성했다.

```bash
PYTHONDONTWRITEBYTECODE=1 python \
  docs/2026-10-19/meeting/supporting/current_pose_contacts_22s_v1/annotate.py
```
