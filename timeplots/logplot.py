#!/usr/bin/env python3

"""
logplot.py

Usage:
  logplot.py [options] [-e=<regex>...] <strptime> [<filename>...]
  logplot.py -h | --help
  logplot.py --version

Options:
  -h --help            Show this screen.
  --version            Show version.
  -e=<regex>           Pattern to match.
  --hours=<hours>      Hours [default: 0].
  --minutes=<minutes>  Minutes [default: 0].
  --seconds=<seconds>  Seconds [default: 0].
"""

from collections import Counter, defaultdict, deque
from datetime import datetime, timedelta
from functools import lru_cache
from fileinput import FileInput
import re
import sys

from docopt import docopt

import timeplots


class LogTime(object):
    def __init__(self, *, pattern, delimiter=" ", hours=0, minutes=0, seconds=0):
        """
        Creates an object that produces datetime objects.
        strptime: str: strptime pattern for decoding embedded timestamp.
        hours: int: used to group timestamp by hour.
        minutes: int: used to group timestamp by minutes.
        seconds: int: used to group timestamp by seconds.
        """
        self.pattern = pattern
        self.pattern_size = len(pattern.split())
        self.delimiter = delimiter
        delta = timedelta(hours=hours, minutes=minutes, seconds=seconds)
        self.delta = int(delta.total_seconds())

    @lru_cache()
    def _strptime(self, text):
        timestamp = datetime.strptime(text, self.pattern)
        if self.delta:
            big_delta = timestamp - datetime.min
            total_seconds = int(big_delta.total_seconds())
            mod = timedelta(seconds=total_seconds % self.delta)
            timestamp = timestamp - mod
        return timestamp

    @lru_cache()
    def strptime(self, text):
        words = text.split(self.delimiter)
        words = words[: self.pattern_size]
        text = " ".join(words)
        # print("***", text, flush=True, end="\t")
        timestamp = self._strptime(text)
        return timestamp


def match_any_lines(logtime, lines):
    for line in lines:
        try:
            timestamp = logtime.strptime(line)
        except ValueError as e:
            print(repr(e), file=sys.stderr)
        else:
            print(">>>", timestamp, end="\r", flush=True)
            yield timestamp


def match_lines(logtime, lines, expressions):
    expressions = [(exp, re.compile(exp)) for exp in expressions]
    for line in lines:
        for expression, regex in expressions:
            if regex.search(line):
                try:
                    timestamp = logtime.strptime(line)
                except ValueError as e:
                    print(repr(e), file=sys.stderr)
                else:
                    print(">>>", timestamp, end="\r", flush=True)
                    yield expression, timestamp


def main():
    args = docopt(__doc__)
    print(args)

    logtime = LogTime(
        pattern=args.get("<strptime>"),
        hours=int(args.get("--hours")),
        minutes=int(args.get("--minutes")),
        seconds=int(args.get("--seconds")),
    )

    lines = (line for line in FileInput(args.get("<filename>")))

    plotter = timeplots.Plotter(width=1400)
    plotter.new_plot("Stuff happening", "stuff/day")

    if args.get("-e"):
        buckets = defaultdict(deque)
        for expression, timestamp in match_lines(logtime, lines, args.get("-e")):
            buckets[expression].append(timestamp)
        for expression, times in buckets.items():
            c = Counter(times)
            times, data = zip(*sorted(c.items()))
            plotter.add_line(expression, times, data)
    else:
        c = Counter(match_any_lines(logtime, lines))
        times, data = zip(*sorted(c.items()))
        plotter.add_line("values", times, data)

    plotter.render(filename="testplots.html", title="testplots")


if __name__ == "__main__":
    sys.exit(main())
