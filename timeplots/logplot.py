#!/usr/bin/env python3

"""
logplot.py

Usage:
  logplot.py [options] [-e=<regex>...] <dateformat> [<filename>...]
  logplot.py -h | --help
  logplot.py --version

Options:
  -h --help                         Show this screen.
  --version                         Show version.
  -e=<regex>                        Pattern to match.
  -i, --interval=<interval>[m|h|d]  Sample interval in seconds with optional
                                    suffix to denote minutes, hours, or days.
  -o, --output=<filename>           Output filename [default: logplot.html].
  -t, --title=<title>               Title for plot [default: Events over Time].
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


def get_interval(interval):
    if not interval:
        return "events", {}
    interval = f"{interval}s" if interval.isnumeric() else interval
    value, units = interval[:-1], interval[-1]
    units = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}.get(units)
    if not units or not value.isnumeric():
        raise ValueError("Invalid interval specified.")
    units, interval = f"events every {value} {units}", {units: int(value)}
    if value == "1":
        units = units[:-1]
    return units, interval


def main():
    args = docopt(__doc__)
    print(args)

    title = args.get("--title")
    output_filename = args.get("--output")
    units, interval = get_interval(args.get("--interval"))

    logtime = timeplots.LogTime(pattern=args.get("<dateformat>"), **interval)
    lines = (line for line in FileInput(args.get("<filename>")))

    plotter = timeplots.Plotter(width=1400)
    plotter.new_plot(title=title, units=units)

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

    plotter.render(filename=output_filename, title=title)


if __name__ == "__main__":
    sys.exit(main())
