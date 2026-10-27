# 수동 자세 테스트 공간 구현 결과

요청한 물리 ON/OFF, 기타 위치·회전, humanoid 관절각, 환경 초기화를 별도 모듈로 구현했다. 현재 실행기는 open_v2.sh다. 기존 stability_adapter/·공용 자산·연구 소스·기존 실험 산출물·메인 계획서는 수정하지 않았다.

- [실행·조작 설명](/home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/README.md:1)
- [사전 계획](/home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/PLAN.md:1)
- [현재 실행 파일](/home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/open_v2.sh:1)

## 확인한 내용

첫 버전 순수 동작 테스트9개: OFF 무적분, ON의 pose setter 미사용, ON 관절 변경은 목표만 적용, ON 기타 직접 편집 거절, 리셋 상태·속도 복원, 기타 강체들의 상대 배치 유지, 바디 중심 회전, 관절 한계/NaN 거절, 초기값 저장.

V2 추가 테스트3개: 사용자 편집한 시험 시작 배치로 리셋, 원본 복원 분리, 저장 초기값 재불러오기.

Native CPU PhysX 검증 V1/V2는 각각12 physics step(0.05초)를 수행했고 OFF0step·ON12step·리셋0step·입력 SHA 전후 불변을 확인했다. V1은 이후 수정하지 않았으며 V2는 시험 리셋/저장값 재불러오기를 새 파일에서 보완했다. 두 native 초기화는 연구 스레드의 안정화 trial에 합산하지 않는다.

- [V1 실제 검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/manual_pose_lab_v1/native_check_v1/native_check.json:1)
- [V2 실제 검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/manual_pose_lab_v1/native_check_v2/native_check.json:1)
- [V2 실행 로그](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/manual_pose_lab_v1/native_check_v2.log:1)

Guitar는free이며 root/lower는fixed 모델이다. 기타 질량은 기존 보정기준 합계4.648716kg다. 미측정 물성을 실제 기타 실측값으로 설명하지 않는다.

## 아직 확인하지 못한 내용

현재 실행 환경의 DISPLAY가 없다. Xvfb를 이용한 Tk 조작창 검사도 display 연결 실패로 종료됐다. [해당 로그](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/manual_pose_lab_v1/ui_check_v1.log:1)를 보존했다. GUI 화면을 생성했다거나 직접 조작해 검증했다고 주장하지 않는다. 실제 데스크톱에서 viewer·조작창·키보드·슬라이더의 동시 사용 확인이 필요하다.

CPU headless 로그에는 CUDA device 접근 및 visual geom 관련 오류/경고가 출력됐지만 물리 초기화·12step·입력 보존 검사는 완료됐다. 이는 그래픽 렌더 검증을 대신하지 않는다. Native setter의 articulation 경고도 원문 로그에 남겼다.

GUI 검증용 check_ui.py는 native viewer API stand-in을 사용하는 별도 검사이며 일반 실행기에 연결하지 않는다. 화면 연결 실패이므로 GUI 성공 판정을 내리지 않았다. 독립 서브에이전트 검수는 이 side conversation의 제한에 따라 수행하지 않았다.

이 공간은 수동 배치/기본 PD 실험용이다. 기존 상완 지지·왼손목 추종 controller, 스트랩, Fret/Strike 정책이나 학습을 추가하지 않는다. OFF의 명시적인 편집/리셋과 ON의 물리 경과를 구분한다. 접촉 개수는 관통 깊이·접촉력N·안정화 성공 판정이 아니다.
