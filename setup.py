# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

setup(
    name='keymaster',
    version='0.5.0',
    description='Simple and secure password manager',
    long_description=readme,
    url='https://github.com/moygit/keymaster',
    author='Moy Easwaran',
    author_email='moy.builder@gmail.com',
    license='GPLv3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Topic :: Security',
    ],
    keywords='password security',
    packages=find_packages(exclude=('tests', 'images')),
    setup_requires=['nose>=1.0'],   # run tests with python setup.py nosetests
    install_requires=['PyQt5', 'xdg'],
    entry_points={
        'console_scripts': [
            'keymaster=keymaster.cli.key_cli:main',
            'keymaster_qt=keymaster.ui.key_qt_main:main',
        ],
    },
)
