from setuptools import setup, find_packages

setup(
    name="CryptoMasterPro",
    version="0.1",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'cryptomaster = main:main',
        ],
    },
)