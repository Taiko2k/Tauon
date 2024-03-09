from setuptools import setup, find_packages, Extension

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name = 'Tauon Music Box',
    packages = find_packages(),
    version = '7.7.2',
    url = 'https://tauonmusicbox.rocks/',
    license = 'GPL-3',
    install_requires=required,
	classifiers=[
		'Programming Language :: Python :: 3'
	],
)
