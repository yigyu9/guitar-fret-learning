# 저장 자세·영상·임시 저장 정리 독립 검수

검수일: 2026-10-22. 요약 판정: **문제없음(PASS)**. 산출물과 근거의 대응을 확인했으며 손가락 협응·자연스러운 연주·압력·음향의 개선을 인증하지 않는다.

## 저장 자세 분석

`posture_analysis/analysis.json`과 `report.md`를 원래 5개 평가의 사전 지정 env0..7, 총 40개 실제 NPZ와 대조했다. NumPy/SciPy만으로 전체 부모-자식 quaternion의 상대회전 및 source −y 방향의 yz 투영을 계산해 MCP/PIP/DIP를 재구성했다. t0를 제외한 각 1969개 60Hz 끝점, 모델당 15,752개 끝점에서 유효 분모, 악보 현재음/준비음/없음, 0.25초 idle fade, soft coordination/standby 품질, native q-target RMS를 독립 대조했다. 최대 수치 차이는 **5.684341886080802e−14**, 분석의 **668개 입력 SHA**가 현재 파일과 일치했다. 두 PNG의 SHA와 실제 이미지 파일 형식도 확인했다.

| 모델 | 검지 PIP 평균° | 중지 | 약지 | 소지 |
| --- | ---: | ---: | ---: | ---: |
| 0 | 51.823024 | 38.352979 | 89.329767 | 22.644543 |
| 500 | 84.796740 | 79.522738 | 89.988388 | 57.754865 |
| 1000 | 84.036900 | 78.159273 | 89.996001 | 82.648504 |
| 1500 | 6.566092 | 8.450585 | 89.995711 | 80.802800 |
| 2000 | 14.796233 | 1.175203 | 7.703729 | 85.686873 |

모든 캡처는 안전 완주였고 실패군의 분모는 0으로 `자료 없음`이다. 초기와의 같은 안전 ID 비교도 모두 env0..7에 해당하며 다른 ID로 대체하지 않았다. 이 표본은 전체 1024환경의 실패 분포를 대표하지 않는다. 최신2000의 DIP−PIP>20° 비율은 검지 약83.6%, 약지 약91.3%로 보고서와 일치하며 끝관절 편중 해소를 주장할 수 없다. 실제 전체 MCP와 native q1_x는 정의가 다르므로 차이를 제어 추종오차로 해석하지 않았다. 끝점의 raw helper 품질은 실제 240Hz 누적 보상이 아니며, 역할은 악보 할당이지 접촉 증거가 아니다. 속도·jerk·압력·음향은 이 분석으로 검증하지 않았다.

## 두 실제 영상

`best_fullbody_video`와 `best_hand_video`의 report/presentation/pose_audit/inputs_before/media를 교차 확인했다. 각 **609개 입력 SHA**, 선택된 실제 모델 SHA, segmented training chain, 완료 보고서가 일치했다. 두 GDB 로그는 각각 process1806931/1808067의 정상 종료 및 completed 결과를 기록한다. 새 렌더링이나 물리·정책 실행은 하지 않았다.

- 두 영상 모두 **1280×720, 60/1fps, 1969프레임, 32.816667초**이다. 독립 CPU `ffprobe -count_frames` 결과가 보고서와 정확히 같았다. root의 전체 ffmpeg decode 성공 기록과 두 0byte 오류 로그도 확인했다.
- 원본 캡처는 t0 포함 1970프레임이며 영상은 source frame1..1969를 사용한다. 모든 1969개 pose audit에서 source 프레임/실제 clock/240과 정책 시각, 4배 물리 스텝 대응이 일치했다. body106/joint105이며 최대 위치 오차0m, 회전 오차 **6.379255420885912e−16rad**, 재생용 물리 시각0, 새 적분0으로 기록됐다. 모든 프레임의 projection 값도 기록된 x≤.9/y≤.75 범위 안에 있다. 이는 저장된 audit의 검산이며 GL readback을 새로 수행한 것은 아니다.
- 전신 preview0001/1969와 손 근접 preview0985를 직접 확인했다. 전신 인체·기타가 화면 안에 있고, 근접 손·넥과 한글 시각/달성 카운터를 읽을 수 있었다. root는 별도로 두 뷰의 시작/중간/끝을 시각 확인했다.
- 두 뷰는 사전 규칙으로 선택된 **best500, env0, 안전 완주4/67**의 동일 곡이다. 4음이 가장 많은 환경을 고른 것이 아니다. best는 평가한 네 학습 모델의 전체1024 평균 우선 규칙이며, 해당500 모델의 안전 환경은414/1024이고 실패는610개이다. 안전 env0 영상으로 전체 안전성이나 자연스러운 연주를 인증하지 않는다. 이번에 검수한 두 파일은 모두 best500의 서로 다른 뷰이며 latest2000 영상으로 표기하면 안 된다.

## 임시 저장 정리 결과

이전에 검수한 `finish_temporary_storage.py` SHA가 그대로인 상태에서 root가 실행한 결과만 읽었다. `temporary_cache_release_before.json`의 사전 manifest/연결 검사 로그 SHA가 실물과 일치하고, `temporary_storage_final.json`은 완료 및 3,644,790,537byte의 자기 생성 RAM 고아 캐시 하나만 해제했다고 기록한다. 해당 `/dev/shm/...snapshot2` 경로가 실제로 없음을 확인했다. 정리 도구나 unlink를 검수자가 실행하지 않았다.

현재 읽기 전용 `git config --local --get-all`로 gc.auto/maintenance.auto가 모두 absent임을 확인했다. 사전0/false에서 기대값만 조건 삭제하여 after=[]로 돌아간 기록과 일치한다. fresh `git fsck --connectivity-only`의 exit0은 도달 가능한 Git 연결성 범위이며 전체 object 내용 SHA 인증이 아니다. 유효 pack/refs/index 또는 실제 학습 자료를 정리 대상으로 삼지 않는 도구 경계는 유지됐다.

## 핵심 SHA256

| 산출물 | SHA256 |
| --- | --- |
| posture_analysis/analysis.json | `63c5edf2d591cbe7d2773f514e0c602d89f7c4d3462e2ab1892f61c83d890259` |
| posture_analysis/report.md | `b203cce748a467ffe38c797ad23be070fc7d321fcb7afb362899ebccd70f3a64` |
| best_fullbody_60fps.mp4 | `5465bcd677b0e796500214d2ea8d53f39949738e2962dff9713e1d379a980bf4` |
| best_left_hand_60fps.mp4 | `24cbe1699a3afd6b3ee5ccd93add0a29e76385f943fcfb6af2de24cf6e00fb65` |
| 전신 pose_audit.json | `0b6f19f0833744e4d700649ed9d8b491549afa106cfec7b0b53e4e2cc3e187b4` |
| 손 pose_audit.json | `bbe49f24df8254aa6a4444ae522f9ae2ca925794aa3c8080559b828791f40ca4` |
| media_qa.json | `bd0e3de89e5ef78fc9f524d36f0ffb0a363fe88cba2760f9ac0830479af5cb53` |
| temporary_storage_final.json | `fef055c07641e87dd54150acce4e8595e8f107c22b9296c63a994f1d093bc0be` |

Critical/Warning: 추가 수정이 필요한 정합성 결함을 발견하지 못했다. 검수 중 활성 소스·도구·기존 문서·원자료를 수정하지 않았고, CPU 읽기/ffprobe 및 기존 PNG 확인만 수행했다. 이 검수 MD만 새로 작성했으며 쓰기를 종료한다.
