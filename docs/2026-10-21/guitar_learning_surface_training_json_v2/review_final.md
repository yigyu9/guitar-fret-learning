# 최종 독립 검수

**요약 판정: 문제없음 / PASS.** 남은 Critical·Warning 및 문서 수정 요청은 없다. 이 검수에서는 원자료를 읽어 대조했으며 이 파일 외에는 수정하지 않았다.

## 검수 범위와 결과

현재 phase의 `README.md`, `training_process_result.json`, `video_visual_check.json`, `video_ffprobe.json` 및 갱신한 `CURRENT_STATUS.md`, `guitar_learning/README.md`, `guitar_learning/AGENTS.md`, `docs/2026-10-26/learning_flow/README.md`를 기존 실행·평가·영상 증거와 대조했다.

- 최종 경로는 저장된 **300+150+350+1200회**, 65,536,000전이·64,000행이다. 미저장 63회·2,064,384전이는 보존하되 이 경로에서 제외한다. 세 재개에서 모델·두 optimizer·RNG·3331값 이력을 복원하고 물리는 새 준비 에피소드로 시작한다. 단일 프로세스의 연속 2000회 실행으로 표현하지 않았다.
- 마지막 1200회 보고서의 39,321,600전이·153,600 batched physics step·13,110.3196초와 실제 GDB 로그의 `exited normally`, 프로세스 결과의 exit0/정상 GPU close가 일치한다. 감독 workflow의 완료 상태와 변경 없는 workflow 입력 SHA도 확인했다.
- 과거 세 SIGFPE·native cleanup 실패와 x87 상태 변경 주체 미확인을 보존했다. 과거 gzip 전체 CRC/EOF 통과는 각 crash audit의 근거이며, 최종 검증의 과거 저장 prefix 재검산 및 native 정상 종료와 구분된다. Dragon4를 근본 FP 원인 해결이나 모든 설정의 무실패 보장으로 확대하지 않았다.
- 고정 평가의 원장 1024곡씩을 독립 재집계해 평균 **3.861328→8.300781/67음**, 안전 완주 **1024→1020**, 최종 손가락별 달성 **8383/0/111/6**을 확인했다. 최종 검지 점유율은 98.6235%이고 중지·67음 전체 성공은 0이다. 공통 safe ID1020개의 평균3.865686→8.310784, 관측 최대8→16, 네 기타 변위 실패 시각과 미달성의 배타적 분해도 원자료와 일치한다.
- 학습 수집 마지막100회의8.061은 전체 종료곡 평균이고 마지막250회의8.090은 안전곡 평균이다. 고정 최종 정책의8.301과 구분했다. 후반 검지 편중, 약지·새끼 퇴행, 중지의 접촉/유지 희소성을 전체 성공 하나로 가리지 않았다. 손가락별 보상 정규화는 이미 적용돼 있으며, 후속 후보를 검증된 원인·해결책으로 표현하지 않았다.
- 초기/최종 자체 curriculum0/1, 같은 곡·준비 자세의 상관된 환경, 비독립 seed, 접촉 합력·표면 후보와 실제 현 압력·음향의 차이를 명시했다. 초기64회 검증과 이후 장기 경로를 구분하도록 보완한 AGENTS 문구도 확인했다.

## 영상과 보관 근거

영상은 사전 환경0~7 중 최저 safe ID0의 첫 곡9/67음을 사용한다. 1970개 원자료 자세에서 endpoint1969프레임을 사용한106몸체/105관절 기록, 실제 시계·마지막 달성 수·NPZ/MP4 SHA와 전체 pose/projection 감사가 일치한다. 새 물리 적분·정책 재실행·보간은 없다.

독립 ffprobe 자료는 H.264·1280×720·60fps·1969프레임이며 container duration32.817000초는 영상 보고서 stream duration32.816667초와 일치하는 반올림 범위다. root의 처음/중간/종료 미리보기 시각 검수는 `video_visual_check.json`에 별도로 기록돼 있고 세 이미지 SHA도 일치한다. 본 검수는 기존 영상·감사 자료를 읽었으며 Renderer·GL·새 평가를 실행하지 않았다.

현행429개 Python 파일의 동일집합과 현재 파일/`source_training` SHA를 직접 확인해 불일치0이었다. 이전 문서4개의 보관 SHA와 현재 문서 링크 존재도 확인했다. root의 과거3개 봉인 전체 검증 결과(790/646/860파일) 및 protected3 무변경 결과를 읽어 확인했다. CPU831개 통과 로그 요약과 Dragon4의370회 CPU재생3회 통과 자료는 실제 장기 실행·연주 성능의 별도 증거로 구분된다.

## 검수한 최종 요약·문서 SHA256

| 파일 | SHA256 |
| --- | --- |
| phase `README.md` | `e4702899e9c637b0a2f49e1781d2a69c56aa2b11d61c99a5ab5d3c58a0c0897c` |
| `training_process_result.json` | `6fb6445378f69b2d144cf670deddc8d7da50c3c98b3459f92c0c2d531a281146` |
| `video_visual_check.json` | `65b4bb56014ecdab7cce6ebb15cfc76cdf79083b15fe5ef1702c896e422001ec` |
| `video_ffprobe.json` | `074feac0757a97cbc65bc1db846b7e816352c431983510abaa333fba4f4f2653` |
| `CURRENT_STATUS.md` | `ab1f7d37032454f4f3b104c24d73011f6ba41a9b836b568429d8a321b0228690` |
| `guitar_learning/README.md` | `3bf031b57198299ceaf5a60936d9ede4a121a744c7d641ac249e015c51ab28bb` |
| `guitar_learning/AGENTS.md` | `defcfcc49d3668dbb4afc297e188e61ad6fa64331c25b7203e2f46b5dbcd7019` |
| `docs/2026-10-26/learning_flow/README.md` | `32ad29bf4f42b0f92a1531676f728df90364a5b0b38c7f7100fdeb9e370e3ee5` |

추가 검증 도구·CPU 테스트·GPU·GL을 재실행하지 않았다. 이 결과는 기록된 실행·평가·영상 및 문서의 정합성에 대한 검수이며, 네 손가락의 곡 연주 숙련·새 곡/seed 일반화·x87 근본 원인 해결을 인증하지 않는다.
