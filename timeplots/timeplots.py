"""Main module."""

#!/opt/support/python37/bin/python3

# -*- coding: latin-1 -*-


from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path

import gzip
import os
import re
import sys

from bokeh import layouts, models, plotting


class Plotter(object):
    """
    Usage:
    plotter = Plotter()
    plotter.new_plot("Interface Eth0 Packets Per Second", "pps")
    plotter.add_line("rx", timestamps, rx_data)
    plotter.add_line("tx", timestamps, tx_data)

    """

    x_range = plotting.Figure.x_range
    width = 1400
    height = 400

    def __init__(self, width=None, height=None):
        self.width = self.width if width is None else width
        self.height = self.height if height is None else height
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
        self.colors = ["red", "green", "blue"]
        self.units = units

        plot.plot_width = self.width
        plot.plot_height = self.height

        datetime_tick_formats = {
            key: ["%a %b %d %H:%M:%S"]
            for key in ("seconds", "minsec", "minutes", "hourmin", "hours", "days")
        }
        plot.xaxis.formatter = models.DatetimeTickFormatter(**datetime_tick_formats)

    def _finalize(self, plot):

        """
        Adds the finishing touches to a plot.
        """

        # https://bokeh.pydata.org/en/latest/docs/reference/models/formatters.html
        plot.yaxis.formatter = models.NumeralTickFormatter(format="0a")

        # Legend click policy must be defined after a legend is added.
        self.active_plot.legend.click_policy = "hide"  # other optins: mute

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
        plot.add_tools(models.ResetTool())
        plot.add_tools(models.SaveTool())
        plot.add_tools(models.WheelZoomTool(dimensions="width"))
        plot.toolbar.active_scroll = plot.select_one(models.WheelZoomTool)

    def add_line(self, name, timestamps, data, color=None):
        """Add a line to the active plot."""
        try:
            self.active_plot.line(
                timestamps,
                data,
                line_width=1,
                color="blue",
                name=name,
                legend_label=name,
            )
        except AttributeError:
            print(
                "Error: You must create a 'new_plot' before adding a line.",
                file=sys.stderr,
            )

    def render(self, *, filename=None, title=None):
        """Display the plots or write to file."""

        for plot in self.plots:
            self._finalize(plot)

        if filename is None:
            plotting.output_notebook()
            plotting.show(layouts.column(*self.plots))

        else:
            title = "" if title is None else title
            plotting.output_file(filename, title=title, mode="inline")
            print(f"Writing file '{filename}'")
            plotting.save(layouts.column(*self.plots))


# class Plotter(object):
#     """
#     Usage:
#     plotter = Plotter()
#     plotter.new_plot("Interface Eth0 Packets Per Second", "pps")
#     plotter.add_line("rx", timestamps, rx_data)
#     plotter.add_line("tx", timestamps, tx_data)

#     """

#     x_range = plotting.Figure.x_range
#     width = 1400
#     height = 400

#     def __init__(self, width=None, height=None):
#         self.width = self.width if width is None else width
#         self.height = self.height if height is None else height
#         self.plots = []
#         self.active_plot = None

#     # def plot(self, title, timestamps, *plotlines):
#     def new_plot(self, title, units):

#         """
#         Creates a blank line plot for with timestamps on the x-axis and
#         a line for each data series on the y-axis.
#         """

#         hover = models.HoverTool(
#             mode="mouse",  # other optins: vline
#             line_policy="nearest",  # other optins: prev, next, nearest, interp, none
#             tooltips=[("Time", "@x{%a %m/%d %H:%M:%S}"), (units, "@y{0,0}")],
#             formatters={"x": "datetime"},
#         )

#         plot = plotting.figure(title=title, tools=[])
#         self.active_plot = plot
#         self.plots.append(plot)
#         self.colors = ["red", "green", "blue"]

#         plot.plot_width = self.width
#         plot.plot_height = self.height

#         datetime_tick_formats = {
#             key: ["%a %b %d %H:%M:%S"]
#             for key in ("seconds", "minsec", "minutes", "hourmin", "hours", "days")
#         }
#         plot.xaxis.formatter = models.DatetimeTickFormatter(**datetime_tick_formats)

#         plot.yaxis.formatter = models.NumeralTickFormatter(format="0a")
#         # https://bokeh.pydata.org/en/latest/docs/reference/models/formatters.html

#         plot.add_tools(hover)
#         plot.add_tools(models.BoxZoomTool())
#         plot.add_tools(models.HelpTool())
#         plot.add_tools(models.PanTool())
#         plot.add_tools(models.ResetTool())
#         plot.add_tools(models.SaveTool())
#         plot.add_tools(models.WheelZoomTool(dimensions="width"))
#         plot.toolbar.active_scroll = plot.select_one(models.WheelZoomTool)

#     def add_line(self, name, timestamps, data, color=None):
#         """Add a line to the active plot."""
#         try:
#             self.active_plot.line(
#                 timestamps,
#                 data,
#                 line_width=1,
#                 color="blue",
#                 name=name,
#                 legend_label=name,
#             )
#             # Legend click policy must be defined after a legend is added.
#             self.active_plot.legend.click_policy = "hide"  # other optins: mute
#         except AttributeError:
#             print(
#                 "Error: You must create a 'new_plot' before adding a line.",
#                 file=sys.stderr,
#             )

#     def render(self, *, filename=None, title=None):
#         """Display the plots or write to file."""

#         if filename is None:
#             plotting.output_notebook()
#             plotting.show(layouts.column(*self.plots))

#         else:
#             title = "" if title is None else title
#             plotting.output_file(filename, title=title, mode="inline")
#             print(f"Writing file '{filename}'")
#             plotting.save(layouts.column(*self.plots))
