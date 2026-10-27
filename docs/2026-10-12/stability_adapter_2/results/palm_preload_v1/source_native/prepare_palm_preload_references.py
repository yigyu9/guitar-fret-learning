"""Build minimal verified invariants for length-only PALM_RATE trials."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit',type=Path,required=True)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('preserve prior expectations')
    audit = json.loads(args.audit.read_text())
    origin = args.baseline/'report.json'
    base = json.loads(origin.read_text())
    if not all(base['checks'].values()) or not audit['runtime_sources_unchanged']:
        raise ValueError('baseline or initial audit failed')
    for mapping in (base['source_sha256'],audit['source_sha256']):
        if not all(sha(p)==h for p,h in mapping.items()):
            raise ValueError('origin or initial audit sources differ')
    if any(base['source_sha256'][p]!=h for p,h in audit['source_sha256'].items()
           if p in base['source_sha256']):
        raise ValueError('origin/audit SHA maps conflict')
    inputs = dict(base['source_sha256'], **audit['source_sha256'])
    inputs.update({str(p.resolve()):sha(p) for p in (origin,args.audit,Path(__file__))})
    raw = {n:(args.baseline/(n+'.json')).resolve()
        for n in ('states','trace','controls','contacts','leg_torques')}
    inputs.update({str(p):sha(p) for p in raw.values()})
    if not all(sha(p)==h for p,h in inputs.items()):
        raise ValueError('reference sources differ')
    fields = ('arm_indices','human_joint_names','initial_joint_targets_rad','diagnostic_lower_rad',
        'diagnostic_upper_rad','physics_parameters','guitar_goal_position_m','guitar_goal_quaternion_xyzw')
    args.out.mkdir(parents=True)
    outputs, links = {}, {}
    for record in audit['records']:
        if not all(record['checks'].values()) or not record['accepted_for_diagnostic']:
            continue
        reference = {k:base[k] for k in fields}
        reference.update({'absolute_rest_length_m':record['settings']['strap_rest_length_m'],
            'checks':dict(record['checks'],accepted_initial_source=True,origin_reference_pass=True),
            'source_sha256':inputs,'reference_role':'expected initial/control invariants, not rollout results',
            'origin_report':str(origin.resolve()),'initial_audit_record':record['id']})
        folder = args.out/record['id'];folder.mkdir(parents=True)
        (folder/'report.json').write_text(json.dumps(reference,indent=2,allow_nan=False)+'\n')
        for name,path in raw.items():
            link = folder/(name+'.json')
            link.symlink_to(path)
            links[str(link.absolute())] = {
                'link_path':str(link.absolute()),'resolved_path':str(path),'sha256':sha(path)}
        outputs[record['id']] = str(folder.resolve())
    (args.out/'manifest.json').write_text(json.dumps({'input_sha256':inputs,'references':outputs,
        'raw_links':links},indent=2)+'\n')
    print(json.dumps(outputs,indent=2))


if __name__=='__main__':
    main()
