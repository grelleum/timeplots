# -*- coding: utf-8 -*-

"""Provide version information when imported on command line."""

import sys
import timeplots


if __name__ == "__main__":
    line = "{:14} {:>8}"
    python_version = ".".join(str(x) for x in sys.version_info[:3])
    print(line.format("Python", python_version))
    print(line.format("Timeplots", timeplots.version))
