from setuptools import setup, find_packages

setup(
    name="addpage",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pyyaml",
    ],
    entry_points={
        "console_scripts": [
            "addpage=addpage.cli:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A package to add new .qmd files to _quarto.yml",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/harlananelson/addpage",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
