# 기존115/114 scripted 비교 영상 QA

**네 실제 scene·8MP4의 촬영/종료/원자료 대조를 통과했다. 음악 결과는 기준20Nm 검지3/4·중지4/4, 진단0.25Nm 검지0/4·중지4/4다. 전체16첫시도 원장은 원실행과 같으며 영상은 그중 각env0 첫시도만이다.**

| 조건 | 전체4 달성 | mean clean/wrong | env0 달성 | 손 영상 | 전신 영상 |
|---|---:|---:|---|---|---|
| baseline20_index | 3/4 | 75.00%/0.00% | True | [hand](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/finger_effort_limit_v1/native_videos_v1/runs/baseline20_index/hand.mp4) | [fullbody](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/finger_effort_limit_v1/native_videos_v1/runs/baseline20_index/fullbody.mp4) |
| baseline20_middle | 4/4 | 100.00%/0.00% | True | [hand](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/finger_effort_limit_v1/native_videos_v1/runs/baseline20_middle/hand.mp4) | [fullbody](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/finger_effort_limit_v1/native_videos_v1/runs/baseline20_middle/fullbody.mp4) |
| cap025_index | 0/4 | 0.00%/100.00% | False | [hand](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/finger_effort_limit_v1/native_videos_v1/runs/cap025_index/hand.mp4) | [fullbody](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/finger_effort_limit_v1/native_videos_v1/runs/cap025_index/fullbody.mp4) |
| cap025_middle | 4/4 | 100.00%/0.00% | True | [hand](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/finger_effort_limit_v1/native_videos_v1/runs/cap025_middle/hand.mp4) | [fullbody](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/finger_effort_limit_v1/native_videos_v1/runs/cap025_middle/fullbody.mp4) |

손 색상은 엄지 red, 검지 blue, 중지 green, 약지 orange, 소지 purple이다. 시각 식별용이며 접촉쌍·힘 색상이 아니다.

각4환경의첫시도·실패를포함하며네개촬영의16시도를878개env0끝점과구분한다. 이전원장과전체음악상태/입력·통계대조는comparison.json과attempts.csv에남겼다. 모든물리/손목실패는0이다. 기존index115/middle114고정목표이며새grid112성공영상·정책학습/체크포인트·4seed·4환경전체영상으로부르지않는다.

![손 비교](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/finger_effort_limit_v1/native_videos_v1/analysis/qa_frames/contactsheet_hand.png)

![전신 비교](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/finger_effort_limit_v1/native_videos_v1/analysis/qa_frames/contactsheet_fullbody.png)

행은기준index/middle→capindex/middle,열은첫프레임/이동1초/음중3.066667초/마지막이다. view_image로32대표프레임contactsheet와4조건음중손원본·전신원본을직접확인했다. upright·전신머리/양발여백·손마디굴곡방향은보인다. 넥이손일부를가리므로모든관절/실제접촉·압력·자연성을시각인증하지않는다.

1280×720·30fps·h264각index110/middle109프레임이다. frame n은실제60Hz endpoint2(n+1)에대응하며첫화면local1/30초로t0프레임은없다. index의마지막221번째끝점은raw에만있고110번째프레임은endpoint220이다. middle마지막109번째프레임은endpoint218이다.

관찰raw와같은촬영collector/원실행의q·target·body_state·force·candidate/wrong·scripted/executed action·nearest거리/높이는네조건모두값이정확히같았다. 시간표현(/60 vs /240)의차이를별도기록하고음악/물리허용오차로사용하지않았다. 나머지원시필드의dtype/exact/maxabs/RMS와미저장필드는comparison.json에전부보존한다. 기존CPUnearest argmin/높이재생한계를해결했다는뜻은아니다.

836준비핀과모든실제전후입력·설정/계약·네scene닫힘·8encoder종료0·physics240/control60시계를확인했다. cap의저장native105전필드readback은원cap자료와exact이며16effort외차이0/충돌90쌍이다. 기준native105는pin된원constructor의각환경전필드readback검사근거이며별도baseline배열을새로저장한것처럼다루지않는다.

이자료는기존scripted/fixed기타비교다. cap일괄채택·인간힘한계·현별압력/접촉쌍·음향·자연스러운자세·장기학습·해제/전환/전곡성과를인증하지않는다. 새GPU/native실행없이기존native영상만디코딩했다.
