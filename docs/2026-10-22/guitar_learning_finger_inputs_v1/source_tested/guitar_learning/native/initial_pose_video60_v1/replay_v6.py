"""Native saved-joint-motion visualization, with no integration or interpolation."""

import argparse

import gzip

import hashlib

import json

import math

import re

import subprocess

import sys

import xml.etree.ElementTree as ET

from pathlib import Path

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')

def pose_difference(saved, actual):
    p = [saved['p'][key] - actual['p'][key] for key in 'xyz']
    a = [saved['r'][key] for key in 'xyzw']
    b = [actual['r'][key] for key in 'xyzw']
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    if not na or not nb or not all(math.isfinite(x) for x in p + a + b):
        raise ValueError('finite positions and nonzero finite quaternion norms required')
    a, b = [x / na for x in a], [x / nb for x in b]
    distance = min(math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b))),
                   math.sqrt(sum((x + y) ** 2 for x, y in zip(a, b))))
    angle = 4 * math.asin(min(1., distance / 2))
    return math.sqrt(sum(x * x for x in p)), angle

