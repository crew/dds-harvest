#!/usr/bin/env python

from distutils.core import setup

# FIXME version number, etc.
setup(
    name = 'dds-server',
    description = 'Digital Display Jabber Server',
    version = '0.0.1',
    author = 'Alex Lee',
    author_email = 'lee@ccs.neu.edu',
    maintainer = 'Alex Lee',
    maintainer_email = 'lee@ccs.neu.edu',
    #url = '',
    scripts = ['scripts/dds-server'],
    py_modules = ['gflags'],
    packages = ['dds_server'],
    package_dir = {'' : 'lib'},
    data_files = [('/etc', ['cfg/dds-server.conf']),],
)
