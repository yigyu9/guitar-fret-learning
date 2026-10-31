# 프로젝트 내부 GPU 최종 검증

공백 포함 별도 프로젝트 루트 `.runtime/relocated project v4/`에서 아래 실제 단계를 모두 통과했다. 프로젝트 입력·캐시·출력은 `/3` 내부이며 설치된 Python·OS·드라이버·ffmpeg는 실행 환경으로 구분한다.

| 단계 | 결과 | 소요 시간 |
| --- | --- | ---: |
| native 런타임 준비 | 통과 | 0.56초 |
| 내부 입력 감사 | 통과 | 0.82초 |
| GPU PhysX/CUDA probe | 통과 | 1.82초 |
| 새 학습1회 | 통과 | 4.32초 |
| strict 재개1회 | 통과 | 4.62초 |
| 전곡 평가2에피소드 | 통과 | 259.42초 |
| 손·전신 영상 | 통과 | 272.35초 |

small·2환경·H2에서 새 학습4전이+재개4전이, optimizer누계2회다. 손/전신은 각각1280×720·984프레임·32.8초의 유효 MP4다. 입력 SHA·장면 정상 종료·렌더 종료 코드와 실제 영상을 검사했다. 짧은 실행은 학습 성과·FK 정확도·음향 성공 검증이 아니다.

[원래 단계 report](gpu_smoke_v4/report.json) · [평가 report](gpu_smoke_v4/evaluation/report.json) · [렌더 report](gpu_smoke_v4/render/report.json) · [영상 SHA·ffprobe](gpu_verification.json) · [손 영상](gpu_smoke_v4/render/hand.mp4) · [전신 영상](gpu_smoke_v4/render/fullbody.mp4).

복사본은 GPU 검증 중 봉인 상태를 유지했다. 이후 변경은 기존 외부 fixture를 새 내부 경계에 맞춘 테스트2파일과 검증도구 timeout600초뿐이며, 핵심 실행33파일의 SHA는 복사본과 현행본이 모두 같다. 최종 테스트까지 반영한 현재 `/3` 원본에서도 새 GPU학습1회와 strict재개1회를 다시 통과했다. [현재 소스 재검증](current_source_gpu.json).

관련 검사: 경로·CAS·준비22개, 이동·체크포인트·로컬 런타임·native17개, Git 정책5개로 총44개 통과. 기존16검사 실행에서2개가 실패한 로그는 보존했고, 외부 자료를 정상 입력으로 삼던 fixture를 바꾼 뒤17개(외부 설정 거부 신규1개 포함) 전부 통과했다. 입력 제한을 완화하거나 변조/원본삭제/계보삭제 검사를 제거하지 않았다.

전곡 평가259.42초·렌더272.35초가 기존300초 제한에 가까워, 검증 스크립트의 단계 제한은600초로 늘렸다. GPU 증거는 원래300초 제한 안에서 정상 완료한 결과다.


## 후속 정리 기록

역할별 정리에서 완료된 독립 검증 복사본 `.runtime/relocated project v4/`를 제거했다. 이 문서가 가리키는 report/log·영상은 `gpu_smoke_v4/`에, 현재 소스의 모델은 `current_train/`·`current_resume/`에 보존했다. native 캐시도 유지한다. 당시 명령·수치·입력 SHA는 변경하지 않았다. [이동·삭제 검증](/home/ajou/yigyu/3/docs/maintenance/organization_20261031/REPORT.md).
