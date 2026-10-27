# 독립 코드 검수와 초기 실패 수정

전곡 신규 코드와 CPU 검사를 change-reviewer가 별도로 검수했다. 최초 지적은 expired_count 누락과4개 표본 확인 부족이었고, 원장 진행률을 추가하고환경에서4physics samples를명시 검사했다. 평가도 실제1969step/episode.valid/정확한끝시각/fullsafe와음악성공을구분하도록보강했다.

최초 native training_v1은 환경 구성 후 Actor 초기화에서 중단됐다. generic runner의전역settings parserpatch가 원전문가설정검증에도stageD를 적용한 것이 원인이었다. 원래실패report와소스는보존했다. 파서는 현재run의song키가있는입력만전곡설정을반환하고다른입력은원파서로처리하도록수정했다. 원본은 archive/20261019_before_song_settings_dispatch_fix에보존했다.

회귀검사에서는 patch내부에서실제left BC settings를기존local parser로읽어stageB/roleleft가유지되는지확인했다. 검수자는실제BC증거/gate/hash와기록몸체의전곡계약,실제SongPolicy/PPOTrainer를train.run의전체patch안에서생성해Actor이전·freshAdam/update0·초기화기록출판까지확인했다. 원파서오염의추가경로는발견되지않았다.

최신 신규 CPU41개 통과. 최종 재시도 전 코드 검수: Critical/Warning없음. 이 판정은 코드/CPU범위이며 실제학습의안전성과연주성과는 training_v2 원자료로판단한다.
