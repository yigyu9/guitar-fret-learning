# 진행 기록

## Preview v1 — 실패 보존

- 승인된 renderer: `stability_adapter_2/initial_pose_video60_v1/replay_v5.py`, 실행 전후 SHA-256 `55b40d257a43251099bf3096b99e9501aa33d6cd46cdee30aeae9227f5a13740`.
- 실행은 승인된 `--preview` 명령과 rl38 환경으로 한 번 수행했다. 전체 영상 렌더는 실행하지 않았다.
- 로그: `/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/phase/preview_v1.log`.
- 실패: 첫 측정 상태 복원 검사에서 `restored measured-state mismatch: 2.59622`. 따라서 미리보기 이미지와 `replay_report.json`은 생성되지 않았다. 오류를 수정하거나 재실행하지 않았으며 부분 산출물을 그대로 보존했다.
- 보존된 부분 출력: `preview_v1/attempt.json`, `inputs_before.json`, `original_scene_input_parity.json`, `scene_parity.json`.
- 입력 전 지문 목록은 절대 경로 1,326개이며, 사후 재계산 결과 누락 0개·변경 0개였다. 두 실행의 원시 `states240.json` SHA-256은 각각 `486d37c238606979b9d3abddb52029d8836502bf310a6dbab052637eeb784ae0` (free_strike_v14), `5e9c9e47b9a49f840cf62522f92396780939592691d3ab8289b5a0a1e453f0a9` (regrasp_v14)로 입력 지문과 일치한다.
- 장면 parity는 두 원본 실행 모두에서 scene class, joint/body 순서, 자산 바이트, 의자 초기 배치가 일치한다고 기록했다. 렌더링 전에 상태 복원 검증이 실패했으므로 실제 프레임 결과는 없다.
- 요청 물리 스텝 수는 0이고 scene 설정은 constructor 전에 `simulate`/`fetch_results`를 비활성화했다고 기록한다. 실패로 인해 최종 `replay_report.json`의 실제 스텝/차단 호출 카운트는 남지 않았다. 로그의 PhysX 설정은 Physics Device CPU, GPU Pipeline disabled다.

다음 진행은 root의 새 renderer 버전/SHA 및 재시도 승인 대기다. 이 실패 출력과 소비 입력은 수정하지 않는다.

## Preview v2 — 영상 전용 FK 기준 초과

- 승인된 renderer: `stability_adapter_2/initial_pose_video60_v1/replay_v6.py`, 실행 전후 SHA-256 `17f6bcf5008ef1ed1334acadea31baa268ea9a8b04a5ef150dac58df353b0d09`.
- 적용 기준은 [BRIEF_v2.md](/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/BRIEF_v2.md)다. human DOF를 복원해 native FK로 그리며, 저장된 모든 human body pose를 그대로 재현한다고 주장하지 않는다. 화면용 최대 FK 오차 허용치는 1 mm 및 0.1도다.
- 승인된 `--preview` 명령을 rl38 환경에서 한 번 수행했다. 전체 영상 렌더는 실행하지 않았다. 로그: `/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/phase/preview_v2.log`.
- 첫 렌더 구간에서 FK 제한 초과로 중단됐다: 최대 위치오차 `0.0020366665972007553 m` (`LH:index_top`), 최대 회전오차 `2.3596292811254433°` (`LH:index1`), 비교 body 66개. 허용치인 1 mm/0.1°를 모두 초과한다. 이 값은 오류 메시지의 해당 검사 프레임 측정치다.
- 부분 출력은 `preview_v2/`에 보존했다. 이미지 한 장 `preview_native_free_strike_v14_04080.png` 및 `current_native.png`, `attempt.json`, `inputs_before.json`, `original_scene_input_parity.json`, `scene_parity.json`이 있다. 완성된 3장 미리보기와 `replay_report.json`은 생성되지 않았다.
- 입력 지문은 절대 경로 1,330개이며 사후 SHA 재계산 결과 누락 0개·변경 0개다. 두 원시 `states240.json`의 SHA도 preview_v1과 동일하다. 장면 parity 자료는 두 원본 실행과의 scene class, joint/body 순서, 자산 바이트, 의자 초기 배치 일치를 기록한다.
- `attempt.json`의 요청 물리 스텝은 0이고 `simulate`/`fetch_results` 차단 장치가 constructor 전에 설치됐다. 기준 초과 예외로 완료 보고서의 실제 step/차단 호출 수는 생성되지 않았다. 로그상 PhysX Physics Device는 CPU, GPU Pipeline은 disabled다.

이 출력도 실패 상태 그대로 보존한다. 새 코드 버전/SHA와 root의 별도 실행 승인이 있기 전까지 재시도하지 않는다.

## Preview v3 — 성공, root 시각 확인 대기

- 실행 전 brief, 승인 JSON, 독립 사전 검수 및 소스 SHA를 확인했다. 사용한 renderer는 `replay_v8.py` SHA-256 `d2509d9b5de8c44b371e06366487909fdd0e3b7861c16bdb816c31ea89e05eee`, `static_visual_v7.py` SHA-256 `2a2855f6c14bad20db8ed50ba5506b0d4c00fd6298dddfc0d3d98eed981029bb`다.
- 승인된 preview 명령을 실행했다. 로그: `/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/phase/preview_v3.log`.
- 생성된 세 장: `/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/preview_v3/preview_native_free_strike_v14_04080.png`, `/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/preview_v3/preview_native_free_strike_v14_06960.png`, `/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/preview_v3/preview_native_regrasp_v14_10560.png`.
- Preview 보고서: 60fps, 240Hz stride 4, 새 물리 스텝 0, clock 0, 원입력 SHA 불변, 106 body 표본별 변환 재확인. 세 표본은 각각 17초(physics_step 4080), 29초(6960), 44초(10560)다. 위치 변환 오차는 모두 0m이며 최대 회전 오차는 각각 `5.087710622580481e-16`, `4.002966042486721e-16`, `4.440902686916832e-16` rad다.
- 독립 재계산으로 119개 pinned input SHA를 확인했다: 누락 0개·변경 0개. 당시 preview는 root의 시각 검토 및 full render 별도 승인 전 상태였다.

## Full render v1 — 완료

- root의 시각 확인과 `full_render_approval_v1.json` 승인 후 preview와 같은 renderer/source SHA로 `full_v1`을 한 번 생성했다. 실행 로그는 `phase/full_v1.log`다.
- MP4: `/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/full_v1/front_full_body_60fps.mp4`; SHA-256 `1d9a101eee721b8238dded91a933be045612505d157b68b5a23deee03e07af55`.
- ffprobe: 1280×720, 60/1 fps, 1,980 frames, 33.000초. 전체 ffmpeg decode 종료 코드 0. 보고서에는 기록 표본 1,920개(시험1 1,380개, 시험2 540개), 전환 카드 60프레임, 새 물리 스텝 0, clock 0이 기록됐다.
- 1,920개 기록 프레임 모두 106 body 변환 readback을 통과했다. 프레임 전체 최대 위치오차 0m, 최대 회전오차 `6.753779996930239e-16 rad`. 119개 입력 지문 사후 확인: 누락 0개·변경 0개.
- 최종 영상 embed와 한국어 설명/범위를 담은 문서: `/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/README.md`.
