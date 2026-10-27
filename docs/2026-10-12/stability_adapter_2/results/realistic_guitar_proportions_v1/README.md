# 휴머노이드 크기에 맞춘 콘서트형 기타 — 첫 버전 완료

현재 휴머노이드의 중립 source 높이 약172cm와 기존 넥·현 길이를 기준으로 기타를 다시 만들었다. 기존30×34×4cm 상자를 **바디 길이48.8cm·폭37.3cm·두께8.8–10.8cm, 전체100.2cm**의 콘서트형 비율로 바꿨다. 허리가 있는 상·하부 바디와 머리 연장부를 만들었으며, 기존 넥·프렛·현 좌표와 모든 body 이름·순서·원점은 보존했다. 별도 자산이고 기존 공용 모델과 학습 환경 기본값은 변경하지 않았다.

## 크기의 근거

휴머노이드 중립 source 형상의 높이는1.7205m다. 원본 zero-range 관절은 읽기 전용 측정 사본에서만 제한을 풀어 중립 형상을 계산했다. 실제 Isaac Gym humanoid나 하체 자산은 바꾸지 않았다. 이는 실측 사람 키 또는 앉은 native 높이가 아니다. 어깨 body 원점 간 거리는31.60cm이며 피부 외곽의 어깨너비와 구분한다.

성인 크기 휴머노이드와 기존 넥·현 길이에 맞는 첫 가정으로 콘서트형 어쿠스틱 기타를 선택했다. 참고 모델은 [Yamaha FS800 공식 사양](https://shop.sg.yamaha.com/fs800.html)이다. 바디 길이497mm·폭380mm·깊이90–110mm, 유효 스케일634mm·전체길이1021mm를 참고했다. 여섯 기존 현 marker 양 끝 사이 평균 길이에 맞춰 치수를0.981682배로 환산했다. marker 길이는 실제 nut–saddle 스케일의 정밀 실측이 아니므로 이 대응은 비율 근사다. 윤곽도 직접 설계한 연구용 근사이며 제품 스캔이나 정밀 복제는 아니다.

| 항목 | 기존 | 새 모델 |
|---|---:|---:|
| 바디 길이: 넥 방향 | 34.0cm | 48.7896cm |
| 바디 최대 폭: 넥에 직각 | 30.0cm | 37.3039cm |
| 바디 두께 | 4.0cm | 8.8351–10.7985cm |
| 전체 길이 | 약82.53cm | 100.2298cm |
| 휴머노이드 중립 높이 | 172.05cm | 동일 |
| 넥·프렛·현·proxy body 좌표 | 원본 | 동일 |

## 시각·충돌 형상과 물성

상·하부 bout 각각을 폐합된 convex mesh로 만들고 두 부분의 합으로 잘록한 허리를 유지했다. 한 개의 convex hull로 바디 전체를 처리해 허리가 채워지는 것을 피했다. 시각과 충돌은 동일한 두 mesh를 사용한다. 기존 넥 mesh를 유지하고 전체 길이에 맞는 headstock 연장 geometry만 추가했다. 단순 강체 접촉 모델이며 내부 목재·브레이싱·soundhole의 실제 물리 구조를 재현한 모델은 아니다.

원본 총질량4.6487157kg과 각 body 질량을 유지했다. 새로운 importer COM과 관성에 질량비를 적용한 값을 construction 단계에서 한 번 제출하고 전체 readback을 비교했다. 전체질량, strap 양 끝 route_COM, 관측 COM 캐시도 실제 적용값과 일치했다. 실행 중 body-property setter는 새 guard가 차단하며 초기 setter는 원본0회/새 모델1회, 이후 거절·금지 호출0이다. CPU guard4검사를 통과했다. 실물 어쿠스틱의 중량이나 중공 목재 질량 분포를 측정한 결과는 아니다.

새 G:body의 질량은 원본과 같은4.0800004kg이며, 적용 COM은 기존 body 원점 기준 약[0,−16.30,−29.41]mm다. 관성의 대각 성분은[0.07208,0.03421,0.09958]kg·m²이며 yz 교차 성분도 보존·검증했다. 물성 변경 자체를 시각 크기 변경과 혼동하지 않는다.

## 초기 배치와 실제5초 확인

원본은 직전9° 몸통 굽힘·왼손지지 조건을 같은 PD 목표로5초 기록했다. 새 모델은 커진 바디의 시작 관통을 피하도록 기타를 기존보다 Pelvis앞3.5cm·world위8cm 이동하고 양팔24관절을 기존9° 자세 기준±0.6rad/모델한계 안에서 초기 IK로 조정했다. 몸통·머리·손가락·고정root/하체와 PD·solver는 유지했다. 새 asset을 직접 읽는 source 검사와 실제 native 초기 FK가 통과했다.

스트랩은 원본 길이1.10184697m·법칙을 유지했고, 버튼 위치는 새 바디 측면/끝면에 맞췄다. 따라서 같은 route가 아니다. 새 초기 계산 slack은 약90.97mm다. 영상에는 실제 route를 표시한다. 기타는 자유 물리 상태이며 매프레임 pose 쓰기·손부착·인위적 추가힘은 사용하지 않는다. 초기q_ref PD 목표만5초 유지한다. 음악·체크포인트·안정화정책·학습·초기노이즈는 실행하지 않았다.

| 진단 | 원본 | 새 모델 |
|---|---:|---:|
| 초기→5초 actor-root 이동 | 10.8434cm | 13.1920cm |
| 초기→5초 SO(3) 회전 | 18.9736° | 10.0131° |
| 초기→5초 바디 bounding-envelope 중심 이동 | 4.1077cm | 10.2077cm |
| 2→5초 actor-root 이동 | 0.047841mm | 0.017267mm |
| 2→5초 SO(3) 회전 | 0.008496° | 0.003439° |

두 시험 모두5초/1200physics/300controls를 마쳤고, 전신·손 영상은 각각151frame/30fps·5.033333초다. t0 프레임을 포함하므로 물리5초와 MP4 길이는 다르다. 25개 실행·입력·좌표·물성·영상 검사가 통과했다.

새 모델에서도 초기 이동은 남았고, 접촉은 주로 왼손 손가락과 오른허벅지(R_Hip290/300)에 관측됐다. 오른상완·전완·Chest 접촉은0/300이었다. 따라서 겨드랑이 지지나 왼손 없는 유지 성공은 아니다. 형상뿐 아니라 초기배치·팔 초기각·strap 버튼/route도 바뀌었으므로 회전 감소를 형상만의 인과효과로 주장하지 않는다. 접촉은60Hz query이며 rawλ를 N 단위 힘으로 환산하지 않는다. 이전 체크포인트의 음악 성능은 아직 검증하지 않았다.

![새 기타 초기 실제 Isaac Gym 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/native_realistic_v2/media/frames/whole_body/00000.png)

![새 기타0–5초 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/native_realistic_v2/media/whole_body.mp4)

## 바디 중심의 정의와 보존한 정정 기록

기존 G:body 원점[0,−0.4,−0.0217]m은 ABI 호환용 reference로 유지했다. 새 바디의 실제 source bounding-envelope 중심은[0,−0.4,−0.05569252]m이고, native G:body COM은 약[0,−0.41630393,−0.05111216]m이다. 바디 COM과 전체 기타의 합성 COM도 구분해야 한다.

소비된 manifest의 `body_envelope_center_G_m`은 평균두께를 쓴 중간깊이 reference[0,−0.4,−0.05078411]m여서 이름이 부정확했다. 자산·manifest·첫 분석은 보존하고 별도 중심 audit로 실제 mesh bounds를 계산했다. **권위 있는 중심 분석은 body_center_audit_v2.json과 verification_v3.json**이다. audit에 상속된 설명 문자열은 verification_v2라고 쓰지만, 해당 준비 분석은 입력부재로 실패했고 결과파일이 없다. 여기서 v3를 정확한 분석 경로로 정정한다. 첫 audit의1e-9m 검사는 OBJ 소수점 내보내기 오차1.73e-9m로 실패했으며 새 audit는1e-7m 허용으로 검증했다. 이 정정에서 물리 재실행은0이다.

v1 runner의 물성 readback/guard 부족은 native 전에 독립검수에서 보완했다. 미실행v1과 실패한 준비 후처리 source를 모두 보존했다. 실제 native 두 시험은 v2 runner이며 정상 종료했다. 로그의 기존 일부 humanoid visual-geom 경고와 새 기타의 실제 렌더·완료 결과를 구분한다.

- [새 모델 MJCF](/home/ajou/yigyu/3/stability_adapter_2/assets/realistic_guitar_v1/guitar_asset.xml:1)
- [source 치수·좌표 ABI 검증](/home/ajou/yigyu/3/stability_adapter_2/assets/realistic_guitar_v1/manifest.json:1)
- [실제25검사·물성·접촉·영상 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/verification_v3.json:1)
- [실제 바디 envelope 중심·COM 정의](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/body_center_audit_v2.json:1)
- [실제 초기값·PD·mass·strap](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/native_realistic_v2/initial_values.json:1)
- [v2 물성 보완 계획](/home/ajou/yigyu/3/stability_adapter_2/REALISTIC_GUITAR_PROPORTIONS_PLAN_V2.md:1)
