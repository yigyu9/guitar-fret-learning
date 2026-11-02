"""공유 파일을 읽어서 복사 manifest와 대조한다. 원본에는 쓰지 않는다."""
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parents[1]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
 return h.hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('before','after'),required=True);args=parser.parse_args()
 manifest_path=BASE/'공유파일목록.json';manifest=json.loads(manifest_path.read_text());records=[];bad=[]
 for group,prefix in [('study_files',BASE),('reference_project_files',BASE/'읽기용코드')]:
  for name,expected in manifest[group].items():
   path=prefix/name
   if not path.is_file():actual=dict(exists=False)
   else:actual=dict(exists=True,bytes=path.stat().st_size,sha256=sha(path))
   passed=actual.get('bytes')==expected['bytes'] and actual.get('sha256')==expected['sha256']
   row=dict(group=group,path=str(path.relative_to(BASE)),expected=expected,actual=actual,passed=passed);records.append(row)
   if not passed:bad.append(row)
 controls={name:dict(sha256=sha(BASE/name),bytes=(BASE/name).stat().st_size) for name in ['공유안내.md','공유상태.json','공유검증.json','공유파일목록.json','다른PC_검토프롬프트.md']}
 result=dict(checked_at=datetime.now(timezone(timedelta(hours=9))).isoformat(),phase=args.phase,
  ready=json.loads((BASE/'공유상태.json').read_text()).get('ready'),
  manifest_sha256=sha(manifest_path),expected_manifest_sha256=json.loads((BASE/'공유검증.json').read_text())['manifest_sha256'],
  copied_files=len(records),copied_bytes=sum(r['actual'].get('bytes',0) for r in records),bad=bad,controls=controls,records=records)
 result['passed']=not bad and result['ready'] is True and result['manifest_sha256']==result['expected_manifest_sha256']
 if args.phase=='after':
  before=json.loads((OUT/'integrity_before.json').read_text());result['controls_unchanged']=controls==before['controls'];result['copied_files_unchanged']=records==before['records'];result['passed'] &= result['controls_unchanged'] and result['copied_files_unchanged']
 (OUT/('integrity_'+args.phase+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('records','controls','bad')},ensure_ascii=False));print('bad files',len(bad))
 if not result['passed']:raise SystemExit(1)
if __name__=='__main__':main()
