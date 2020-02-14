#!/opt/support/python37/bin/python3

# coding: utf-8

from collections import defaultdict
from datetime import datetime
from glob import glob

import os
import re
import sys

from bokeh import layouts, models, plotting


global x_range
x_range = None


def main():

    filename = sys.argv[1] if sys.argv[1:] else choose_file()
    with open(filename, "rt") as fh:
        lines = [line.rstrip() for line in fh.readlines()]

    datapoints = defaultdict(list)
    for measurement, *values in get_datapoints(lines):
        datapoints[measurement].append(values)

    title = f"pps_plot-{filename}"
    output_filename = title + ".html"

    sample_values = next(v for v in datapoints.values())
    timestamps = [t[0] for t in sample_values]
    start, *_, end = timestamps
    timeframe = f"{start.strftime('%Y%m%d.%H%M%S')} - {end.strftime('%Y%m%d.%H%M%S')}"

    header = f"""<html><h2>{title}</h2><h2>{timeframe}</h2></html>"""
    header = models.widgets.Div(text=header)

    plotting.output_file(output_filename, title=title, mode="inline")
    plots = list(get_all_plots(datapoints))
    plotting.save(layouts.column(header, *plots))

    # output name of the file containing the plots.
    cwd = os.path.realpath(os.getcwd())
    if cwd.startswith("/mnt/support/data/"):
        filepath = os.path.join(cwd, output_filename)
        output_link = filepath.replace("/mnt/support/", "http://support.nbttech.com/")
        # try:
        #     os.chmod(output_filename, 0o666)
        # except PermissionError:
        #     pass
    else:
        output_link = output_filename
    print(f"Ouput saved to:\n{output_link}")


def choose_file():
    files = list(find_files())
    if files:
        print("Found the following 'pps' files in the current folder.")
        for index, filename in enumerate(files, 1):
            print(index, filename)
        while True:
            choice = input("\nWhich file should I open? ")
            if choice in files:
                return choice
            try:
                return files[int(choice) - 1]
            except (IndexError, ValueError):
                print("Invalid choice!")


def find_files():
    for filename in glob("*pps*"):
        with open(filename, "rt", encoding="latin-1") as fh:
            for line in (line.rstrip() for line in fh):
                if get_timestamp(line):
                    yield filename
                    break


def get_timestamp(line):
    """Inspect a line and return a datetime object or None."""

    try:
        words = line.split()
        timestamp = " ".join((*words[1:4], words[5]))
    except IndexError:
        return

    try:
        timestamp = datetime.strptime(timestamp, "%b %d %H:%M:%S %Y:")
    except ValueError:
        return

    return timestamp


def get_numeric(text):
    """Split text and return first numberic value as an interger."""
    values = text.split()
    numbers = [n for n in values if n.isnumeric()]
    if numbers:
        return int(numbers[0])


def get_datapoints(lines):
    """Traverse lines and yield data."""

    trx = re.compile(r" ?[TR]X ?")
    measures = ("pkts/s", "kB/s", "PktLen")

    for line in lines:

        timestamp = get_timestamp(line)
        if not timestamp:
            continue

        _, TX, RX = trx.split(line)

        measurement = [m for m in measures if m in TX][0]
        TX = get_numeric(TX)
        RX = get_numeric(RX)

        yield measurement, timestamp, TX, RX


def make_multiline_plot(title, timestamps, rx, tx, width=1200, height=400):
    """Creates a single line plot for the data provided."""

    print(f"Generating plots for {title}")

    global x_range

    data_type = "pps" if title.endswith("packets per second") else "Value"
    data_type = "bps" if title.endswith("bits per second") else data_type

    hover = models.HoverTool(
        mode="mouse",  # other optins: vline
        line_policy="nearest",  # other optins: prev, next, nearest, interp, none
        tooltips=[
            ("Name", "@legend"),
            ("Time", "@x{%a %m/%d %H:%M:%S}"),
            (data_type, "@y{0,0}"),
        ],
        formatters={"x": "datetime"},
    )

    plot = plotting.figure(title=title, tools=[])

    if x_range is None:
        x_range = plot.x_range
    else:
        plot.x_range = x_range

    plot.line(timestamps, rx, line_width=1, color="blue", name="rx", legend_label="rx")
    plot.line(timestamps, tx, line_width=1, color="green", name="tx", legend_label="tx")

    plot.plot_width = width
    plot.plot_height = height
    plot.legend.click_policy = "hide"  # other optins: mute
    # plot.xaxis.formatter = models.DatetimeTickFormatter()
    datetime_tick_formats = {
        key: ["%a %b %d %H:%M:%S"]
        for key in ("seconds", "minsec", "minutes", "hourmin", "hours", "days")
    }
    plot.xaxis.formatter = models.DatetimeTickFormatter(**datetime_tick_formats)
    plot.yaxis.formatter = models.NumeralTickFormatter(format="0a")
    plot.add_tools(hover)
    plot.add_tools(models.BoxZoomTool())
    plot.add_tools(models.HelpTool())
    plot.add_tools(models.PanTool())
    plot.add_tools(models.ResetTool())
    plot.add_tools(models.SaveTool())
    plot.add_tools(models.WheelZoomTool(dimensions="width"))
    plot.toolbar.active_scroll = plot.select_one(models.WheelZoomTool)

    return plot


def get_all_plots(datapoints):
    for key in datapoints:
        timestamps, tx, rx = zip(*datapoints[key])
        yield make_multiline_plot(key, timestamps, rx, tx, width=1500)


if __name__ == "__main__":
    main()
