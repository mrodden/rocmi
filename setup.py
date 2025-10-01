from setuptools import setup, find_packages


with open("README.md", "r", encoding="utf8") as fd:
    long_desc = fd.read()


setup(
    name="rocmi",
    version="0.3.1",
    author="Mathew Odden",
    author_email="matodden@amd.com",
    url="https://github.com/mrodden/rocmi",
    description="Pure Python implementation of ROCm metircs and management interfaces",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=find_packages(
        where="src",
    ),
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.6",
    extras_require={
        "cli": [
            "prettytable>=2",
        ],
    },
    entry_points={
        "console_scripts": [
            "rocmi = rocmi.cli:main [cli]",
        ],
    },
)
