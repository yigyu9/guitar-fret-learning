# 외관 asset 경로 정정·금속 시각 요소 보완 검수

요약 판정: **문제없음 — v2 경로 정정 확인과 v3 source 사전 범위.** 추가 확정 차단 오류는 없습니다. v1 실패·v2 native 완료·v3 시각 추가의 검증 범위를 구분합니다.

## v1 실패와 v2 정정

[실패 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/native_exit_v1.json:1)은 절대 mesh 경로가 asset directory 뒤에 이어 붙은 native loader 오류와 exit139를 기록합니다. 기존 [v1 사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/review_preflight_v1.md:1)는 source만으로 importer 지원을 확정하지 않았으나 이 실제 경로 실패를 사전에 차단하지 못했습니다. v1 소스·asset·attempt·로그·리뷰는 보존합니다.

[builder v2:33](/home/ajou/yigyu/3/stability_adapter_2/build_acoustic_appearance_v2.py:33)과109행의 mesh filename은 자산 디렉터리 기준 상대 경로입니다. v1→v2 diff는 해당 경로 및 새 결과 경로 분리입니다. 실제 생성된 모든 mesh 경로가 상대 경로이고 해당 파일로 해석됨을 직접 확인했습니다. [native v2 완료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/acoustic_guitar_appearance_v1/native_exit_v2.json:1)와 report에서1200물리 step/300제어·property setter1/거절0·캐시 검사 통과 및 collision comparison exact를 확인했습니다. 이는 v1 실패한 native 실행의 성공으로 소급하지 않습니다.

## v3 추가 시각 mesh

[builder v3](/home/ajou/yigyu/3/stability_adapter_2/build_acoustic_appearance_v3.py:134)은 metal 재질·현6개·프렛1..21·튜너 시각 mesh를 추가합니다. 현은 기존 G:string 시작/끝 좌표로 정렬하고 프렛은 해당 body의 원본 box 크기·좌표를 사용합니다. 기존 물리 geom은 rgba 외 동일하며 모든 추가 geom은 contype0/conaffinity0/density0입니다. v2/v3의 asset·manifest 입력·출력 SHA,body frame·원물리 geom 및 상대 경로를 직접 대조했습니다.

소비된 runner v1을 그대로 재사용하므로 native의 shape layout/속성 exact gate,직전 mass/COM/fullI 복원·readback·캐시·construction guard·동일 초기 q_ref5초 조건은 유지됩니다. v3가 실제로 보이는지와 importer가 추가 시각 mesh를 물리에서 분리하는지는 v3 native 결과로 확인해야 합니다. 이번 사전 검수는 v3 native 성공·최종 외관 품질을 인증하지 않습니다.

## Warning

기존 [camera 경로](/home/ajou/yigyu/3/stability_adapter_2/run_acoustic_appearance_trial_v1.py:90)의 실패 handle/None 이미지 처리 Warning은 남습니다. v2 정상 완료가 모든 로딩·카메라 실패 경계의 안전 처리를 증명하지는 않습니다. 사운드홀·브리지는 텍스처,금속 요소는 시각 추가이며 연주·안정화·실물 목재 물성 성공으로 해석하지 않아야 합니다. builder v3의 미사용 `nonlocal_ids` 변수는 기능 차단 사항이 아니며 소비 소스에서 삭제하지 않습니다.

## SHA·보존 범위

- builder v2: `ef3721cb30f83b2133d3ad6fd1a616dd0180403f4452def25c27fce0f96684d7`
- builder v3: `be390f6991b66aa0c10f6b3979019396ecb546c36a0e019a43a7daddaf69de8a`
- v2 MJCF: `a22ceb1f92ecfe962172eb7a592295eaf64c13f5caaeb6de263ea1cc9a83a1c5`
- v3 MJCF: `4df0b3e24335c9f975070a47d69075708ca981a37e367a6b8bc95e90426b84ec`

검수자는 이 새 리뷰만 작성했습니다. 기존 파일 수정·추가 native/물리·추론·학습을 하지 않았습니다. 최종 v3 원자료·렌더·물리 동일성 대조는 별도 최종 리뷰 대상입니다.
