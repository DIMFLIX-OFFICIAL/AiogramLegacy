from setuptools import setup, find_packages

setup(
    name='Aiogram Legacy',
    author='DIMFLIX',
    description='💖 A library to simplify the daily development of bots on aiogram ',
    version='1.0.0',

    author_email='dimflix.official@gmail.com',
    package_dir={'': 'AiogramLegacy'},
    packages=find_packages(
        'AiogramLegacy',
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
