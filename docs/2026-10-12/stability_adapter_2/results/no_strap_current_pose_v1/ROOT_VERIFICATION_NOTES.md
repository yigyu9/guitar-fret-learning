# 최종 검증 범위와 보존 정정

- 실제 물리 실행은 스트랩 없는 조건1회·1200step·5.000초이다. 저장자료 분석1회와 영상모음 원본복사1회가 뒤따랐다. 최종 감사는 물리/분석을 재실행하지 않는다.
- `analysis.json`의 `all21_initial_fields_exact`는 잘못된 개수 label이다. `compared_initial_fields`는 실제20개이며, 모든20개와 전체 초기native state·81×1200최종명령이 기준과같다. 소비된소스/결과는보존하고문서와최종감사에서실제개수를사용한다.
- 분석의 `build_fixed_lower_asset.py`가 가져오는 `strap.py`는 분석단계 manifest의 별도행에없다. 물리실행14,028개입력closure와사전source_snapshot에는포함돼있으며최종감사에서동일SHA확인·최종사본을보존한다. 이를분석단계에서별도로사전보존했던것처럼설명하지않는다.
- 스트랩장력은전체1201표본0이며explicit rigid-body force API 호출0이다. trace에남은nominal LA/route/법칙파라미터는비활성진단정보이며스트랩이힘을가했다는증거가아니다.
- 환경은Isaac Gym의CPU PhysX이며GPU pipeline disabled다. CUDA/일부visual geom 로딩경고를원로그에보존했다. 실제생성된native화면과정상1200step/151frame기록을확인했다.
- source1188 초기형상검사는PhysX cooked침투없음의인증이아니다. 후기변화가작아진것은다른자세에서의안정화관측이며초기자세유지·자연스러운연주·checkpoint호환성공을뜻하지않는다.
- 이전initial_middle3_alignment_v1과fixed_strap_source_compatibility_v1의선언된inventory파일,기존영상140개,main문서기존prefix를최종감사로보존확인한다. 기존stability_adapter/·공용자산을수정하는작업은없었다.
