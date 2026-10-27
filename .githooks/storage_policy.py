#!/usr/bin/env python3
"""Refresh machine-local ignores for external-storage symlinks; never delete data."""
import json
import os
from pathlib import Path
import stat
import subprocess

BEGIN = '# BEGIN managed external-storage symlinks'
END = '# END managed external-storage symlinks'


def is_external_link_target(root, name, target):
    root = Path(root)
    target_path = Path(target)
    lexical = os.path.normpath(str(target_path if target_path.is_absolute() else root / Path(name).parent / target_path))
    prefixes = ('/media/', '/mnt/', '/run/media/')
    if lexical.startswith(prefixes):
        return True
    try:
        resolved = Path(lexical).resolve()
        if str(resolved).startswith(prefixes):
            return True
        info = resolved.stat()
        return (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)) and info.st_dev != root.stat().st_dev
    except (OSError, RuntimeError):
        return False


def git_path(root, name):
    raw = subprocess.check_output(['git', 'rev-parse', '--git-path', name], cwd=root, text=True).strip()
    path = Path(raw)
    return path if path.is_absolute() else root/path


def refresh(root):
    root = Path(root)
    record = git_path(root, 'external-storage-links.json')
    links = []
    def escaped(name):
        assert '\n' not in name and '\r' not in name, 'Unsupported newline in external link path'
        return '/' + ''.join('\\'+c if c in '\\*?[] ' else c for c in name)
    def scan(directory, may_collapse=True):
        patterns=[]; nonexternal=False; count_before=len(links)
        for entry in os.scandir(directory):
            path=Path(entry.path); name=path.relative_to(root).as_posix()
            if entry.is_symlink():
                if is_external_link_target(root,name,os.readlink(path)):
                    links.append(name);patterns.append(escaped(name))
                else:
                    nonexternal=True
            elif entry.is_dir(follow_symlinks=False):
                if entry.name in {'.git','__pycache__','node_modules','.venv','venv','related_work'} or 'archive' in entry.name.lower():
                    nonexternal=True
                    continue
                child_patterns,child_nonexternal=scan(path)
                patterns.extend(child_patterns);nonexternal |= child_nonexternal
            else:
                nonexternal=True
        if may_collapse and not nonexternal and len(links)>count_before:
            return [escaped(directory.relative_to(root).as_posix())+'/'],False
        return patterns,nonexternal
    patterns=[]
    for top in ['data','docs','guitar_learning','isaacgym','paper','tab2fingermapping','.githooks']:
        path=root/top
        if path.is_dir() and not path.is_symlink():
            rules,_=scan(path,may_collapse=False);patterns.extend(rules)
        elif path.is_symlink() and is_external_link_target(root,top,os.readlink(path)):
            links.append(top);patterns.append(escaped(top))
    exclude = git_path(root, 'info/exclude')
    before = exclude.read_text() if exclude.exists() else ''
    assert (BEGIN in before) == (END in before), 'Malformed managed exclude block'
    block = BEGIN+'\n'+'\n'.join(patterns)+'\n'+END+'\n'
    if BEGIN in before:
        start = before.index(BEGIN)
        stop = before.index(END, start)+len(END)
        after = before[:start]+block+before[stop:].lstrip('\r\n')
    else:
        after = before.rstrip()+'\n\n'+block
    exclude.parent.mkdir(parents=True, exist_ok=True)
    temp = exclude.with_name(exclude.name+'.storage-policy.tmp')
    temp.write_text(after)
    os.replace(temp, exclude)
    record.write_text(json.dumps({'schema':1,'paths':sorted(links),'patterns':patterns}, ensure_ascii=False))
    return links


if __name__ == '__main__':
    root = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip())
    print(json.dumps({'external_storage_links_ignored':len(refresh(root))}))
