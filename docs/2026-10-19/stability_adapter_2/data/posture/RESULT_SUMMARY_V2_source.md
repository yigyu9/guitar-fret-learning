# 스트랩 없이 왼손을 떼는 초기 자세 — 관측 결론

오른쪽 상완을 기타 바디의 넥 쪽 위테두리에 접근시키는 초기 자세와 관절 토크 제어를 구현했다. **스트랩 OFF·왼팔/왼손 접촉0인 상태에서5초 동안 기타가 넘어가지 않는 후보를 동일 조건2회 확인했다.** 이때 상완·가슴·오른 허벅지 접촉이 관측됐다. 각 접촉의 실제 지지 힘/모멘트 기여를 분리 측정한 결과는 아니다. 이전 README의 ‘접촉으로 유지’ 표현은 이 관측 범위로 해석한다.

초기 대비 바디 bounding-box 중심이40.207mm, 기타 SO(3) 회전이11.071° 변한 뒤2→5초 추가변화는0.073932mm/0.028843°였다. actor-root 이동53.017mm와 바디 중심 이동은 다르다. 오른 상완 접촉1187/1200, 왼팔·Head 각각0/1200 끝점이었다. 물리 경과5.0초를151frame/30fps로 담아 MP4는5.033333초다. 양의 raw lambda를N 단위 접촉력 또는 지지 비중으로 해석하지 않는다.

기타는 자유 상태이며 직접 외력·부착·런타임 pose 덮어쓰기가 없다. root/하체 고정, 오른팔12 유한 EFFORT, 다른69 POSITION PD다. 기존 기타 모델·질량·학습 네트워크/보상을 보존했다. 초기 정착·큰 오른팔 초기각·손목 한계 접근이 남고, 팔을 움직이며 fret/strike를 수행하는 능력은 이번 시험에 포함하지 않았다.

![초기와5초 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/artifacts_candidate_v2/native11_zero_to_five_comparison_v2.png)

![환경 시작부터5초 전신](/home/ajou/yigyu/3/docs/2026-10-12/video/om_no_strap_upper_arm_v1/candidate_v1/native11_whole_body.mp4)

[초기 관절각](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/search_v9/upper_arm_neck_side/candidate.json:85), [기타 초기 위치](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/search_v9/upper_arm_neck_side/candidate.json:168), [제어 구현](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v16.py:88), [이전 진단·전체 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/README.md:1), [변경 경로·실제 줄 번호 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/CHANGED_FILES.md:1).

다음 검증은 정착 변화와 오른팔의 큰 초기각을 줄이고, 작은 오른팔 움직임에도 이 상태가 유지되는지 확인하는 것이다. 이후 현재 기타 기준 fret·strike와 안정화 제어의 제어권을 합치는 별도 검증이 필요하다.
