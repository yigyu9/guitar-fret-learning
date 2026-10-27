# 허리를 더 편 자세: 추가4°·8° 실제 비교

이전4° 완화 자세에서 몸통을 추가로 펴고 팔을 다시 맞췄다. **추가8° 자세**를 이번 시각적 검토 후보로 선택한다. 초기 Torso/Spine/Chest 전방 기울기 proxy는32.729/34.403/61.412°에서29.529/28.403/53.412°로 줄었고,5초Chest는56.422°였다. 기타 초기 배치는 동일하다.

| 새 조건 | 실제 경과 | 최대 기타BB 이동 / SO3 | 2~5초 변화 |
|---|---|---|---|
| 추가4° |5초 완료|13.040mm / 7.353°|1.893mm / .894°|
| 선택추가8° |5초 완료|12.882mm / 7.543°|.382mm / .144°|

이전 현재 자세의 최대14.545mm/8.013°보다 두 후보 모두 줄었다. 추가8°는더펴진자세와후기변화감소로선택했으며추가4°보다최대회전은조금크다. 원waist기준보다모든안정성지표가좋아진것은아니므로학습기본값은교체하지않는다. local-Z기울기proxy를임상적척추각이나관절scalar합으로해석하지않는다.

두조건모두waist접촉1198/1200·후기양의rawlambda120/120,근위상완후기120/120,Thorax후기0/120,오른전완/손기타접촉0이다. 왼손손가락기여는남는다. 기타자유/strapOFF/selfcollisionON·root하체고정·81목표·기존controller를유지했으며기타힘/부착/pose덮어쓰기없음. Source2수락/native2완료,총2400physics/600control,새팔꿈치파동·checkpoint·학습0이다.

[실제 초기 비교와0·2·5초 이미지](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_straighten_v1/artifacts_v1/README.md:1) · [전신/손 영상4개](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/waist_straighten_v1/INDEX.md:1) · [구현·검증·한계](/home/ajou/yigyu/3/stability_adapter_2/WAIST_STRAIGHTEN_COMPLETION_V1.md:1) · [변경 파일](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_straighten_v1/CHANGED_FILES_v1.md:1)
