#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from setuptools import find_packages, setup


required_packages=[
    "nipype==1.8.5", "networkx==2.8.7"]

verstr = "unknown"
try:
    verstrline = open('fetpype/_version.py', "rt").read()
except EnvironmentError:
    pass # Okay, there is no version file.
else:
    VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
    mo = re.search(VSRE, verstrline, re.M)
    if mo:
        verstr = mo.group(1)
    else:
        raise RuntimeError("unable to find version in yourpackage/_version.py")

print("Will not build conda module")

setup(
    name="fetpype",
    version=verstr,
    packages=find_packages(),
    author="fetpype team",
    description="Pipeline for anatomic processing for macaque",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    license='BSD 3',
    entry_points = {
        'console_scripts': ['pipeline_fet = workflows.pipeline_fet:main']},
    install_requires= required_packages,
    include_package_data=True)
