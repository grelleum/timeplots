"""
bump_version.py

Change version number in this file and execute.
"""

import re

version = "0.2.2"
print('"version: {}"'.format(version))


py_regex = re.compile(r"version = \"\d+\.[\d\.]+[a-z]?\"")
py_replacement = 'version = "{}"'.format(version)


def bump_version_in_file(filename, regex, replacement):
    """Replace version number within a file."""
    with open(filename, "rt") as fh:
        contents = fh.read()
    contents = regex.sub(replacement, contents)
    with open(filename, "wt") as fh:
        fh.write(contents)


# bump_version_in_file("docs/index.rst", py_regex, py_replacement)
bump_version_in_file("README.rst", py_regex, py_replacement)
bump_version_in_file("setup.py", py_regex, py_replacement)
bump_version_in_file("timeplots/__init__.py", py_regex, py_replacement)
