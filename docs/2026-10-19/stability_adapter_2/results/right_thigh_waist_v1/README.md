# 기타 아래쪽 waist를 오른 허벅지에 걸친 초기 배치

이전보다 휴머노이드 오른쪽으로 약9.6cm·앞3.0cm·아래4.9cm 옮기고 앞판을5° 기울였다. 넥의 world 방향은 유지했다. 몸통·양팔 초기각을 다시 맞춰 초기 전체 형상 겹침 검사를 통과했고 실제 Isaac Gym/PhysX로 정지 및 팔꿈치 움직임을 각각5초 확인했다.

오른 허벅지의 실제 접촉점1198/1200step이 정의한 오목한 곡면 영역 안에 있었으며 모두 양의 raw lambda를 보였다. 마지막0.5초도120/120step 유지됐다. 오목한 중앙 한 점을 붙이는 방식이 아니라 양옆 곡면이 허벅지를 받치는 배치다. raw lambda를 접촉력 N으로 해석하지 않는다.

팔꿈치 실제 운동 범위는10.096°, 같은 시점의 정지 조건 대비 추가 기타 변화는 최대0.155mm·0.149°였다. 초기 대비 전체 최대 바디 중심 이동11.725mm·SO3 6.095°,5초 종료11.660mm·5.217°다. 상완과 왼손 손가락 접촉도 남아 있고 후기 Thorax 접촉은0이라 오른쪽 두 블록만의 유지 결과는 아니다. 손가락은 중지2·검지2·새끼3이며 엄지로 잘못 표기하지 않는다.

## 실제 영상

0–2.5초 정지 관찰 후2.5–4.5초 R_Elbow_y 목표±5° 한 주기,4.5–5초 관찰이다. 음악 체크포인트를 연결한 준비 단계가 아니다. strap OFF·root/하체 고정·self collision ON·기타 자유 상태이며 고정/부착/기타 직접 힘/runtime 덮어쓰기를 사용하지 않았다. 학습0회다.

![새 걸침 배치에서 팔꿈치를 움직인 실제 Isaac Gym 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/native_elbow5_v1/media/whole_body.mp4)

## 확인할 파일

- [초기값·제어·실제 비교·제한과 다음 단계](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_THIGH_WAIST_COMPLETION_V1.md:3)
- [선택 후보와81 초기각](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/search_v5/shift95_front30_roll-5/candidate.json:1)
- [실제 초기값](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/native_elbow5_v1/initial_values.json:1)
- [두 완료 조건의 명령·waist 접촉·정지 비교 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/analysis_final_v1/analysis.json:1)
- [첫 자세의4.783초 보호 중단 원자료 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/partial_analysis_v1.json:1)

CPU 후보9개 중7거절/2수락, native3시도 중2회5초 완료/1회4.783초 중단이다. 이전 모델/실험/소비 소스·부분 영상까지 보존한다. source1은human mesh before SHA 누락의 감사 제한이 있고 source2 이후는37개 실제human mesh를 pin했다. source3/helper1은 box 검수 오류로 fitting/native 미실행이다.
