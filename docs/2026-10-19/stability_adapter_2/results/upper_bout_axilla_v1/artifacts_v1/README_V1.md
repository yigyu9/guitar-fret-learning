# Upper-bout axilla · native1–3 결과

세 조건 모두 실제 native 5초 완료이며 source v5 geometry 후보를 유지했습니다. root/lower body 고정, strap OFF, 기타 자유, left grip 없음, 기타에 직접 힘 없음입니다. Native1/2는 source right-bout geometry 조건에서 기존 forearm control과 upper-arm motor-point reference를 사용했고, native3은 upper-point effort를 gentle press로 변경했습니다. 여러 controller·기하·몸통 조건이 함께 달라졌으므로 차이를 한 설정의 단독 효과로 귀속하지 않습니다. Full native initial states는 native2/native3 exact match이고 세 조건 guitar initial pose는 같았습니다.

![세 실제 native의 0·2·5초 전신 캡처](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/artifacts_v1/native_timeline_0_2_5s.png)

![Weak-case native3에서 R_Shoulder motor-reference와 t=5 실제 contact feature의 주석 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/artifacts_v1/weakcase_motor_reference_vs_contact_v1.png)

| 관측값 | native1 · Chest4° / upper35 | native2 · Chest6° / upper35 | native3 · Chest6° / gentle press |
|---|---:|---:|---:|
| 최종 body-bbox 중심 이동 | 303.680 mm | 234.261 mm | 59.465 mm |
| 초기 대비 전체 SO(3) 회전 | 113.813° | 82.276° | 53.935° |
| 최종 neck G+Y elevation | 63.971° | 56.665° | −13.709° |
| R_Shoulder contact endpoints | 135/1200 | 180/1200 | 1075/1200 |
| Head contact endpoints | 796/1200 | 728/1200 | 0/1200 |
| 왼팔·손 contact endpoints | 0/1200 | 0/1200 | 0/1200 |

모든 contact endpoint 수는 240 Hz after-physics query 1200개 기준입니다. Contact/raw lambda는 측정된 힘이 아닙니다. Native3의 2→5초 body 중심 변화는 0.132568 mm, 전체 회전 변화는 0.066829°로 작지만 이미 자세가 크게 바뀐 뒤 정착한 것이므로 초기 자세 유지 성공을 뜻하지 않습니다.

![Weak-case 표시의 뜻](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/artifacts_v1/weakcase_motor_reference_vs_contact_v1.png)

Weak-case 표시의 노란 점은 R_Shoulder body state와 axilla motor-reference local 좌표를 합성한 shoulder-side 35% 사람 관절 motor-reference 위치입니다. 파란 점은 native3 step1200에서 positive raw lambda가 기록된 실제 R_Shoulder–guitar contact feature입니다. 둘은 t=5에서 33.76 mm 떨어져 있지만 이 수치는 motor-reference와 contact feature 사이의 거리일 뿐 shoulder capsule gap/상완 지지 여부를 나타내지 않습니다. 확대 crop과 화살표는 표시용 사후 주석이며 depth-tested가 아니고 physics를 바꾸지 않습니다. Contact-region 검사에서는 shoulder-side 35%와 upper-bulge 규정 영역의 접촉이 세 조건 모두 0/1200으로 분류됐습니다. 접촉 feature가 있다고 해서 지정된 지지점이라 단정하지 않습니다.

이전 body-side/native2 upper-press baseline도 upper-arm any-contact 256/1200이었지만 source-qualified proximal contact는 0/1200이었습니다. 총 upper-arm contact 수만으로 지정한 겨드랑이 지지를 확인할 수 없습니다.

영상은 151프레임·30fps, encoded duration 5.033333초이며 physics 구간은 5.0초입니다. [영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upper_bout_axilla_v1/INDEX_V1.md) · [source/copy SHA·ffprobe](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upper_bout_axilla_v1/manifest_v1.json)

- [결과 summary](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/result_summary_v2.json)
- [contact-region record](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/contact_region_v2.json)
- [verification native1](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/analysis_v1/verification.json) · [native2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/analysis_v2/verification.json) · [native3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/analysis_v3/verification.json)
