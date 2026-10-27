# 기타 모델·초기 자세 자료 모음

사용자가 지정한 `docs/2026-10-19/`에 현재 기타 형상, 스트랩 없는 초기 자세, 이미지와 영상을 모은다. 이 날짜는 자료 정리 경로다. 기존10-12 실험의 실행일·원자료 경로를 바꾸거나 새로 실행한 결과로 표시하지 않는다. 계획·구현·실제 자산은 `/home/ajou/yigyu/3/stability_adapter_2/`에 유지한다.

## 현재 기타

Grellier OM 도면을 바탕으로 바디 외곽과 외부 두께를 근사한 회색 모델이다. 바디 길이491.957mm·최대 폭380.632mm·국소 두께 약85~107.198mm이며 기존 넥과 fret/strike 물리 영역을 유지한다. 6현 선 표시는 영상 확인용으로 물리적 상호작용이 없다. 목재 내부·음향·질감이나 사진 속 제품의 정확한 재현은 포함하지 않는다. 현재총질량4.648716kg은 이전 모델값을 유지한 것으로 실제 중공 기타의 질량 재현값이 아니다.

## 현재 초기 자세

스트랩을 끄고 왼팔·왼손을 떼어 둔 상태에서 기타가5초 동안 넘어가지 않는 후보를 동일 초기 조건2회 확인했다. 이때 오른쪽 상완(어깨 아래)·가슴·오른 허벅지 접촉이 관측됐다. 각 접촉의 지지 힘/모멘트 기여를 분리 측정한 것은 아니다. root·하체 고정, 기타 자유, 오른팔12 EFFORT 제어와 다른69 POSITION PD를 사용한다. 기타에 직접 외력·부착·런타임 pose 덮어쓰기를 하지 않는다.

| 측정 | 값 |
|---|---:|
| 초기 대비 바디 bounding-box 중심 이동 | 40.207mm |
| 초기 대비 actor-root 이동 | 53.017mm |
| 초기 대비 전체 SO(3) 회전 | 11.071° |
| 2→5초 바디 중심 추가 이동 / 추가 회전 | 0.073932mm /0.028843° |
| 상완 / 왼팔·왼손 / Head 접촉 끝점 | 1187 /0 /0 (각1200개 중) |
| 물리 경과 / 녹화 길이 | 5.0초 /5.033333초 |

초기 정착 변화와 오른팔의 큰 초기각·손목 한계 접근이 남는다. 연주 중 안정성, 접촉력 분포 및 cooked 관통 검증은 이번 정리 결과에 포함하지 않는다. raw lambda와 접촉 관측 횟수를N 단위 힘이나 지지 비중으로 해석하지 않는다.

## 자료 구성

- `guitar/`: 모델 형상·치수·두께·출처 설명
- `posture/`: 초기값·제어 방식·5초 결과·미검증 사항
- `images/`: 기타 모델 확인 이미지, 초기·측면 자세,0→5초 비교
- `video/candidate/`: 최종 후보와 동일 조건 반복의 전신·손 영상
- `video/diagnostics/`: 이전 실패 시험의 전신·손 영상
- `data/`: 원본 그대로 복사한 초기값·모델 정보·검증 자료

복사한JSON 내부의 기존 절대경로는 원실험 추적용으로 그대로 둔다. 이 복사본을 새로운 실행 설정으로 간주하지 않는다. 원본과 사본의 해시는 정리 provenance에 기록하며, 이번 작업의 새 물리 실행·학습·모델 변경은0회다.

## 바로 보기 — 검수 보완본 v2

[기타 형상·치수·출처와 참고 이미지](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/guitar/README_v2.md:1) · [초기 자세·조건·측정 결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/posture/README_v2.md:1) · [전신·손 영상22개 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/INDEX_v2.md:1) · [원자료 복사본 안내](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/README.md:1)

![현재 후보의 초기와5초 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/images/native11_zero_to_five_comparison_v2.png)

![현재 후보 환경 시작부터5초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/candidate/native11_whole_body.mp4)

초기 정리본 v1은 영상 색인의 일부 원본–사본 연결과 접촉 주기 설명에 오류가 있어 이력을 보존했다. 실제 영상 사본은 원본과 같으며, 현재 안내는 링크가 정정된 v2를 사용한다. [정정 영상 manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/manifest_v2.json:1)와 [보완 provenance](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/provenance_v2.json:1)에서 원본과 사본의 대응을 확인할 수 있다.


## 최신 오른팔 자세 수정 결과

[참고 사진에 따른 오른팔 수정과 실제5초 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/README.md:1). 이전 교차 팔은 연주 자세로 채택하지 않는다. 새 팔 모양은 개선됐지만 기타 유지에는 실패했고, 작은 위쪽 보정은 머리접촉으로 거절했다. 이전 이미지·영상과 실패 기록도 모두 보존한다.


## 최신 몸통 기울임·겨드랑이 접근

[왼쪽4°·초기배치조합·상완누름의실제5초비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/README.md:1). source근접에도상완접촉0/1200이며세조건모두기타유지에실패했다. [전체·손영상6개](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/INDEX_V2.md:1). 이전자료는보존하고반대방향과의명확화는대기중이다.


## 최신 바디 쪽 몸통 기울임: 방향 확정 및 실제 비교

사용자 확인 방향은 정면 screen-left=player-right=기타 바디 쪽이다. 추가Chest4°/Torso1°/Spine2.5°와 자연 오른팔 조정·기타 초기 이동을 구성하고 같은 초기값을 실제5초2조건 비교했다. 스트랩OFF·왼손지지없음·root/lower고정·기타자유를 유지했다. 전완 제어 / 상완 추가에서 바디 중심48.051/47.501mm, 전체회전52.174/47.662°, 넥고도−15.921/−10.019°로 초기회전 유지에 실패했다. 상완접촉968/256 of1200이며 머리/왼팔0이다.2초뒤정착을성공으로해석하지않는다. 이전넥쪽기울임 기록은반대방향진단으로보존한다.

[초기 배치·그림·실제 영상·결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/README.md:1), [현재 계획](/home/ajou/yigyu/3/stability_adapter_2/BODY_SIDE_LEAN_AXILLA_PLAN_V6.md:1), [초기81각·기타p/q](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/search_v5/right4_close_support/candidate.json:1). 다음은 누름 증가보다 허벅지·상완·전완 지지점 배치 조정이다.
