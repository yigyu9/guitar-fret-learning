# Humanoid self-collision 독립 검수

- 검수일: 2026-10-07
- 범위: 새 probe·환경·실행기·계획, OFF/ON 저장 결과, canonical render_v2와 결과 문서.
- 검수자는 native 초기화·physics step을 추가하지 않았으며 이 새 검수 파일만 작성했다.

**요약 판정: 문제없음. 남은 Critical / Warning / Suggestion 없음.**

## 충돌 정책·실행 조건

실제 importer mask와 XML을 바탕으로 active human54개의 1,431 body pair를 독립 계산했다. LH/RH distal group의 반대 elbow bit만 제거하고 importer 기본값 대비 323쌍을 추가 허용하며 의도 외 pair 변화는 없다. 최종 허용 1,115쌍/제외 316쌍, 명시 exclude28 유지, 기타 예약 bit4096 분리와 disabled proxy 제외를 native readback과 대조했다. 동일 손 내부·연결부 제외는 남는다. 323은 모든 self pair가 제외된 OFF 대비 수치가 아니다.

OFF raw5는 이전 near2µm 실행과 exact다. OFF/ON 모두 25 states/trace 및 24 controls/contacts이고 초기 전체 state가 같다. Root·하체8 body의 전체 state 불변, 초기각·native PD·limits·기타 목표·고정 LA·solver 조건과 실제 입력 SHA 일치를 확인했다. 저장 actualq에서 팔24 PI의 6회 업데이트, e+2I·조건부 적분·clip 및 24개 held target을 독립 재계산해 float32 허용 오차 안에서 일치했다. 충돌 필터 외 모델·제어 변경이나 runtime pose 재주입은 없다.

raw contacts에서 self-contact를 다시 집계한 결과 OFF0행/ON9행이며 ON의 양수 raw lambda는 6행이다. 모두 LH:palm–RH:index1 쌍, 기록 step20–24이고 첫 기록은 0.083333초다. 정확한 물리 접촉 onset·9개 이벤트·교정된 힘·무관통·지속 지지 인증으로 확대하지 않는다. LH:palm–기타 접촉은 두 조건 모두 0이다.

## 저장 pose 재생·provenance

renderer는 같은 saved pose·같은 step의 strap 경로를 source geometry에 적용한다. probe mj_forward1회와 saved pose render54회, mj_step/native 초기화·physics 추가0의 경계가 코드와 일치한다. Canonical v2의 시작/종료 실제 SHA105입력·6helper·40asset·3output 및 실행 직전 producer 사본을 대조했다. 원 v1 producer와 두 보존 manifest의 SHA도 일치하며 초기 SHA coverage 실패 기록은 보존되어 있다.

ffprobe로 H264/yuv420p, 1280×720, 25frame, 12fps, 2.083333초를 독립 확인했다. 영상의 실제 step0/12/20/24와 종료 OFF/ON 비교 이미지를 직접 봤다. 시간·카메라·색상·strap 및 raw contact 현재/누계 행 표시가 저장 결과와 맞으며 t0는 미조회로 표시한다. 영상은 PhysX renderer·cooked clearance·힘 인증이 아니다.

## 최종 문서 검수

README·VISUAL §53·계획은 mask 범위, importer 대비 추가 허용 수치와 OFF 비교 기준, 기타 오차 최대값 및 미달성 지지를 정확히 구분한다. OFF4.041302mm/0.641189°와 ON4.035079mm/0.639349°의 작은 차이는 안정성 성공으로 채택되지 않았다. 실제 접촉 기록이 관찰돼 추가0.5초 실행 없이 이 단위를 마친 범위가 명확하다.

CHANGED_FILES의 존재하지 않는 requested_settings 필드 참조는 initial_settings로 교정됐고 새 네 구현 파일의 소유 범위가 명확해졌다. 절대 링크·실제 줄과 workflow의 후속 self-collision 경로 지침도 확인했다. 손가락 내부 제외를 더 세분화하는 작업과 지속 지지 해결은 별도 후속 범위다. 현재 검수 문서는 동결 가능하다.
