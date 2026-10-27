# 현재 초기 자세의 스트랩 없는 실제5초 영상

사용자 요청에 따라 최근 보여준 initial_middle3_alignment_v1의 초기52.09° 자세에서 스트랩을 물리적으로 제거한 비교 영상을 만든다. 주황 경로 표시만 숨기는 재인코딩이 아니다. 기존 현재자세·손목명령·PD·기타 초기p/q·root/하체고정·selfcollision·최종66권한은 유지하고 외부 strap cable-force 적용을 하지 않는다. 중력·실제 접촉·관절 PD는 유지한다. 후속 손5관절 source 호환 초기배치 계획은 이번 비교와 별도로 보존한다.

1. 새 runtime adapter에서 CameraEnvironment의 physics integration만 simulate/fetch로 실행한다. 하체live DOF가0인지 검사하고 모든 explicit rigid-body force API 호출을 금지하는 guard를 둔다. Strap tension은0으로 기록한다. 원본환경/공용자산/기존runner는 수정하지 않는다.
2. 기존의 검증된 초기화·fresh14/1188·5초 명령/기록 루프를 재사용하되 recorder는 원native 카메라만 사용한다. 동작이 없는 천mesh를 지우는 편집은 하지 않는다(기존 strap은 routed force 모델이다). Runtime의 환경/recorder/metadata 교체는 새소스와 mode audit에 명시하고 재사용runner의旧scope를 새조건의 증거로 사용하지 않는다.
3. 실제 초기전체state/PD/81×1200 명령이 strap-on 기준과 같은지, 전체trace 장력0/force API 호출0·root하체고정/연속5초/두151frame30fps영상인지 대조한다. 기타가 떨어지거나 자세가 무너지는 결과도 그대로 기록한다. 오류/중단은partial 영상과 경과를 남긴다.
4. Luna가 확정된 측정치로 초기/종료 이미지와 두영상을 설명하는 한국어 결과를 정리한다. 영상모음에 원본 그대로 추가하고 독립검수·보존 기록을 남긴다.

- [ ] 새 adapter/기록wrapper 구현·코드검수
- [ ] 스트랩 힘없는 actual5초·초기값/두영상
- [ ] 기준동일성/0strap force/실제기타 변화 분석·영상모음
- [ ] 이미지·영상설명/독립검수·보존 기록

메인계획·구현은 /home/ajou/yigyu/3/stability_adapter_2, 결과는 /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1 에저장한다. 이번사용자요청의별도조건이며기존fixed-LA 비교기준을덮어쓰지않는다. 기타고정·손부착·지속pose덮어쓰기·기타를끌어당기는힘은사용하지않는다. 이단위에actor/학습/새자세탐색은추가하지않는다.
