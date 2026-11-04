#!/usr/bin/env python3
"""Narrow, reviewed home cleanup. prepare is read-only except /tmp evidence; apply requires manifest SHA."""
import argparse, collections, hashlib, json, os, re, stat, time
from pathlib import Path
BASE=Path('/tmp/pc-home-cleanup-20261104')
PROPOSAL=Path('/home/ajou/yigyu/3/docs/maintenance/pc_storage_audit_20261104/user_files_audit.json')
TASK_HOME=Path('/home/ajou')
HOST_NS='pid:[4026531836]'
SAFE_UNREADABLE={'(sd-pam)','sshd','sftp-server','gvfsd-admin'}
ROOTS={
'browser_cache':[str(TASK_HOME/'.cache/google-chrome'),str(TASK_HOME/'snap/firefox/common/.cache/mozilla')],
'vscode_vsix':[str(TASK_HOME/'.config/Code/CachedExtensionVSIXs'),str(TASK_HOME/'.vscode-server/data/CachedExtensionVSIXs')],
'vscode_cache':[str(TASK_HOME/'.config/Code/Cache'),str(TASK_HOME/'.config/Code/CachedData')],
'app_logs':[str(TASK_HOME/'.config/Code/logs'),str(TASK_HOME/'.vscode-server/data/logs')],
'other_caches':[str(TASK_HOME/'.cache/zotero'),str(TASK_HOME/'.cache/thumbnails')],
'vscode_obsolete':[str(TASK_HOME/'.vscode/extensions'/x) for x in ['anthropic.claude-code-2.1.312-linux-x64','anthropic.claude-code-2.1.314-linux-x64','ms-vscode.cpptools-1.35.5-linux-x64']],
'codex_old_releases':[str(TASK_HOME/'.codex/packages/standalone/releases'/f'{v}-x86_64-unknown-linux-musl') for v in ['0.153.4','0.154.0','0.159.2']],
'claude_old_releases':[str(TASK_HOME/'.local/share/claude/versions'/v) for v in ['2.1.175','2.1.186']]}
ALL_ROOTS=[p for pp in ROOTS.values() for p in pp]
CONFIGS=[TASK_HOME/x for x in ['.bashrc','.bash_profile','.profile','.zshrc','.zprofile','.codex/config.toml','.config/Code/User/settings.json','.vscode-server/data/Machine/settings.json']]
def out(suffix):return Path(str(BASE)+suffix)
def write(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def metadata(s):return {'dev':s.st_dev,'ino':s.st_ino,'size':s.st_size,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns,'mode':s.st_mode,'nlink':s.st_nlink,'allocated_bytes':s.st_blocks*512}
def under(path,root):return path==root or path.startswith(root+'/')
def safe_chain(path):
    # lstat each component, never resolve symlinks into a different tree.
    p=Path(path); result=[]
    for parent in list(reversed(p.parents))+[p]:
        s=parent.lstat()
        if stat.S_ISLNK(s.st_mode):raise RuntimeError('symlink component: '+str(parent))
        result.append({'path':str(parent),'dev':s.st_dev,'ino':s.st_ino})
    return result
def scan():
    if os.readlink('/proc/self/ns/pid')!=HOST_NS:raise RuntimeError('Host process namespace required')
    refs=collections.defaultdict(set); inode_refs=set(); apps=set(); errors=[]; scanned=0; install=False
    for entry in os.scandir('/proc'):
        if not entry.name.isdigit() or int(entry.name)==os.getpid():continue
        try:
            if entry.stat().st_uid!=os.getuid():continue
            comm=Path(entry.path,'comm').read_text().strip(); scanned+=1
            args=Path(entry.path,'cmdline').read_bytes().decode(errors='replace').split('\0')
            low=' '.join(args).lower()
            if 'google-chrome' in low or '/chrome' in low or 'chromium' in low:apps.add('chrome')
            if 'firefox' in low or comm.startswith('firefox'):apps.add('firefox')
            if '/snap/code/' in low or '/usr/share/code/' in low or '.vscode-server/' in low or comm=='code':apps.add('code')
            if 'zotero' in low:apps.add('zotero')
            if 'thumbnail' in comm:apps.add('thumbnail')
            if any(x.startswith(('--install-extension','--uninstall-extension','--update-extensions')) for x in args):install=True
            paths=list(args)
            for name in ['exe','cwd']:
                try:paths.append(os.readlink(entry.path+'/'+name))
                except FileNotFoundError:pass
                except PermissionError:
                    if comm not in SAFE_UNREADABLE:raise
            restricted=[]
            try:
                for fd in os.scandir(entry.path+'/fd'):
                    try:
                        paths.append(os.readlink(fd.path))
                        s=os.stat(fd.path);inode_refs.add((s.st_dev,s.st_ino))
                    except FileNotFoundError:pass
                    except PermissionError:
                        if comm not in SAFE_UNREADABLE:raise
            except PermissionError:restricted.append('fd')
            try:
                for line in Path(entry.path,'maps').read_text().splitlines():
                    parts=line.split(None,5)
                    if len(parts)==6:paths.append(parts[5])
                    # Include mmap references even when no fd remains open.
                    if len(parts)>=5 and int(parts[4]):
                        major,minor=(int(x,16) for x in parts[3].split(':'))
                        inode_refs.add((os.makedev(major,minor),int(parts[4])))
            except PermissionError:restricted.append('maps')
            if restricted:
                errors.append({'pid':int(entry.name),'comm':comm,'restricted':restricted})
                if comm not in SAFE_UNREADABLE:raise RuntimeError('Unknown same-user process inaccessible: '+entry.name+' '+comm)
            for p in paths:
                p=p.removesuffix(' (deleted)')
                if any(under(p,root) for root in ALL_ROOTS):refs[p].add(int(entry.name))
        except FileNotFoundError:continue
    return {'time':time.time(),'namespace':HOST_NS,'processes':scanned,'apps':sorted(apps),'extension_install_command':install,'restricted_helpers':errors,'path_refs':{p:sorted(v) for p,v in refs.items()},'inode_refs':[list(x) for x in inode_refs]}
def config_pins():
    pins=[]
    # Search only known benign configuration files, and store matches, never contents.
    for p in CONFIGS:
        if not p.exists() or p.is_symlink() or p.stat().st_size>2*1024*1024:continue
        text=p.read_text(errors='replace')
        for root in ROOTS['codex_old_releases']+ROOTS['claude_old_releases']:
            if root in text or Path(root).name in text:pins.append({'config':str(p),'root':root})
    for directory in [TASK_HOME/'.local/bin',TASK_HOME/'bin']:
        if directory.exists():
            for p in directory.iterdir():
                if p.is_symlink():
                    target=str(p.resolve(strict=False))
                    for root in ROOTS['codex_old_releases']+ROOTS['claude_old_releases']:
                        if under(target,root):pins.append({'config':str(p),'root':root})
    return pins
def root_reason(kind,root,process,pins):
    apps=process['apps']; p=Path(root)
    if not p.exists():return 'missing'
    if p.is_symlink():return 'symlink root'
    if kind=='browser_cache' and ('chrome' if 'google-chrome' in root else 'firefox') in apps:return 'application active: preserve entire cache instance'
    if kind=='vscode_cache' and 'code' in apps:return 'Code active: preserve entire cache instance'
    if kind=='other_caches' and (('zotero' in root and 'zotero' in apps) or ('thumbnails' in root and 'thumbnail' in apps)):return 'cache producer active'
    if kind=='vscode_vsix':
        if 'code' in apps:return 'Code active: preserve entire download cache instance'
        if process['extension_install_command']:return 'extension install command active'
        if any(x.name.endswith(('.lock','.tmp','.part','.download')) for x in p.iterdir()):return 'download/install lock or partial file exists'
    if kind in ['vscode_obsolete','codex_old_releases','claude_old_releases']:
        if any(under(x,root) for x in process['path_refs']):return 'candidate version is referenced by a process'
        if any(x['root']==root for x in pins):return 'candidate version pinned in user configuration'
    if kind=='vscode_obsolete':
        obs=json.loads((TASK_HOME/'.vscode/extensions/.obsolete').read_text())
        registry=json.loads((TASK_HOME/'.vscode/extensions/extensions.json').read_text())
        if obs.get(p.name) is not True:return 'extension no longer marked obsolete'
        if any(x.get('relativeLocation')==p.name for x in registry):return 'extension is selected in registry'
    if kind=='codex_old_releases':
        current=(TASK_HOME/'.codex/packages/standalone/current').resolve(strict=True)
        if under(str(current),root):return 'current standalone release'
    if kind=='claude_old_releases':
        current=(TASK_HOME/'.local/bin/claude').resolve(strict=True)
        if under(str(current),root):return 'current Claude executable'
    return None
def file_rows(root):
    p=Path(root)
    if p.is_file():return [p],[]
    files=[];skips=[]
    for cur,dirs,names in os.walk(root,followlinks=False):
        for d in list(dirs):
            if Path(cur,d).is_symlink():dirs.remove(d);skips.append({'path':str(Path(cur,d)),'reason':'symlink directory'})
        for n in names:
            f=Path(cur,n)
            if f.is_symlink():skips.append({'path':str(f),'reason':'symlink file'})
            elif stat.S_ISREG(f.lstat().st_mode):files.append(f)
    return files,skips
def blocked_sessions(root,process):
    sessions=sorted(p for p in Path(root).iterdir() if p.is_dir() and not p.is_symlink())
    result={str(sessions[-1]):'latest session'} if sessions else {}
    for p in sessions:
        if any(under(x,str(p)) for x in process['path_refs']):result[str(p)]='open/current session'
        files,_=file_rows(str(p))
        if any(time.time()-max(f.lstat().st_mtime,f.lstat().st_ctime)<7*86400 for f in files):result[str(p)]='session has recent log (<7 days)'
    return result
def initial_protection():
    roots=[TASK_HOME/'.codex/sessions',TASK_HOME/'.codex/archived_sessions',TASK_HOME/'.config/Code/User',TASK_HOME/'.config/Code/WebStorage',TASK_HOME/'.config/google-chrome',TASK_HOME/'yigyu/guitar_learning_runs/20261022_v6_long',TASK_HOME/'.vscode/extensions/anthropic.claude-code-2.1.316-linux-x64',TASK_HOME/'.vscode/extensions/ms-vscode.cpptools-1.35.6-linux-x64',TASK_HOME/'.codex/packages/standalone/current',TASK_HOME/'.local/bin/claude']
    roots.extend(CONFIGS)
    result=[]
    for p in roots:
        try:
            s=p.lstat();result.append({'path':str(p),'metadata':metadata(s),'target':os.readlink(p) if p.is_symlink() else None})
        except FileNotFoundError:pass
    return result
def prepare():
    if out('.manifest.json').exists():raise RuntimeError('Manifest already exists; do not overwrite reviewed evidence')
    proposal=json.loads(PROPOSAL.read_text())
    if {x['id']:x['roots'] for x in proposal['candidates']}!=ROOTS:raise RuntimeError('Approved candidate roots differ from strict whitelist')
    process=scan();pins=config_pins();rows=[];skips=[];root_states=[]
    open_inodes={tuple(x) for x in process['inode_refs']}
    for kind,roots in ROOTS.items():
        for root in roots:
            reason=root_reason(kind,root,process,pins)
            if reason:skips.append({'path':root,'reason':reason});continue
            chain=safe_chain(root);files,syms=file_rows(root);skips.extend(syms)
            sessions=blocked_sessions(root,process) if kind=='app_logs' else {}
            root_states.append({'kind':kind,'root':root,'chain':chain})
            for p in files:
                s=p.lstat();reason=None
                if s.st_nlink!=1:reason='multiple hardlinks'
                elif (s.st_dev,s.st_ino) in open_inodes or str(p) in process['path_refs']:reason='open or mapped file'
                elif any(under(str(p),session) for session in sessions):reason='retained '+next(v for k,v in sessions.items() if under(str(p),k))
                elif '.trash' in p.relative_to(root).parts:reason='download trash staging'
                elif kind=='vscode_vsix' and time.time()-max(s.st_mtime,s.st_ctime)<48*3600:reason='recent download (<48h)'
                elif kind in ['browser_cache','other_caches'] and time.time()-max(s.st_mtime,s.st_ctime)<24*3600:reason='recent cache (<24h)'
                if reason:skips.append({'path':str(p),'reason':reason,'allocated_bytes':s.st_blocks*512});continue
                rows.append({'path':str(p),'root':root,'kind':kind,'metadata':metadata(s),'parents':safe_chain(str(p.parent))})
    result={'created':time.time(),'proposal':str(PROPOSAL),'proposal_sha256':sha(PROPOSAL),'policy_roots':ROOTS,'files':rows,'roots':root_states,'skips':skips,'configuration_pins':pins,'protection':initial_protection(),'allocated_bytes':sum(x['metadata']['allocated_bytes'] for x in rows),'count':len(rows)}
    write(out('.manifest.json'),result);write(out('.process-prepare.json'),process)
    digest=sha(out('.manifest.json'));out('.manifest.sha256').write_text(digest+'\n')
    print(json.dumps({'manifest':str(out('.manifest.json')),'sha256':digest,'files':len(rows),'bytes':result['allocated_bytes'],'skips':len(skips),'groups':dict(collections.Counter({k:sum(x['metadata']['allocated_bytes'] for x in rows if x['kind']==k) for k in ROOTS}))},indent=2))
def load_verified(digest):
    if not digest or sha(out('.manifest.json'))!=digest:raise RuntimeError('Explicit manifest SHA mismatch')
    m=json.loads(out('.manifest.json').read_text())
    if m['policy_roots']!=ROOTS or sha(PROPOSAL)!=m['proposal_sha256']:raise RuntimeError('Proposal/whitelist changed')
    for row in m['files']:
        if row['root'] not in ROOTS.get(row['kind'],[]) or not under(row['path'],row['root']):raise RuntimeError('File outside whitelist')
    return m
def unlink_checked(row):
    # Open each parent with O_NOFOLLOW. Unlink relative to the held parent descriptor.
    fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        expected={x['path']:x for x in row['parents']}; cur=''
        for part in Path(row['path']).parent.parts[1:]:
            new=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=new;cur+='/'+part
            s=os.fstat(fd);e=expected[cur]
            if (s.st_dev,s.st_ino)!=(e['dev'],e['ino']):return 'parent identity changed'
        name=Path(row['path']).name;s=os.stat(name,dir_fd=fd,follow_symlinks=False)
        if not stat.S_ISREG(s.st_mode) or metadata(s)!=row['metadata']:return 'file metadata changed'
        os.unlink(name,dir_fd=fd);return None
    finally:os.close(fd)
def apply(digest):
    m=load_verified(digest)
    if out('.execution.json').exists():raise RuntimeError('Execution record already exists')
    execution={'manifest_sha256':digest,'started':time.time(),'deleted':[],'skipped':[],'complete':False}
    write(out('.execution.json'),execution)
    for rootstate in m['roots']:
        process=scan();kind=rootstate['kind'];root=rootstate['root'];reason=root_reason(kind,root,process,config_pins())
        if not reason:
            for x in rootstate['chain']:
                try:s=Path(x['path']).lstat()
                except FileNotFoundError:reason='candidate path absent';break
                if stat.S_ISLNK(s.st_mode) or (s.st_dev,s.st_ino)!=(x['dev'],x['ino']):reason='candidate parent/root identity changed';break
        rows=[x for x in m['files'] if x['root']==root]
        open_inodes={tuple(x) for x in process['inode_refs']}
        sessions=blocked_sessions(root,process) if not reason and kind=='app_logs' else {}
        for row in rows:
            skip=reason
            if not skip and ((row['metadata']['dev'],row['metadata']['ino']) in open_inodes or row['path'] in process['path_refs']):skip='open at execution preflight'
            if not skip and any(under(row['path'],session) for session in sessions):skip='current/recent session at execution'
            if not skip:
                try:skip=unlink_checked(row)
                except (FileNotFoundError,NotADirectoryError):skip='path changed or absent'
            if skip:execution['skipped'].append({'path':row['path'],'reason':skip})
            else:execution['deleted'].append({'path':row['path'],'allocated_bytes':row['metadata']['allocated_bytes']})
        write(out('.execution.json'),execution)
        write(out('.process-last.json'),process)
    execution.update(complete=True,finished=time.time(),deleted_bytes=sum(x['allocated_bytes'] for x in execution['deleted']))
    write(out('.execution.json'),execution);print(json.dumps({'deleted':len(execution['deleted']),'bytes':execution['deleted_bytes'],'skipped':len(execution['skipped'])}))
def verify(digest):
    m=load_verified(digest);e=json.loads(out('.execution.json').read_text());remaining=[];missing_protected=[];changed_protected=[]
    for row in e['deleted']:
        if os.path.lexists(row['path']):remaining.append(row['path'])
    for row in m['protection']:
        p=Path(row['path'])
        if not os.path.lexists(p):missing_protected.append(str(p));continue
        s=p.lstat()
        if (s.st_dev,s.st_ino)!=(row['metadata']['dev'],row['metadata']['ino']):changed_protected.append(str(p))
        if p.is_symlink() and os.readlink(p)!=row['target']:changed_protected.append(str(p))
    result={'complete':e['complete'],'deleted_count':len(e['deleted']),'deleted_bytes':e.get('deleted_bytes'),'deleted_paths_still_exist':remaining,'protected_missing':missing_protected,'protected_identity_changes':changed_protected,'scope':'Protected top-level identities and symlink targets; active app contents may change independently.'}
    write(out('.validation.json'),result);print(json.dumps(result,indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','apply','verify']);parser.add_argument('--manifest-sha');args=parser.parse_args()
    if args.mode=='prepare':prepare()
    elif args.mode=='apply':apply(args.manifest_sha)
    else:verify(args.manifest_sha)
