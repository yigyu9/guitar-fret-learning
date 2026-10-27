# 넥 축 회전 source5 사전 검수

판정: **문제없음 — CPU 탐색 차단 없음.** Critical 0건, Warning 2건, Suggestion 0건. 후보 수락·실제 native 유지 결과는 미검증이다.

[source5:51](/home/ajou/yigyu/3/stability_adapter_2/search_right_thigh_waist_v5.py:51)의 `gr=gr0*Ry(roll)`은 기존 G local Y 축 주위 회전이다. −5/−10°에서 world 넥축 `gr*[0,1,0]` 보존 오차≤2.54e−16을 순수 산술로 확인했다. 양손 목표 위치 `gp+gr*gr0^-1*(oldp−gp0)`와 목표 방향 `gr*gr0^-1*oldR`은 기존 G-relative 관계를 보존한다. 두 새 minHip brent 구간은 현재 고정 기준 입력에서 부호 전환을 통과한다.

새 quaternion을 gr로 저장하고 전체 predicted G39 상태·genuine human FK를 갱신한다. body/right/left/head 확대 범위는 native 한계와 교차하며 Elbow_y ±5° 여유·frozen42·Head world 방향·왼 wrist5mm/1°·6caps≥0.05mm/전체 LP·waist flank/forearm/자연 팔 gate를 유지한다. Thorax 최종 간격<1mm는 강화됐고 목표0.3mm 가중치15000/축점500 변경은 명시되어 있다. human37 mesh/config/원GXML/실패 전 source4 numeric seed pin 및 새 search_v5 출력이 유지된다. AST 통과.

## Warning

- [PLAN_V5:36](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_THIGH_WAIST_PLAN_V5.md:36): 새 자세는 기타 회전·위치·초기각 범위·fit 가중치를 함께 바꾼다. Thorax 접근이나 유지 변화의 원인을 한 설정으로 분리하지 않는다. 초기 source gap·넥축 보존은 cooked 접촉/지지·회전량 유지·범용 팔 운동의 인증이 아니다. 직전 시험은 위치20cm guard에 따른4.783333초 중단으로 분리한다.
- [source5:71](/home/ajou/yigyu/3/stability_adapter_2/search_right_thigh_waist_v5.py:71): 양손 변환식은 목표의 규약이다. 오른 RH:palm 위치/방향은 soft fit이며 최종 exact 보존 gate가 아니다. 왼 wrist 허용오차와 오른 실제 초기 pose를 별도로 기록하고 모든 손목 world pose가 exact라고 확대하지 않는다. 확대된+15mm flank와 좁은+5mm core도 구분한다.

검수 SHA-256: source5 `cca82f777b9a9eebb6fe2cc681de9c9c280493079f1fd9fa30710cb7ccd64f2d`, PLAN_V5 `14c7a5beb80d8562f8647588bc6d47aa0e87e3d361a7511ca7881a89a59b3bb8`.

읽기 전용 코드·계획·기존 기준 형상의 순수 산술 검수다. 새 fitting/native/학습·다른 소스/원자료/기존 리뷰 수정은 없다.
