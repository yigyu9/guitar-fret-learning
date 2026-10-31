"""Candidate joint observation: physical core, source skill blocks, joint history."""
import numpy as np

BLOCKS=(('physical_core',548),('source_fret_v2',420),('source_strike_v2',303),('joint_music_diagnostic',28))


def compose_observation(physical,fret,strike,joint):
    values=[];manifest=[];offset=0
    for (name,size),value in zip(BLOCKS,(physical,fret,strike,joint)):
        value=np.asarray(value,dtype=np.float32)
        if value.shape!=(size,) or not np.isfinite(value).all():raise ValueError('invalid observation block: '+name)
        manifest.append({'name':name,'offset':offset,'length':size,'dtype':'float32'})
        values.append(value);offset+=size
    return np.concatenate(values),manifest
