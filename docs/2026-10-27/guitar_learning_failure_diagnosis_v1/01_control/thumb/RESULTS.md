# 엄지 제한 범위 후면 접근 진단

기존 `guitar_learning.tool.validation.thumb_contact_probe`를 source 변경 없이 GPU에서 실행했다. 정책 학습이 아니라 엄지5축만 기존 누적 action codec으로 움직이는 검사다. 초기 목표 ±15도·tick당0.5도 요청 제한이며 전체 native 범위의 도달 불가능성을 증명하지 않는다.

- 15초·900제어tick·3600물리끝점, 실제 native 영상450프레임(1280×720/30fps).
- 실행·입력 불변·scene 종료·영상 인코더 검사는 통과했다.
- **접촉→유지→해제→재접촉 프로토콜은 미통과**다. 1초 준비 뒤14초 내내 최초 접촉 후보가 성립하지 않아 approach에 머물렀다.
- 선택된 기하 안내 품질은 전 표본1이고 후면 영역 초과는 수치오차 수준이다. 그럼에도 thumb3 몸체의 순접촉힘은 전 표본0이며 후면 법선 하중도0이었다. 기하 안내와 실제 부하 성립을 구분해야 한다.
- 고정된 제어 표본63은 마지막에 원본 후면 평면 안쪽0.30005mm까지 갔고 영역 초과0, 법선cos0.94957였다. 동일 점의 현재 source neck1/neck2 convex halfspace 검사에서도 각각0.30005mm 안쪽이다. 이는 **원본 기하** 검사이며 PhysX cooked hull의 readback이나 접촉 쌍 인증이 아니다.
- 원래 진단 접근깊이는 최대0.3mm이다. 실제 cooked shape·접촉 속성·접근 깊이를 추가 분리해야 하며, 이 결과만으로 센서/충돌 오류를 확정하지 않는다.

[원보고서](limited_rear_probe/report.json) · [실제 영상](limited_rear_probe/native_thumb_oblique.mp4) · [마지막 프레임](limited_rear_probe/last_frame.png) · [같은 점 재검산](limited_rear_probe/witness_last_check.json) · [source neck halfspace 검사](limited_rear_probe/witness_source_neck_hull_check.json)

## 접근 깊이 분리 검사

후속 실행은 요청 깊이만 최대0.9mm로 늘렸다. native 범위·힘 상한·물리 속성·접촉 판정은 유지했으며, 기존 candidate 허용 깊이1mm 안에서 검사했다. 동일한 첫15초를 비교하고 추가5초는 별도 후속 관측으로 남겼다.

| 관측: 동일 첫15초 | 최대0.3mm 요청 | 최대0.9mm 요청 |
| --- | ---: | ---: |
| 고정한 제어 표본의 마지막 gap | −0.300mm | −0.919mm |
| 기하 안내 품질 평균 | 1.0 | 1.0 |
| 실제 thumb3 순접촉힘 최대 | 0N | 0N |
| 접촉 후보 표본 수 / 3600 | 0 | 0 |

후속20초 전체에서도 접촉힘·후보는0이다. 기하 품질이 최대여도 실제 접촉은 확보되지 않았으므로, 안내 품질만으로 엄지 지지를 달성했다고 보고하면 안 된다. 실제 actor shape 속성의 readback에서 thickness와 rest offset은0이어서, 기본 AssetOptions thickness만으로 이 현상을 설명할 수 없다. source 표면과 실제 cooked 충돌 표면의 차이 등은 미해결이며, 접촉 문턱 완화로 덮지 않았다. 이 제한 범위 검사만으로 전체 엄지 가동범위에서 접촉이 불가능하다고 결론내릴 수도 없다.

[동일 시간 비교 그래프](depth_comparison.png) · [수치·입력 SHA](depth_comparison.json) · [후속 원보고서](deeper_rear_probe/report.json)
