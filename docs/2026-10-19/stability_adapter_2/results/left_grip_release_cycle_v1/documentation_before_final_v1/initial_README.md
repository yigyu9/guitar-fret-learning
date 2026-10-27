# 초기 자세 보관함

사용자가 괜찮다고 평가한 현재 자세를 보존하고, 오른쪽 이동 후보를 별도로 저장했다. 원본 실험·모델·기존 테스트 공간을 변경하거나 삭제하지 않았다.

| 보관본 | 성격 | 내용 |
|---|---|---|
| [현재 넥 지지 자세](/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/README_v3.md:1) | 사용자가 평가한 기존 baseline 보존 | 초기81각·전체body 상태·설정·실제 초기PNG3장·완전5초영상3개 |
| [오른쪽1cm 비교 후보](/home/ajou/yigyu/3/docs/2026-10-19/initial/right_shift10_comparison_v1/README_v3.md:1) | 기존본을 대체하지 않는 별도 후보 | 초기57각·기타회전유지/양팔24각접근조정,실제5초지지·EW6왕복검증·초기이미지/영상 |

원래 자세 실행:

```bash
bash /home/ajou/yigyu/3/stability_adapter_2/current_pose_test_v1/open_v2.sh
```

오른쪽1cm 비교 실행:

```bash
bash /home/ajou/yigyu/3/stability_adapter_2/right_shift_pose_test_v1/open.sh
```

그래픽 데스크톱 터미널에서 실행하며 처음은 정지다. Space 실행/정지,R 재시작,C 카메라,Esc 저장·종료. 실제desktop 키·마우스 통합은현재환경의DISPLAY 부재로미검증이다. 각경로는공용모델/mesh를참조하는기록물이며 독립모델배포번들이아니다. 보관 config는원본절대경로를그대로유지한다.

초기 DOF의PD 속성은 `initial_values.json`의 `PD_properties`에 있다. `native_properties.json`은 기타 imported/requested/applied 질량·COM·관성 기록이다. 자세를 다시 불러올 때 **기타 actor-root 위치와 바디 bounding-box 중심은 다른 값**임에 유의한다.

오른쪽후보는처음정착시22.91mm/5.01° 변화로원래보다초기이동이크다.2초후추가변화는.383mm/.121°로작고상완/허벅지접촉·가상EW6타현은유지된다. 종료위치는기존보다약27.7mm오른쪽이다. 후기완전삼면grip·왼손완전해제·수동평형·학습된노래성공은확인하지않았다.

[상세수치·한계·다음단계](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_SHIFT_INITIAL_COMPLETION_V1.md:1) · [영상색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_shift_initial_v1/INDEX_v4.md:1) · [변경파일/실제줄](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/CHANGED_FILES_v1.md:1).
