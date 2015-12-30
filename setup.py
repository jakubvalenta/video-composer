from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='tv_series_tools',

    version='1.0.0',

    description='Tools to work with TV series\'s subtitles.',
    long_description=long_description,

    url='https://lab.saloun.cz/jakub/tv-series-tools',

    author='Jakub Valenta',
    author_email='jakub@jakubvalenta.cz',

    license='Apache Software License',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Artistic Software',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7',
    ],

    keywords='',

    packages=find_packages(),

    install_requires=[
        'requests',
        'imdbpy',
        'python-opensubtitles>=0.2.dev0',
        'pysrt',
        'termcolor',
        'moviepy',
    ],

    entry_points={
        'console_scripts': [
            'tv-series-download-subs=tv_series.download_subs:download_subs_and_cache_results',
            'tv-series-find-episode-ids=tv_series.find_episode_ids:find_and_write_episode_ids',
            'tv-series-search-subs=tv_series.search_subs:search_and_approve_subs',
            'tv-series-chech-approved-subs=tv_series.search_subs:check_approved_subs',
            'tv-series-print-approved-subs=tv_series.search_subs:print_approved_subs',
            'tv-series-video=tv_series.video:create_super_cut',
        ],
    },
)
