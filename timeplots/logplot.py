#!/usr/bin/env python3

from datetime import datetime
from fileinput import FileInput

import sys

import timeplots

pattern = sys.argv[1]

for line in FileInput(sys.argv[2:]):
    try:
        timestamp = timeplots.strptime(line, pattern)
    except ValueError:
        pass
    else:
        print(">>>", repr(timestamp))

