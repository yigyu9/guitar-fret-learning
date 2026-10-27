# 수동 테스트 기본값: 기존 앉은 humanoid 자세 복원

오른쪽으로 휘어진 몸통이 기본값으로 들어간 문제를 지적한 사용자 요청에 따라, 수동 테스트의 상체81관절을 공용 seated_pose.json의 기존 초기각으로 복원했다. 추가 몸통 옆굽힘·회전·머리 보정은 승계하지 않는다. 임의의 모든0각 자세를 만든 것이 아니라 기존 앉은 모델 자세를 사용했다.

기타 초기 actor-root 위치·quaternion은 이전 native_wrap55_static 수동 테스트 배치와 동일하다. Root·하체 고정, 모델 형상·질량, 스트랩OFF, 조작·물리 기능은 유지한다. 이 조합의 접촉 비겹침이나5초 기타 안정성을 인증하는 변경은 아니다.

## 실행

기존 창을 닫고 다음 명령으로 다시 시작한다. V1/V2 파일과 연구 실험은 보존하며 새 기본값은 V3 실행에 적용된다.

```bash
bash /home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/open_v3.sh
```

이 실행에서 ‘원본 자세’ 버튼은 복원된 기존 앉은 자세로 돌아간다. ‘시험 초기화’는 여전히 마지막 ON 직전 사용자 배치로 돌아간다. 저장한 별도 초기값을 --initial로 지정하면 그 값이 우선한다.

## 검증

- 81개 이름·원본 관절각 대응·finite·native 모델 범위를 확인했다.
- 원본에서 이미 모델 한계를 약간 넘던 LH:thumb1_x/y/z 세 좌표만 기존 초기화와 같은0으로 처리했다. 원본 모델·seated_pose.json은 수정하지 않았다.
- 기타 p/q 및 생성 입력 SHA 전후 불변을 확인했다.
- 새 기본값의 CPU PhysX 초기화, OFF0step, ON12step(0.05초), 리셋0step 검증을 통과했다. native 실제 입력145개 SHA 전후 일치를 다시 확인했다.
- DISPLAY 부재로 데스크톱 조작창·화면 렌더는 이번에도 확인하지 못했다. 과거 GUI 검증 한계를 그대로 유지한다.

[초기값 검사 원자료](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/manual_pose_lab_v1/upright_default_v1/preset_check.json:1) · [Native 검사](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/manual_pose_lab_v1/upright_default_v1/native_check/native_check.json:1) · [Native 로그](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/manual_pose_lab_v1/upright_default_v1/native_check.log:1)

## 새 파일과 실제 줄

- [계획](/home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/UPRIGHT_DEFAULT_PLAN_V1.md:1)
- [초기값 생성](/home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/build_upright_initial_v1.py:17)
- [복원한81관절 초기값](/home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/upright_initial_v1.json:86)
- [새 기본 실행 파일](/home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/open_v3.sh:4)
- [최신 사용 설명](/home/ajou/yigyu/3/stability_adapter_2/manual_pose_lab_v1/README_V3.md:1)
