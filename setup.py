"""Setup configuration for JuaKazi."""
from setuptools import setup, find_packages

setup(
    name="juakazi",
    version="0.1.0",
    packages=find_packages(include=['eval', 'eval.*', 'api', 'api.*', 'ui', 'ui.*', 'ml', 'ml.*', 'scripts', 'scripts.*']),
    python_requires=">=3.12",
    install_requires=[
        "tqdm>=4.67.1",
    ],
)
