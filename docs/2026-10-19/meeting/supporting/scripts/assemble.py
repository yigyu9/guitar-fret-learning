"""Copy selected completed research artifacts without changing experiment sources."""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    meeting=Path(__file__).resolve().parents[2]
    root=meeting.parents[2]
    catalog=json.loads((meeting/'supporting/catalog.json').read_text())
    records=[]
    for item in catalog:
        source=root/item['source'];dest=meeting/item['destination']
        dest.resolve().relative_to(meeting.resolve())
        before=sha(source)
        if args.verify:
            if sha(dest)!=before:raise RuntimeError('copy/source digest mismatch: '+str(dest))
        else:
            dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():
                if sha(dest)!=before:raise FileExistsError('preserve existing different file: '+str(dest))
            else:shutil.copy2(source,dest)
        if sha(source)!=before or sha(dest)!=before:raise RuntimeError('source changed while copying: '+str(source))
        records.append(dict(item,sha256=before,bytes=dest.stat().st_size,source_absolute=str(source),destination_absolute=str(dest)))
    if args.verify:print('verified',len(records),'copies; original bytes unchanged')
    else:
        target=meeting/'supporting/provenance/copied_files_v1.json'
        with target.open('x') as stream:json.dump(dict(created_utc=datetime.now(timezone.utc).isoformat(),files=records),stream,ensure_ascii=False,indent=2)
        print('copied',len(records),'files')


if __name__=='__main__':main()
