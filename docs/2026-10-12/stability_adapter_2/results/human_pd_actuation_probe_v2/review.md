# 관절 구동 효과 진단 독립 검수

요약 판정: 문제없음. Critical 없음. OFF 명령 설명 Warning은 원문 보존 후 해결됐다. 이번 검수는 소스·저장 자료 읽기, 독립 수치 대조, SHA·영상 메타데이터 확인에 한정하며 native·분석기를 재실행하지 않았다.

- [runner](/home/ajou/yigyu/3/stability_adapter_2/run_human_pd_actuation_probe_v2.py:36)는 `GraphicsGym → NoStrapGym → native Gym` 타입을 확인하고 지정한 human 관절 tensor API만 호출한다. 81 DOF 중 오른팔 12축만 effort 한계 내 명령하며 나머지 69축은 0이다. 기타/body/root 외력 및 상태 쓰기 guard는 우회하지 않는다. OFF 역시 매 physics step 동일 API에 0벡터를 제출한다.
- OFF/ON 초기 native 상태, PD 속성, 절대 목표와 저장 Kp가 exact다. 각각 1200 steps·151 frames·7개 검사 true이며 실패 기록은 없다. 300개 명령의 시점은 0,4,…,1196이다. 모든 명령의 81개 값·effort 한계·69축 0을 대조했다. 저장 상태가 있는 151개 ON 명령은 float32 `clip(Kp*(target-actual),±effort)`와 exact다. 첫 `R_Shoulder_z` 요청은 OFF 0 / ON 10.000001907348633 Nm다.
- [원자료 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/analysis/summary.json:1)을 독립 대조했다. 0,4,8,…,1200 step의 152개 전체 native 상태가 OFF/ON exact다. DOF 위치·속도뿐 아니라 모든 human/G body 상태를 포함한다. 첫 4 physics steps와 전체 저장 표본의 차이는 0이다. 이 CPU/POS 구성에서 제출 torque의 상태 응답 증거가 없다는 결론은 타당하다. 요청값은 측정 힘이 아니며, 저장 표본 사이의 모든 내부 solver 상태나 다른 구성의 actuator 효과를 인증하지 않는다. hybrid 구동·타현·연주 성공 근거로 확대하지 않는다.
- 보존 wrapper의 시작 전 입력 SHA와 source 사본을 대조했다: OFF 1009 inputs/265 source copies, ON 1012/268. 종료 metadata는 두 실행 모두 변경 0·task error 없음이다. 현행 runner·wrapper·leaf SHA는 각 실행의 before SHA 및 사본과 일치한다. 분석기의 11개 직접 입력은 현재 SHA exact이고 before/after 변경 0이다. 새 소스의 Python 3.8 AST도 통과했다.
- 604개 native PNG의 capture SHA와 readonly 표시, 각 151개 표본의 시각을 확인했다. 0/2/5초는 frame 0/60/150이다. 네 MP4의 실제 SHA와 독립 ffprobe 결과는 각각 151 frames·30 fps·5.033333 s다. 같은 view의 OFF/ON 영상 SHA도 exact다. 실제 5초 손 PNG를 확인했다.
- v1 실패 report는 physics 0/frame 1·완료 false이며 `set_dof_actuation_force_tensor` guard 오류다. v1 입력 1006개 변경 0과 오류 로그가 보존되어 있다. v1을 완료 비교나 actuator 응답으로 사용하지 않았다. 미실행 hybrid 경로의 기존 한 층 wrapper 오류 역시 이번 결과로 해결됐다고 주장하지 않는다.
- [README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/human_pd_actuation_probe_v2/README.md:3)의 OFF 설명은 0벡터 제출로 정정됐다. 정정 전 README/색인은 `doc_before_zero_command_correction`에 보존됐다. 표, 네 영상 embed, 실제 파일 링크와 [PLAN 기록](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:251)·[프로젝트 README](/home/ajou/yigyu/3/stability_adapter_2/README.md:1556)의 범위 표현은 실제 결과와 정합한다. 후속 READY 잔차 시험은 이번 probe 성공 판정에 포함하지 않는다.

최종 검수 SHA-256:

- runner: `06981824059588d7c8cabd1a87ba60ef6a357dcb56cdf0464d2c08275b98b606`
- wrapper: `7871c4b20bede74aafc059eb27ebeeef9f1bc8a2ed998d878cc6e394e72947d8`
- leaf: `505f4a185b228a4d37a0b0fa41db85754910c4ed66b4ed4800b6c0a24b067032`
- analyzer: `1f8b25fcf82b1993e828dcc4da62288ed541b8b36d5981227ae106ff42618d1f`
- analysis summary: `2c7fce5d52046f748fc7dfa3610051d71176cf9e00c52d64ca992e4ef3eb2fdb`
- README: `0a2aef9b2f73ffdde8a61447ca4517501e0d4f775819afb2451867ba346a5fd0`
- CHANGED_FILES: `d31ffd614529f3f46bb225a31556ffe11cf8397241f3d7d9c8a9a480b4312147`

최종 판정: PASS
