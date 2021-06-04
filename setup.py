from pathlib import Path

from setuptools import find_packages, setup

from video_composer import __title__

setup(
    name='video-composer',
    version='2.1.0',
    description=__title__,
    long_description=(Path(__file__).parent / 'README.md').read_text(),
    url='https://github.com/jakubvalenta/video-composer',
    author='Jakub Valenta',
    author_email='jakub@jakubvalenta.cz',
    license='Apache Software License',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Utilities',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
    ],
    packages=find_packages(),
    install_requires=['listio', 'moviepy'],
    entry_points={
        'console_scripts': ['video-composer=video_composer.cli:main']
    },
)
