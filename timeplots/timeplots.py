#!/opt/support/python37/bin/python3
# -*- coding: latin-1 -*-

"""Provide tools for plotting time based line graphs."""

# from collections import defaultdict, deque
# from pathlib import Path

# import gzip
# import os
# import re

from datetime import datetime, timedelta
from functools import lru_cache
import sys

from bokeh import layouts, models, plotting, palettes


class Plotter(object):
    """
    Usage:
    plotter = Plotter()
    plotter.new_plot("Interface Eth0 Packets Per Second", "pps")
    plotter.add_line("rx", timestamps, rx_data)
    plotter.add_line("tx", timestamps, tx_data)

    """

    x_range = plotting.Figure.x_range

    def __init__(self, width=1400, height=400):
        self.width = width
        self.height = height
        self.plots = []
        self.active_plot = None

    def new_plot(self, title, units):
        """
        Creates a blank line plot for with timestamps on the x-axis and
        a line for each data series on the y-axis.
        """

        plot = plotting.figure(title=title, tools=[])
        self.active_plot = plot
        self.plots.append(plot)
        self.colors = list(reversed(palettes.colorblind["Colorblind"][8]))
        self.units = units

        plot.plot_width = self.width
        plot.plot_height = self.height

        datetime_tick_formats = {
            key: ["%a %b %d %H:%M:%S"]
            for key in ("seconds", "minsec", "minutes", "hourmin", "hours", "days")
        }
        plot.xaxis.formatter = models.DatetimeTickFormatter(**datetime_tick_formats)

        # https://bokeh.pydata.org/en/latest/docs/reference/models/formatters.html
        plot.yaxis.formatter = models.NumeralTickFormatter(format="0a")

        hover = models.HoverTool(
            mode="mouse",  # other optins: vline
            line_policy="nearest",  # other optins: prev, next, nearest, interp, none
            tooltips=[("Time", "@x{%a %m/%d %H:%M:%S}"), (self.units, "@y{0,0}")],
            formatters={"x": "datetime"},
        )
        plot.add_tools(hover)

        plot.add_tools(models.BoxZoomTool())
        plot.add_tools(models.HelpTool())
        plot.add_tools(models.PanTool())
        plot.add_tools(models.WheelZoomTool(dimensions="width"))
        plot.toolbar.active_scroll = plot.select_one(models.WheelZoomTool)
        plot.add_tools(models.WheelZoomTool(dimensions="height"))
        plot.add_tools(models.UndoTool())
        plot.add_tools(models.RedoTool())
        plot.add_tools(models.ResetTool())
        plot.add_tools(models.SaveTool())

    def add_line(self, name, timestamps, data, color=None):
        """Add a line to the active plot."""

        if self.active_plot is None:
            error = "Error: You must create a 'new_plot' before adding a line."
            print(error, file=sys.stderr)

        color = color or self.colors.pop()

        self.active_plot.line(
            timestamps, data, line_width=1, color=color, name=name, legend_label=name
        )

        # Legend click policy must be defined after a legend is added.
        self.active_plot.legend.click_policy = "hide"  # other optins: mute
        self.active_plot.legend.location = "top_left"

    def render(self, *, filename=None, title=""):
        """Display the plots or write to file."""

        if filename is None:
            plotting.output_notebook()
            plotting.show(layouts.column(*self.plots))

        else:
            plotting.output_file(filename, title=title, mode="inline")
            print(f"Writing file '{filename}'")
            plotting.save(layouts.column(*self.plots))


class LogTime(object):
    def __init__(self, *, date_format, delimiter=" ", hours=0, minutes=0, seconds=0):
        """
        Creates an object that produces datetime objects.
        date_format: str: strptime format for decoding embedded timestamp.
        hours: int: used to group timestamp by hour.
        minutes: int: used to group timestamp by minutes.
        seconds: int: used to group timestamp by seconds.
        """
        self.date_format = date_format
        self.date_format_length = len(date_format.split())
        self.delimiter = delimiter
        delta = timedelta(hours=hours, minutes=minutes, seconds=seconds)
        self.delta = int(delta.total_seconds())

    @lru_cache()
    def _strptime(self, text):
        """
        Private function to get strptime from text,
        and truncate to specific period if self.delta is set.
        """
        timestamp = datetime.strptime(text, self.date_format)
        if self.delta:
            big_delta = timestamp - datetime.min
            total_seconds = int(big_delta.total_seconds())
            mod = timedelta(seconds=total_seconds % self.delta)
            timestamp = timestamp - mod
        return timestamp

    @lru_cache()
    def strptime(self, text):
        """
        Return a datetime object from begining of string object.
        Will ignore end portion of string that does not contain
        the date/time information.
        """
        words = text.split(self.delimiter)
        words = words[: self.date_format_length]
        text = " ".join(words)
        timestamp = self._strptime(text)
        return timestamp


def missing_time_data(timestamps, data, *, default=0):
    """
    Fill in missing times with a default value, usually zero.

    timestamps is a sequence of times in the datetime format.
    data is a sequence of values matching those timestamps.
    default is a value that will be added to the output sequence
      when an expected timestamp is missing.

    Example Input:
        timestamps = [8:00, 9:00, 12:00]  # pretend they are datetime.
        data = [17, 5, 21]
    Example Output:
        timestamps = [8:00, 9:00, 10:00, 11:00, 12:00]
        data = [17, 5, 0, 0, 21]

    This assumes the smallest delta between any two timestamps
    is the period over which we should always see data.

    For example, if we have two data points that are one minute apart
    we expect that we should have a data point every one minute.

    Assuming not all data points will be on the mark,
    we allow up to a 50% skew on the next timestamp,
    before providing a value.
    """

    # Find the lowest period between timestamps.
    minimum_delta = min(
        after - before for after, before in zip(timestamps[1:], timestamps)
    )

    # Make generators from the input data
    timestamps = (t for t in timestamps)
    data = (d for d in data)

    # Get and yield the initial values.
    previous = next(timestamps)
    value = next(data)
    yield previous, value

    # Next expected timestamp and allowable skew.
    expected = previous + minimum_delta
    upper_limit = previous + minimum_delta * 1.5

    for time, value in zip(timestamps, data):
        # Inner loop to return default values if missing times.
        while time > upper_limit:
            yield expected, default
            previous = expected
            expected = previous + minimum_delta
            upper_limit = previous + minimum_delta * 1.5

        yield time, value
        previous = time
        expected = previous + minimum_delta
        upper_limit = previous + minimum_delta * 1.5
