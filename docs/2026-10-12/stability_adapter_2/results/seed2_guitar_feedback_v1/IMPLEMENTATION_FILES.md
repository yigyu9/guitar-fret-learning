# 구현 경로와 실제 줄 위치

줄 번호는 2026-10-08 실행에 사용한 workspace source 기준이다.

| 경로 | 줄 | 설명 |
|---|---:|---|
| [prepare_seed2_feedback_trials.py](</home/ajou/yigyu/3/stability_adapter_2/prepare_seed2_feedback_trials.py:19>) | 19–38 | 이전 분석 입력 closure 검사, 동일 시작조건으로 세 trial 작성 |
| [run_seed2_guitar_feedback.py](</home/ajou/yigyu/3/stability_adapter_2/run_seed2_guitar_feedback.py:18>) | 18–30 | 별도 native runner 입력 검증 및 source/trial hash closure |
| [analyze_seed2_guitar_feedback.py](</home/ajou/yigyu/3/stability_adapter_2/analyze_seed2_guitar_feedback.py:26>) | 26–35 | 저장된 run report/capture를 읽는 사후 분석 진입부 |
| [make_seed2_feedback_artifacts.py](</home/ajou/yigyu/3/stability_adapter_2/make_seed2_feedback_artifacts.py:75>) | 75–80 | 저장 분석 자료에서 그래프 산출물을 만드는 진입부 |
| [PLAN.md](</home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1430>) | 1430–1458 | 실행 결과, 해석 한계, 다음 미실행 pose 계획 |
| [프로젝트 README](</home/ajou/yigyu/3/stability_adapter_2/README.md:787>) | 787–812 | 결과 요약과 다음 단계 링크 |
| [날짜 인덱스 README](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:488>) | 488–494 | 날짜별 실험 인덱스 기록 |

native 세 조건의 명령·종료코드·경과시간은 [execution.json](execution.json)에 있다. PNG plot producer의 canonical SHA와 미측정 elapsed 설명은 [artifact_execution.json](artifact_execution.json)에 있다. 새 그래프는 21 input hash의 before/after 일치가 기록된 producer 출력이며 native call은 0이다.

프로젝트 source 문서의 line reference는 향후 수정에 따라 달라질 수 있다. 최종 보존본 및 manifest는 [source_final_manifest.json](source_final_manifest.json)에 기록될 예정이다.
