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


def main():

    global x_range
    x_range = None

    # read files and parse out the data.
    input_filenames = get_input_filenames()
    input_filenames = sort_files(input_filenames)

    dumps = split_dumps(input_filenames)
    dumps = [get_dump_details(dump) for dump in dumps]

    timestamps = [dump.get("timestamp") for dump in dumps][1:]
    print(f"Number of sample times collected: {len(timestamps)}")

    if timeframe_is_discontiguous(timestamps):
        print("Files are discontiguous.")
        print("There should only be a one minute gap between samples.")
        print("Please specify only contiguous service core dump files.")
        sys.exit(1)

    interfaces_details = get_interfaces_details(dumps)
    del dumps

    interfaces_details = get_counter_diffs(interfaces_details)
    interfaces_details = convert_packet_per_second(interfaces_details)
    interfaces_details = convert_bits_per_second(interfaces_details)

    # generate an html page with interactive plots.
    try:
        start, *_, end = timestamps
    except ValueError:
        print("Files are missing 'periodic dump at' - not valid for plotting values.")
        return 1
    title = f"service_core-{start.strftime('%Y%m%d.%H%M%S')}-{end.strftime('%Y%m%d.%H%M%S')}"
    output_filename = title + ".html"
    period = f"{start.strftime('%a %b %d %H:%M:%S')} through {end.strftime('%a %b %d %H:%M:%S (%Y)')}"
    header = models.widgets.Div(
        text=f"""<html><h2>{period}</h2><h3>{os.getcwd()}</h3></html>"""
    )

    plotting.output_file(output_filename, title=title, mode="inline")
    plots = list(get_plots(interfaces_details, timestamps))
    print(f"Writing file '{output_filename}'")
    plotting.save(layouts.column(header, *plots))

    # In the case that the file already was created by different user,
    # the file should have correct permissions anyway.
    try:
        os.chmod(output_filename, 0o666)
    except PermissionError:
        pass

    # output name of the file containing the plots.
    cwd = os.path.realpath(os.getcwd())
    if cwd.startswith("/mnt/support/data/"):
        filepath = os.path.join(cwd, output_filename)
        output_link = filepath.replace("/mnt/support/", "http://support.nbttech.com/")
    else:
        output_link = output_filename
    print(f"Ouput saved to:\n{output_link}")


def get_input_filenames(folder="."):
    """
    Return a list of dump files,
    either supplied from command line args, or found in local folder.
    """
    # this was separated out because jupyter doesn't like the
    if len(sys.argv) > 1:
        if os.path.isdir(sys.argv[1]):
            os.chdir(sys.argv[1])
            return find_local_filenames(".")
        else:
            return sys.argv[1:]
    else:
        return find_local_filenames(folder)


def find_local_filenames(folder):
    """
    This was separated out to use in jupyter as jupyter has this sys.argv:
    0 /opt/support/python37/lib/python3.7/site-packages/ipykernel_launcher.py
    1 -f
    2 /usr/home/nfs/gmueller/.local/share/jupyter/runtime/kernel-c0c4d7be-f174-441d-b8a7-1ef81ecd11b4.json
    """
    input_filenames = Path(folder).glob("**/service_core_periodic_dump_port_5001.txt*")
    input_filenames = [str(fn) for fn in input_filenames]
    input_filenames = [fn for fn in input_filenames if "html" not in fn]
    input_filenames = sort_files(input_filenames)
    return input_filenames


def sort_files(input_filenames):
    """
    Get first timestamp from all files.
    Return a chronologically sorted list of files.
    """

    files = {}
    for filename in input_filenames:
        openfile = gzip.open if filename.endswith(".gz") else open
        try:
            with openfile(filename, "rt") as fh:
                for line in fh:
                    if line.startswith("periodic dump at "):
                        line = line.strip().replace("periodic dump at ", "")
                        timestamp = datetime.strptime(line, "%a %b %d %H:%M:%S %Y")
                        files[timestamp] = filename
                        break
        except PermissionError:
            print("Permissions Error: run permfix in case directory and try again.")
            sys.exit(1)

    filenames = sorted(files.items())
    filenames = [filename for timestamp, filename in filenames]
    return filenames


def read_files(filenames, encoding="latin-1"):
    """Return a filehandle for each provided filename."""
    for filename in filenames:
        print(f"Reading '{filename}'")
        file_open = gzip.open if filename.endswith(".gz") else open
        with file_open(filename, "rt", encoding=encoding) as file_handle:
            for line in file_handle:
                yield line.rstrip()


def timeframe_is_discontiguous(timestamps):
    max_gap = 300
    previous = None
    for ts in timestamps:
        if previous is None:
            previous = ts
            continue
        if ts - previous > timedelta(seconds=max_gap + 1):
            print(f"\nUnexpected gap greater than {max_gap} seconds found in timeline.")
            print(f"{previous}\t{ts}\t{ts - previous}")
            return True
        previous = ts


def split_dumps(filenames):
    """
    Splits the file by each timed dump.
    There will be two of these per timed dump, one of which is network activity.
    Returns a list of each dump that pertains to network activity.
    """
    lines = deque()
    for line in read_files(filenames):
        if line.startswith("periodic dump at "):
            data = "\n".join(lines)
            if "tx_packets" in data:
                yield data
            lines = deque()
        lines.append(line)


def get_dump_details(dump):
    knet_mapping = re.compile(r"name: \[(\w+)\], .*, port: \[(\w+)\],.*")
    data = {}
    iface_map = {}
    current_iface = None
    for line in dump.splitlines():
        if line.startswith("periodic dump at "):
            data["timestamp"] = datetime.strptime(
                line, "periodic dump at %a %b %d %H:%M:%S %Y"
            )
            continue
        if line.startswith("name: [knet"):
            mapped = knet_mapping.findall(line)
            if mapped:
                knet, actual = mapped[0]
                iface_map[knet] = actual
            continue
        if line.startswith("iface name: knet"):
            current_iface = line.split()[-1]
            if iface_map.get(current_iface):
                current_iface = f"{current_iface} ({iface_map.get(current_iface)})"
            continue
        if current_iface and line.startswith("rx_packets:"):
            details = line.split()
            keys = details[::2]
            keys = [key.replace("_", " ") for key in keys]
            keys = [key.replace("rx error:", "rx errors:") for key in keys]
            keys = [f"{current_iface}: {key[:-1]}" for key in keys]
            values = details[1::2]
            values = [int(value[1:-1]) for value in values]
            for key, value in zip(keys, values):
                data[key] = value
            current_iface = None
    return data


def get_interfaces_details(dumps):
    """Creates separate lists for each interface counter."""

    interfaces_details = defaultdict(list)

    for dump in dumps:
        for key, value in dump.items():
            if key == "timestamp":
                continue
            interfaces_details[key].append(value)

    return interfaces_details


def get_counter_diffs(interfaces_details):
    """Converts raw numbers to diff from previous value."""

    details = {}

    for key, values in interfaces_details.items():
        details[key] = [
            after - before if before <= after else 2 ** 32 - before + after
            for before, after in zip(values[:-1], values[1:])
        ]

    return details


def convert_packet_per_second(interfaces_details):
    """Replaces the 'packets' counter with a count of 'packets per second'."""

    details = {}

    for key, values in interfaces_details.items():
        if key.endswith(" packets"):
            key = key.replace("packets", "packets per second")
            details[key] = [v / 60 for v in values]
        else:
            details[key] = values

    return details


def convert_bits_per_second(interfaces_details):
    """Replaces the 'bytes' counter with a count of 'kilobits per second'."""

    bps = 60 // 8
    details = {}

    for key, values in interfaces_details.items():
        if key.endswith(" bytes"):
            key = key.replace("bytes", "bits per second")
            details[key] = [v / bps for v in values]
        else:
            details[key] = values

    return details


def get_plots(interfaces_details, timestamps):
    interfaces = set(key.split(":")[0] for key in interfaces_details.keys())
    for interface in sorted(interfaces):
        header = models.widgets.Div(text=f"""<html><hr/><h2>{interface}</h2></html>""")
        for counter in ["packets per second", "bits per second", "errors", "dropped"]:
            title = f"{interface}: {counter}"
            rx = interfaces_details[f"{interface}: rx {counter}"]
            tx = interfaces_details[f"{interface}: tx {counter}"]
            if any(rx) or any(tx):
                # Zero data plots will not be charted.
                if header:
                    yield header
                    header = None
                yield make_multiline_plot(title, timestamps, rx, tx)


def make_multiline_plot(title, timestamps, rx, tx, width=1400, height=400):
    """Creates a single line plot for the data provided."""

    global x_range

    print(f"Generating plots for {title}")

    data_type = "pps" if title.endswith("packets per second") else "Value"
    data_type = "bps" if title.endswith("bits per second") else data_type
    data_type = "kbps" if title.endswith("kbits per second") else data_type

    hover = models.HoverTool(
        mode="mouse",  # other optins: vline
        line_policy="nearest",  # other optins: prev, next, nearest, interp, none
        tooltips=[("Time", "@x{%a %m/%d %H:%M:%S}"), (data_type, "@y{0,0}")],
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

    datetime_tick_formats = {
        key: ["%a %b %d %H:%M:%S"]
        for key in ("seconds", "minsec", "minutes", "hourmin", "hours", "days")
    }
    plot.xaxis.formatter = models.DatetimeTickFormatter(**datetime_tick_formats)

    plot.yaxis.formatter = models.NumeralTickFormatter(format="0a")
    # https://bokeh.pydata.org/en/latest/docs/reference/models/formatters.html
    plot.add_tools(hover)
    plot.add_tools(models.BoxZoomTool())
    plot.add_tools(models.HelpTool())
    plot.add_tools(models.PanTool())
    plot.add_tools(models.ResetTool())
    plot.add_tools(models.SaveTool())
    plot.add_tools(models.WheelZoomTool(dimensions="width"))
    plot.toolbar.active_scroll = plot.select_one(models.WheelZoomTool)

    return plot


if __name__ == "__main__":
    sys.exit(main())
