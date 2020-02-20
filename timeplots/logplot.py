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
from fileinput import FileInput
import re
import sys

from docopt import docopt

import timeplots


def get_timestamp(logtime, text):
    try:
        timestamp = logtime.strptime(text)
    except ValueError as e:
        print(repr(e), file=sys.stderr)
    else:
        print(">>>", timestamp, end="\r", flush=True)
        return timestamp


def match_all(logtime, lines):
    for line in lines:
        yield get_timestamp(logtime, line)


def match_regex(logtime, lines, expressions):
    expressions = [(exp, re.compile(exp)) for exp in expressions]
    for line in lines:
        for expression, regex in expressions:
            if regex.search(line):
                yield expression, get_timestamp(logtime, line)


def main():
    args = docopt(__doc__)
    print(args)

    logtime = timplots.LogTime(
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
        for expression, timestamp in match_regex(logtime, lines, args.get("-e")):
            buckets[expression].append(timestamp)
        for expression, times in buckets.items():
            c = Counter(times)
            times, data = zip(*sorted(c.items()))
            times, data = zip(*timeplots.missing_time_data(times, data))
            plotter.add_line(expression, times, data)
    else:
        c = Counter(match_all(logtime, lines))
        times, data = zip(*sorted(c.items()))
        times, data = zip(*timeplots.missing_time_data(times, data))
        plotter.add_line("values", times, data)

    plotter.render(filename="testplots.html", title="testplots")


if __name__ == "__main__":
    sys.exit(main())
