# v8 GPU 왼손 장기 학습 결과

**학습·검산·저장본 평가와 영상 생성을 완료했다. 평가한 학습 모델 중 최고는1500회다.** large/1024환경/H32/seed7로 fresh2000업데이트·65,536,000전이를 정상 완료했다. 평균 달성음은 초기3.8633/67→최고7.8262→최종6.7383음으로 늘었지만, 모든67음 성공은0이며 손가락별 편중과 끝관절 집중이 남았다. 연주 수렴이나 자연스러움 개선 완료로 분류하지 않는다.

원곡은05_BN2-131-B_solo의67음이다. 학습은2026-10-22 22:52:56 KST에 시작해2026-10-23 05:39:00 KST에 정상 종료했다. launcher 기준6시간46분4초, 실제 runner는6시간45분59.9초다. 이전 smoke8+1회와 v6의 전이는 합산하지 않았다. 별도2000→2001 strict resume1회는32,768전이이며 장기 예산에서 제외했다.

## 고정1024환경 평가

각 모델의 동일 곡·seed7·035/v14 초기자세에서 환경별 첫 종료곡만 평가했다. 물리 종료를 포함한 전체1024의 평균이며, 안전 완료는32.8167초를 마친 곡 수다. 저장3331값 curriculum을 그대로 복원했고 다섯 모델의 progress는 모두0이었다. 평가 중 PPO나 curriculum을 갱신하지 않았다.

| 업데이트 | 평균 달성음 /67 | 안전 완료 /1024 | 67음 전체 성공 |
| ---: | ---: | ---: | ---: |
| 초기0 | 3.863281 | 1023 | 0 |
| 500 | 1.265625 | 850 | 0 |
| 1000 | 5.555664 | 936 | 0 |
| **1500** | **7.826172** | **999** | **0** |
| 최종2000 | 6.738281 | 990 | 0 |

평가한500/1000/1500/2000 중 전체 평균 달성음→안전 완료수→최근순으로1500회를 선정했다. 초기0은 별도 기준이며, 모든100회 간격 저장본이나 다른 곡의 최고를 찾았다는 뜻은 아니다. 최고 평균도67음의 약11.68%다. `음 달성`은 지정 손가락·현·프렛의 기하/몸체하중 기반 clean 누적 기준이며 실제 현 압력·음향 인증과 구분한다.

## 핵심 분석

**모든 손가락이 함께 좋아진 결과는 아니다.** 최고1500의 안전999곡에서는 검지/중지 달성0, 약지6248건·소지1647건이었다. 최종 안전990곡에서는 검지5건·중지2건·약지6757건·소지0건이다. 이 건수의 분모는 곡 수×손가락별 목표 수(25/18/12/12)로 다르다. 상세 비율은 고정 평가 보고서에 있다.

**후반 하락은 물리 종료 증가만으로 설명되지 않는다.** 두 모델에서 모두 안전한 동일965환경에서도 평균7.9233→6.8187음으로 낮아졌다. 이 집단의 소지1587건 소실을 약지514건·검지5건·중지2건 증가가 일부 상쇄했다. 고정 정책에서의 성과 교체는 확인했지만 신경망 망각이나 특정 보상·optimizer 하나를 원인으로 확정하지 않는다.

**주된 병목은 목표 접근이다.** 최종 안전곡의66,330개 목표 중57,867개(87.241%)는 목표 geometry에 한 번도 진입하지 못했다. clean 유지시간만 부족한 경우는811개(1.223%)다. 최종 소지의11,880개 목표는 모두 준비창에서 최소거리5cm 초과였고 near/contact/달성이0이었다. 단순 유지시간 완화로 해결될 모양은 아니며 성공 조건을 바꾸지 않았다.

**단계0이 손가락 압현을 막은 것은 아니다.** 단계0에서도 접촉·달성 보상이 작동한다. 검지·중지의 near 지표가 낮아 모든 손가락 near20%와 안전90%를 함께 요구하는 진급 gate를 충족하지 못했다. 학습 전체에서도 curriculum은0이었다.

**손가락 모양 문제는 남았다.** 사전 지정8환경×5모델의 실제 자세40개 캡처를 분석했다. 모두 안전 완료 표본이므로 물리 실패 환경을 대표하지 않는다. 최고·최종의10초 이후 소지는 PIP가 거의 펴지고 DIP가90도 근처인 끝점이100%였다. 최종 검지·중지에는 PIP/DIP 동시 큰 굽힘도 지속됐다. 손가락 움직임 비용0·전체 native 범위·독립 누적제어·PD를 유지했다는 구현 사실과 자연스러운 관절 분담을 학습했다는 결론은 다르다.

다음 검토 우선순위는 검지·중지의 접근 부족, 이미 얻은 소지 성과의 유지, 끝관절·누적 한계 명령에 의존하는 자세다. 이번 결과 제공 작업에서 학습 코드·보상·성공/안전 기준은 변경하지 않았다.

- [손가락별 고정 평가·접근 원인·실제 자세 상세](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/fixed_evaluation_analysis.md)
- [학습 로그·PPO·메모리 분석](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/result_log_analysis.md)
- [고정 평가 상세 수치와 입력SHA](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/fixed_evaluation_analysis.json)

## 로그·실행 검증

전체34,791종료곡 중 시간축 완료29,150곡, 물리 실패5,641곡이다. 학습 중 바뀌는 확률적 정책의 수집 집단이며 위의 고정 모델 평가와 합치지 않는다. 마지막 수집 구간에도 달성음 하락과 소지 성과 소실이 나타났다. reward/cost advantage의 개별 정규화는 유한값과 요약 통계 검산을 통과했으며, 이 사실을 어느 신호가 실제 gradient를 지배했다는 인과 증거로 해석하지 않는다.

전체64,000 raw행·2,000 gzip member의 CRC/EOF·행 순서·에피소드 대응, sampled/logged/durable/committed65,536,000 일치,583입력SHA·438 Python 원문/보관본·3331curriculum 재생 오차0·모델/양Adam 유한값·정상 GPU close를 확인했다. 별도 strict resume에서는 metadata를 제외한 전체 저장 상태를 정확히 복원하고1회 갱신했다. 물리 장면/곡 시계는 새 준비 episode로 시작한다.

Torch 캐시 반환 후 GPU 여유는 최저7.034GiB·최종7.894GiB였고 비Torch 추정 증가의 마지막100회 범위는0GiB였다. 이 실행에서 할당 실패나 수치 비유한 오류는 없었다. 프로젝트 SSD는 중간에 약11.9MB까지 줄었으므로 모든 자원이 항상 넉넉했다고 주장하지 않는다. 아래 보관 이전 조치와 외장 결과 저장으로 실행을 이어갔다.

- [자동 전체 검산](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/actual_training_verification.json)
- [별도2000→2001 재개 검산](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/actual_resume_verification.json)
- [독립 전체 재검산](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/independent_training_verification.json)
- [영상 품질 검증](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/video_quality_verification.json)

아래는100업데이트 단위 학습 수집 곡선이다. 종료곡 집단과 정책이 계속 바뀌므로 위의 동결 평가 점수와 구분한다.

![학습 수집 곡선](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/plots/training.png)

## 실제 자세 영상

대표1500회와 최종2000회 모두 사전 지정env0..7 중 가장 작은 안전ID인env0을 사용했다. 각 영상의 달성은8/67·7/67이며 전체1024 평균과 다르다. 저장된 실제 GPU world pose를 재생한 것으로 새 물리 적분이나 재학습은 없다. 원본4개는1280×720·60fps·1969프레임·32.816667초다. 손 비교본은 원본 두 개를 시간 변경 없이 좌우로 붙인2560×720 영상이다. 전체5개 파일의 끝까지 decode·프레임 수·기간·SHA를 검사했고, 원본별 시작/중간/끝 프리뷰를 확인했다. 이 시각 검토를 인간 생리학적 자연스러움 인증으로 확대하지 않는다.

대표1500회 전신:

![대표1500회 전신](/home/ajou/yigyu/3/runs/left_song_v8_results_20261023/best_fullbody_video/best_fullbody_60fps.mp4)

왼쪽1500회·오른쪽최종2000회 손 비교:

![손 동작 비교](/home/ajou/yigyu/3/runs/left_song_v8_results_20261023/hands_1500_vs_2000_60fps.mp4)

- [대표1500회 손 근접](/home/ajou/yigyu/3/runs/left_song_v8_results_20261023/best_hand_video/best_left_hand_60fps.mp4)
- [최종2000회 전신](/home/ajou/yigyu/3/runs/left_song_v8_results_20261023/latest_fullbody_video/latest_fullbody_60fps.mp4)
- [최종2000회 손 근접](/home/ajou/yigyu/3/runs/left_song_v8_results_20261023/latest_hand_video/latest_left_hand_60fps.mp4)

## 보존 경로와 저장본

원자료는 `/media/ajou/새 볼륨1/guitar_learning_runs/20261022_v8_long/`에 보존했다. 원래 자동후처리의 `independent_result_review_pending=true`는 자동 종료 당시 상태로 원문을 남겼고, 이번 최종 검수는 별도 independent_result_review에 기록한다. 원래 보고서/로그/영상·모델 바이트를 덮어쓰지 않았다.

- [대표1500회 checkpoint](</media/ajou/새 볼륨1/guitar_learning_runs/20261022_v8_long/train2000/checkpoint_001499.pt>)
- [최종2000회 checkpoint](</media/ajou/새 볼륨1/guitar_learning_runs/20261022_v8_long/train2000/final.pt>)
- [실제 실행 설정](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/launch.json)
- [소스438 동결](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/training_source_manifest.json)
- [독립 최종 검수](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/independent_result_review.md)

미사용 Git 임시 pack1개(3,644,790,537바이트)는 연결 index·열린 handle 없음과 stat 불변을 확인하고 외장 storage_backup에 전체복사/fsync/재읽기SHA 대조한 뒤 이전했다. 유효pack/index/ref/staging·기존 학습 자료는 변경하지 않았다. Git 연결검사 exit0과 복구 경로/SHA는 storage_relocation.json에 있다. 영상 전달본은 원본과SHA가 같은 로컬 사본이며 delivery_manifest.json에 기록했다. 새 결과 봉인은 로컬 result_manifest.json과 외장 결과 manifest로 구분하고, 별도 임시 pack 백업은 storage_relocation의 SHA로 관리한다.
