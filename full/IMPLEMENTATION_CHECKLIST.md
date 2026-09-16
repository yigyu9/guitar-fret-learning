# 구현 체크리스트

> 상태: **2026-09-07 현재**

- [x] song bundle에서 Canonical PlayEvent compile 및 입력 hash 검증
- [x] one score clock, one cursor, exactly-once event resolution
- [x] effective sounding-fret readiness와 1-frame dwell
- [x] 최대 3-frame·event별 0~3-frame safe delay rule supervisor
- [x] ordered/directional/unplanned crossing 검증
- [x] Fret-v2 420D·Strike-v2 303D strict source loader
- [x] 105D named action manifest와 G0 60 active + 45 hold partition
- [x] CPU bundle·runtime·checkpoint interface probe
- [ ] shared simulator를 소유하는 `FullG0Task`
- [ ] standalone task와 동일한 Fret/Strike inference view 추출 및 parity test
- [ ] current-pose hold와 entry-side 물리 gate
- [ ] merged collision filter 감사
- [ ] qualified full-song source checkpoint 쌍 확보
- [ ] 1-env fixed-guitar physical smoke
- [ ] 전체곡 deterministic G0 평가와 영상
- [ ] `strapped-v1`을 G1 환경에 연결
- [ ] StabilityAdapter 학습·assist 감소·G2 평가

체크 항목의 상세 계약은 [`03_implementation/STATUS.md`](03_implementation/STATUS.md)와
[`master_plan`](../master_plan/README.md)을 따른다.
