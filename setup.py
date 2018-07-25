from codecs import open
from os import path

from setuptools import find_packages, setup

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='video_composer',

    version='1.0.1',

    description='Video composer.',
    long_description=long_description,

    url='https://lab.saloun.cz/jakub/video-composer',

    author='Jakub Valenta',
    author_email='jakub@jakubvalenta.cz',

    license='Apache Software License',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Artistic Software',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
    ],

    keywords='',

    packages=find_packages(),

    install_requires=[
        'moviepy',
    ],

    entry_points={
        'console_scripts': [
            'video-composer=video_composer.video_composer:main',
        ],
    },
)
