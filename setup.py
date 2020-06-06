#!/usr/bin/env python3

"""
Timeplots: setup script.
"""

from setuptools import setup, find_packages

version = "0.2.0"

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

# install_requires = ["bokeh"]
# requirements = ["bokeh"]

setup_requirements = ["pytest-runner"]

test_requirements = ["pytest>=3"]

setup(
    author="Greg Mueller",
    author_email="greg@grelleum.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Bokeh wrapper for creating time based line plots.",
    # install_requires=requirements,
    install_requires=["bokeh"],
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="timeplots",
    name="timeplots",
    packages=find_packages(include=["timeplots", "timeplots.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/grelleum/timeplots",
    version=version,
    zip_safe=False,
)
