from setuptools import setup

setup(
    name='Behavior Sequences',
    version='1.0',
    packages=[''],
    url='',
    license='',
    author='Isabelle Baker',
    author_email='ibaker@umich.edu',
    description='User Interface and BackEnd code for finding behavior sequences within LabGym output excel files.',
    install_requires=[
        'numpy>=1.26.1',
        'openpyxl>=3.1.2',
        'pandas>=2.1.1',
        'wxPython>=4.2.1', ]
)