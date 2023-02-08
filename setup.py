from setuptools import setup

setup(
    name="FileGenerator",
    version="0.0.1",
    author="Mohammad Mohsen",
    author_email="kuro.ece@gmail.com",
    packages=[],
    scripts=[],
    url="https://github.com/ece-mohammad/FileGenerator",
    license="LICENSE",
    description="Generate files (text, C, C++, etc) with optional boilerplate, according to a template file",
    long_description=open("README.md").read(),
    install_requires=[
    ],
    entry_points = {
        "console_scripts": [
            "GenerateFiles=GenerateFiles:main"
        ]
    }
)