#!/usr/bin/env python

from distutils.core import setup

# FIXME version number, etc.
setup(
    name = 'dds-harvest',
    version = '0.1.0',
    license = '',
    description = 'Digital Display Harvest Server',
    long_description = 'Digital Display Harvest Server',
    author = 'Alex Lee',
    author_email = 'lee@ccs.neu.edu',
    maintainer = 'Alex Lee',
    maintainer_email = 'lee@ccs.neu.edu',
    url = 'http://crew-git.ccs.neu.edu/bugs/projects/harvest',
    download_url = '',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Education',
    ],
    platforms = ['linux'],
    scripts = ['scripts/dds-server'],
    packages = ['harvest'],
    data_files = [('/etc', ['cfg/dds-server.conf']),
        ('/etc/init.d', ['cfg/harvest'])]
)
