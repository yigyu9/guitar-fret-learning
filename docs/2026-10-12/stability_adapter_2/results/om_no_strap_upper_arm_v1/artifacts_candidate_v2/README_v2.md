# 초기 기타 목 옆 상완 유지 후보 · 패널 v2

이번 v2는 소비된 v1 패널의 footer 배경이 마지막 캡션보다 짧았던 표시 문제만 보완합니다. 기존 v1 PNG·producer·provenance는 그대로 두고, 패널 배경 높이를 50 px 늘렸으며 두 footer 문장의 실제 text bounding box가 배경 안에 포함되는지 검사했습니다. 데이터, 수치, 캡션 내용은 바꾸지 않았습니다.

![native 11 초기 자료와 0, 0.5, 2, 5초 whole_body 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/artifacts_candidate_v2/native11_initial_and_timeline_v2.png)

![native 11 whole_body 0초와 5초 프레임 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/artifacts_candidate_v2/native11_zero_to_five_comparison_v2.png)

0→5초 비교 그림은 v1의 검증된 PNG를 그대로 복사했으며 SHA-256도 일치합니다. 이 v2는 문서·그림 후처리만 수행했습니다. native 물리/제어 실행 0회, MP4 재복사 0개입니다.

## 결과 문맥

두 번의 동일 초기조건 5초 평가에서 bounding-box 중심 변화는 40.206626858 mm, actor-root 위치 변화는 53.017169762 mm, 초기 대비 SO(3) 회전은 11.070531790°였습니다. 2초→5초 중심 변화는 0.073932230 mm, 회전 변화는 0.028842817°였습니다. 이는 초기 조건의 5초 유지 후보이며 움직이는 연주 강건성이나 학습 성공을 뜻하지 않습니다. actor-root와 bounding-box 중심 지표를 혼동하지 마세요.

v1 수치의 접촉·제어 해석 및 RH finger query 제한은 [v1 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/artifacts_candidate_v1/README.md)에 있습니다. 기존 동영상은 다시 복사하지 않았습니다. 보관 영상 목록은 [manifest_v3.json](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/manifest_v3.json)에서 확인할 수 있습니다.

## 기록

- [새 패널 producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/artifacts_candidate_v2/build_candidate_v2.py)
- [입력·출력 SHA-256 및 footer bbox 검사 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/artifacts_candidate_v2/provenance_v2.json)
