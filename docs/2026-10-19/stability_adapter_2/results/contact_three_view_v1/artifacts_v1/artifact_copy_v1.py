from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
ROOT=Path('/home/ajou/yigyu/3')
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/contact_three_view_v1'
ART=P/'artifacts_v1';V=ROOT/'docs/2026-10-19/stability_adapter_2/video/contact_three_view_v1'
SRC=P/'visual_v1'
SNAPS=[('three_views_00015.png',0.5,'prepare'),('three_views_00105.png',3.5,'hold_A'),('three_views_00160.png',5.333333333333333,'release_A'),('three_views_00195.png',6.5,'open_A'),('three_views_00315.png',10.5,'hold_B'),('three_views_00420.png',14.0,'open_B')]
VIDS=[('front.mp4','front.mp4','front'),('right_side.mp4','right_side.mp4','right_side'),('top.mp4','top.mp4','top'),('front_side_top.mp4','front_side_top.mp4','combined')]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
 before=read(ART/'artifact_before_v1.json');pin={x['path']:x['sha256'] for x in before['inputs']}
 if before['self']['path']!=str(ART/'artifact_copy_v1.py') or before['self']['sha256']!=sha(ART/'artifact_copy_v1.py'):raise SystemExit('self hash differs from pre-pin')
 if any(sha(p)!=h for p,h in pin.items()):raise SystemExit('pinned input hash mismatch before copy')
 report=read(SRC/'report.json');summary=read(P/'contact_summary_v1.json');repro=read(P/'reproduction.json')
 if not report.get('inputs_unchanged') or not repro.get('inputs_unchanged') or not all(repro.get('exact',{}).values()):raise SystemExit('closed source report checks failed')
 copies=[]
 for source_name,dest_name,view in VIDS:
  src=SRC/source_name;dst=V/dest_name
  want=report['videos'][view]['sha256']
  if sha(src)!=want:raise SystemExit(f'source video hash mismatch: {source_name}')
  shutil.copy2(src,dst)
  if sha(dst)!=want:raise SystemExit(f'video copy mismatch: {dest_name}')
  copies.append({'kind':'annotated_video','source':str(src),'copy':str(dst),'sha256':want,'expected_sha256_from_report':want})
 for filename,t,stage in SNAPS:
  src=SRC/filename;dst=ART/filename
  rec=next(x for x in report['snapshots'] if abs(x['time_s']-t)<1e-9)
  if src!=Path(rec['path']) or sha(src)!=rec['sha256']:raise SystemExit(f'snapshot source/report mismatch: {filename}')
  shutil.copy2(src,dst)
  if sha(dst)!=rec['sha256']:raise SystemExit(f'snapshot copy mismatch: {filename}')
  copies.append({'kind':'annotated_three_view_snapshot','time_s':t,'stage':stage,'source':str(src),'copy':str(dst),'sha256':rec['sha256'],'expected_sha256_from_report':rec['sha256']})
 # Concise stage observations from the closed summary; all values are marker rows, not events.
 snaps=summary['snapshots'];assert len(snaps)==6 and summary['raw_feature_rows_across_30fps_frames']==7912
 snappath=lambda fname:str(ART/fname)
 pairs=[
  ('0.5 s · 준비',snappath('three_views_00015.png'),'Chest, 오른쪽 위팔·허벅지, 왼쪽 검지 접촉 표식이 보임.'),
  ('3.5 s · A 유지',snappath('three_views_00105.png'),'엄지와 검지 양의 접촉 표식; Chest 0, 왼쪽 허벅지 양의 표본 0.'),
  ('5.333 s · A 해제 전환',snappath('three_views_00160.png'),'오른쪽 허벅지 표식은 없음. 왼쪽 허벅지·위팔·엄지·검지·새끼손가락 표식은 남음; 완전 해제 장면으로 해석하지 않음.'),
  ('6.5 s · A 분리 유지',snappath('three_views_00195.png'),'왼팔·손 표식 없음; Chest·오른쪽 위팔·허벅지 표식은 있음.'),
  ('10.5 s · B 유지',snappath('three_views_00315.png'),'Chest·오른쪽 위팔·허벅지 및 왼쪽 엄지·검지 접촉 표식.'),
  ('14.0 s · B 분리 유지',snappath('three_views_00420.png'),'왼팔·손 표식 없음; Chest·오른쪽 위팔·허벅지 표식은 보임.')]
 Pabs=str(P);Aabs=str(ART);Vabs=str(V)
 rowtext='\n'.join(f'| {title} | [{Path(path).name}]({path}) | {caption} |' for title,path,caption in pairs)
 readme=f'''# 접촉 표식 3-view 재현 자료

이 실행은 기존 16초 물리 trace의 exact 재생이다. 재현 기록상 `trace.json`, `actual_contacts.json`, `initial_values.json`이 이전 실행과 일치하며 모든 입력은 변경되지 않았다. 화면은 전면·오른쪽 옆면·위 순서로 배치했다. 세 view 각각 native 1280×720 이미지 위에 220 px 설명 footer를 붙였고, 합본은 1920×470이다. 동영상은 각 481 frames, 30 fps, 표시 길이 16.0333초다.

## 접촉 표식 읽기

- 원형 표식 색: Chest 청록, 오른쪽 위팔 주황, 오른쪽 허벅지 보라, 왼쪽 허벅지 파랑, 왼손 엄지 빨강, 왼손 나머지 손 노랑, 그 밖의 인체 부위 회색.
- **손 모델의 초록·분홍 표면은 원래 재질색**이다. 접촉 표식은 그 위에 그려진 원형 점뿐이며, 손 표면색은 접촉 표시가 아니다.
- 원형 점이 채워져 있으면 양의 raw lambda, 속이 비면 접촉 행은 있지만 lambda=0이다. 점 크기는 화면상 고정이며 힘의 크기를 나타내지 않는다.
- 점들은 **X-ray처럼 항상 보이도록** 그려져 몸체 뒤에 있는 접촉 특징도 표시한다. 실제 occlusion이나 가림을 묘사하지 않는다.
- 동일 그룹 안의 2 mm voxel dedup은 시각 판독을 돕기 위한 단계다. 원시 행을 삭제하지 않으며 2 mm 접촉 반경, 면적 또는 압력을 뜻하지 않는다.

## 실제 캡처 예

각 PNG와 MP4는 source 산출물의 바이트 보존 복사다. 캡션은 스냅샷 시점의 raw-row/양의 lambda 분류를 요약하며 인과관계를 주장하지 않는다.

| 시점·단계 | native 3-view frame | 관찰 |
|---|---|---|
{rowtext}

아래는 네 시점의 전체 화면 이미지다.

![0.5초 준비, 3.5초 A 유지, 5.333초 A 해제 전환, 14초 B 분리 유지]({snappath('three_views_00015.png')})

![A 유지 시점 3.5초]({snappath('three_views_00105.png')})

![A 해제 전환 5.333초]({snappath('three_views_00160.png')})

![B 유지 시점 10.5초]({snappath('three_views_00315.png')})

## 원시자료 범위와 한계

여섯 30 fps snapshot을 합친 요약은 7,912 raw feature rows다. 행 수는 독립 접촉 사건 수가 아니다. body-local contact feature를 body 원점과 정규화된 native quaternion으로 world 변환해 쌍을 비교한 최대 잔차는 0.000141880 mm였다. 양의 raw lambda는 보정된 힘(N)이 아니며, contact area나 압력으로 해석하지 않는다. 표식은 30 fps 순간값이며 모든 240 Hz 표본이나 solver substep을 보여주지 않는다. 각 시점의 동시 접촉만 묘사하며 접촉의 원인이나 지지 기여를 입증하지 않는다.

[네 개 전체 annotated native 영상]({Vabs}/README.md) · [contact 요약 원자료]({Pabs}/contact_summary_v1.json) · [render report]({Pabs}/visual_v1/report.json) · [exact 재현 보고서]({Pabs}/reproduction.json) · [copy manifest]({Aabs}/copy_manifest_v1.json)
'''
 (ART/'README.md').write_text(readme,encoding='utf-8')
 index=f'''# 접촉 표식 native 3-view 영상

4개 16초 annotated native 영상. 화면은 전면·오른쪽 옆면·위 순서이며, 원형 접촉 표식은 양의 lambda/0 lambda로 채움 여부를 나눈다. 표식은 X-ray처럼 항상 보이고, 초록·분홍 손 재질색은 접촉 표시가 아니다. fixed-pixel 점은 힘을 나타내지 않는다. 상세 범위와 6개 스냅샷은 [한국어 설명]({Aabs}/README.md)에 있다.

## 전면

![전면 view]({Vabs}/front.mp4)

## 오른쪽 옆면

![오른쪽 옆면 view]({Vabs}/right_side.mp4)

## 위

![위 view]({Vabs}/top.mp4)

## 전면·오른쪽 옆면·위 합본

![세 view 합본]({Vabs}/front_side_top.mp4)
'''
 (V/'README.md').write_text(index,encoding='utf-8')
 after={p:sha(p) for p in pin}
 if any(after[p]!=h for p,h in pin.items()):raise SystemExit('pinned inputs changed during copy/docs')
 copyhash=all(sha(x['copy'])==x['sha256'] for x in copies)
 if not copyhash:raise SystemExit('final copy hash mismatch')
 outputs=[ART/'README.md',V/'README.md']
 manifest={'schema':'contact_three_view_artifact_copy_manifest_v1','self':before['self'],'inputs_before':before['inputs'],'inputs_after':[{'path':p,'sha256':h} for p,h in after.items()],'all_inputs_unchanged':True,'copies':copies,'all_copies_match_report_sha':True,'outputs':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in outputs]}
 (ART/'copy_manifest_v1.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({'input_count':len(pin),'copies':len(copies),'inputs_unchanged':True,'copy_hashes_verified':True},ensure_ascii=False))
if __name__=='__main__':main()
