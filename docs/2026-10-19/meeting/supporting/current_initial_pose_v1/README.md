# 현재 초기 자세 미디어 수집

[완성 자료 안내](../../result/documents/01e_current_initial_pose.md)에 현재 학습 기준035/v14와 오늘의 별도 자세 진단을 구분했다.

- `collect.py`: 기존 current_v3 PNG 6개·native 전신 MP4 5개와 별도 진단 초기 PNG 3개를 복사한 코드
- `manifest.json`: 원본·사본 경로, SHA, 이미지 해상도와 영상 길이·fps·frame 수·전체 decode 확인
- `source_records/current_v3/`: 기준 자세 설명·미디어·값·설정 사본
- `source_records/diagnostic_20261019/`: 오늘의 별도 잡기·놓기 결과 설명

9개 PNG 열기, 5개 MP4 전체 decode, 모든 원본/사본 SHA 일치를 확인했다. 이미 수집한 별도 진단16초 영상은 중복 복사하지 않고 result의 기존 사본으로 연결했다. 원문 설명의 내부 링크는 원프로젝트를 가리킨다. 새 시뮬레이션이나 렌더·영상 편집은 수행하지 않았다. 재수집은 새 버전 경로를 사용한다.
