"""
    Support function for loading test datasets
"""
import os
import os.path as op

import shutil


def make_tmp_dir():
    tmp_dir = "/tmp/test_fetpype"
    if op.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir)
    os.chdir(tmp_dir)

    return tmp_dir
