# 가슴·오른쪽 위팔 초기 지지 테스트

기타는 자유·스트랩OFF, root/하체고정·자기충돌ON이다. 왼손은 넥 삼면 근처 준비 상태다. 손을 강제 부착하지 않는다. 실제5초 비교에서 왼손 접촉이 있었으므로 이 프리셋을 왼손 무지지 증거로 쓰지 않는다.

그래픽 데스크톱의 터미널에서:

```bash
bash /home/ajou/yigyu/3/stability_adapter_2/chest_upperarm_pose_test_v1/open_v2.sh
```

Space 실행/일시정지, N 한 단계, R 같은 초기값으로 재시작, C 카메라 전환, G 형상 표시, Esc 저장·종료. 처음 정지 상태이며5초 후 멈춘다.2초부터 기타 현재좌표 기준의 가상피크 왕복 타현을 실행한다. 목표를 바꾸는 관절은 오른 Elbow/Wrist6개이며 다른75목표는 유지한다. 실제 상태는 물리적으로 움직일 수 있다. 학습 체크포인트를 연결한 연주는 아니다.

[초기값](/home/ajou/yigyu/3/stability_adapter_2/chest_upperarm_pose_test_v1/initial.json:1)에는81관절·기타actor-root·전체body native 상태가 있다. 기타 바디BB중심과actor-root좌표를혼동하지않는다. 출력은 `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_upperarm_initial_v1/interactive/sessions/` 아래 새 폴더에 저장된다.

기존 viewer와제어를 재사용한다. DISPLAY가없는현재작업환경에서 실제창/키조작은미검증이며, headless0.2초생성·실행은검증했고초기값과기타경과가영상원본prefix와동일했다. 결과영상은native카메라렌더다. 가슴접촉은타현후반에끊길수있고오른위팔/허벅지가계속지지한다.

V1 README/open.sh는nestedviewer사전SHA누락이있던이력으로보존한다. 이V2실행안내를우선한다.
