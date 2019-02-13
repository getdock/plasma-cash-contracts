#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
    Sample py-solc based compilation for Dock's Plasma Cash contracts with complete_json output
    split into iniovodual json files suitable for deployment. For a more fine-grained approach,
    use standard_json in/output specifications.

    Requires solc verion 0.4.24

'''
import json
import os
import sys
from typing import List

from solc import compile_files, get_solc_version  # pylint: disable=E0012

assert sys.version.startswith('3.7'), 'Require python 3.7 or better'  # isort:skip

SOLC_VERSION = '0.4.24'
solc_version = str(get_solc_version())
assert solc_version.startswith(SOLC_VERSION), f'Solc version {SOLC_VERSION} ir required but got {solc_version}.'

CTR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'source'))
JSN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'json'))
if not os.path.exists(JSN_DIR):
    os.mkdir(JSN_DIR)


def compile_to_json(ctr_paths: List, out_dir: str, complete_out: bool) -> bool:
    '''
        Compile the target sol file, split the respective json key segments
        into destination files corresponding to source file name.
    '''
    # err_msg = 'Invalid or missing path: {}'
    # assert os.path.exists(ctr_path), err_msg.format(ctr_path)

    d_complete = compile_files(ctr_paths, optimize=True)

    if complete_out:
        out_path = os.path.join(out_dir, 'complete.json')
        assert not os.path.exists(out_path), f'File {out_path} already exists.'
        with open(out_path, 'w') as fd:
            json.dump(d_complete, fd)

    for k, v in d_complete.items():
        out_path = os.path.join(out_dir, k.split('sol:')[1] + '.json')
        assert not os.path.exists(out_path), f'File {out_path} already exists.'
        with open(out_path, 'w') as fd:
            json.dump(v, fd)

    return True


if __name__ == '__main__':

    ctr_paths = [os.path.join(CTR_DIR, 'PlasmaContract.sol'), os.path.join(CTR_DIR, 'ERC20DockToken.sol')]
    complete_json = False
    assert compile_to_json(ctr_paths, JSN_DIR, complete_json)
