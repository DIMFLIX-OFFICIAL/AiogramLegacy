from setuptools import setup, find_packages

setup(
    name='Aiogram Legacy',
    author='DIMFLIX',
    description='💖 A library to simplify the daily development of bots on aiogram ',
    version='1.0.0',

    package_dir={'': 'src'},
    packages=find_packages(
        'src',
        include=['storages*', 'questioning*'],
    ),
    install_requires=[
        'aiogram==3.0.0b7',
        'aiomysql',
        'asyncpg',
        'aiosqlite',
        'jsonpickle'
    ],
)
