#!/usr/bin/env python3

from setuptools import setup

setup(name='m2mtool',
      version='1.0',
      description='Run m2mtool.',
      author='Jon Wedell',
      author_email='wedell@bmrb.wisc.edu',
      url='https://devel.nmrbox.org/svn/nmrbox/trunk/software/m2mtool',
      packages=['m2mtool'],
      package_data={'m2mtool': ['file_selector/*.ui', 'config.json']},
      entry_points={
          'console_scripts':
              [
                  'm2mtool = m2mtool.__main__:run_m2mtool',
              ]
      }
      )
