#!/usr/bin/env python3
import json
import re
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

BENCHMARKS = Path(__file__).parent / "benchmarks.json"


QUERY_RE = re.compile(r"\[(?P<column>FLAG|BOOL)\] (?P<index>.*)")

PLOT_DIR = Path(__file__).parent  # / 'doc' / 'source' / 'plots'


def parse_plt(plt_str):
    mtch = QUERY_RE.match(plt_str)
    if not mtch:
        raise ValueError(f"Could not parse plot string: {plt_str}")
    return mtch.groups()


def plot_size(size_benchmarks):
    plt.figure(figsize=(10, 6))
    plt.title("Number of Bytes Saved per Row by Using a Mask")
    plt.xlabel("Number of Flags")
    plt.ylabel("Bytes / Row")

    # color different x-ranges
    plt.axvspan(1, 15, color="#D8DDEF", alpha=0.75)
    plt.axvspan(15, 31, color="#A0A4B8", alpha=0.75)
    plt.axvspan(31, 63, color="#7293A0", alpha=0.75)
    # plt.axvspan(63, 127, color='#45B69C', alpha=0.75)

    # create patches for the legend
    small_int = mpatches.Patch(color="#D8DDEF", alpha=0.75, label="Small Int")
    int = mpatches.Patch(color="#A0A4B8", alpha=0.75, label="Integer")
    big_int = mpatches.Patch(color="#7293A0", alpha=0.75, label="Big Integer")
    # extra_big_int = mpatches.Patch(
    #     color='#45B69C', alpha=0.75, label='Big Integer'
    # )

    count = size_benchmarks.pop("count", None)
    if not count:
        raise ValueError("No count found in benchmarks")

    num_flags = []
    for vendor, metrics in size_benchmarks.items():
        num_flags = []
        bytes_saved = []

        for idx, (bools, flags) in enumerate(
            zip(metrics["bools"]["table"], metrics["flags"]["table"])
        ):
            num_flags.append(idx + 1)
            bytes_saved.append((bools - flags) / count)

        plt.plot(num_flags, bytes_saved, label=vendor)

        if metrics["bools"].get("column", []) and metrics["flags"].get("column", []):
            num_flags = []
            bytes_saved = []

            for idx, (bools, flags) in enumerate(
                zip(metrics["bools"]["column"], metrics["flags"]["column"])
            ):
                num_flags.append(idx + 1)
                bytes_saved.append((bools - flags) / count)

            plt.plot(num_flags, bytes_saved, label=f"{vendor} (column)")

    # save the plot as a .png file
    plt.xlim(min(num_flags), max(num_flags))
    # add legend to the plot
    plt.legend(
        handles=[
            small_int,
            int,
            big_int,
            # extra_big_int,
            *plt.gca().get_lines(),
        ]
    )

    plt.savefig(str(PLOT_DIR / "FlagSizeBenchmark.png"))


def plot_queries(queries):
    plt.figure(figsize=(10, 6))
    plt.title("Number of Bytes Saved per Row by Using a Mask")
    plt.xlabel("Number of Flags")
    plt.ylabel("Bytes / Row")

    lines = [("all_time", "has_all"), ("any_time", "has_any"), ("exact_time", "exact")]

    for vendor, indexes in queries.items():
        plt.figure(figsize=(10, 6))
        plt.title("Query Performance [{}]".format(vendor))
        plt.xlabel("Table Rows")
        plt.ylabel("Query Seconds")
        count_min = None
        count_max = None

        for index, num_flags in indexes.items():
            if "No Index" in index:
                continue
            for num_flag, counts in num_flags.items():
                cnts = list(sorted((int(cnt) for cnt in counts.keys())))
                count_min = cnts[0] if count_min is None else min(cnts[0], count_min)
                count_max = cnts[-1] if count_max is None else max(cnts[-1], count_max)

                plts = {}
                for key, label in lines:
                    plts[label] = []

                for count in cnts:
                    metrics = counts[str(count)]
                    for key, label in lines:
                        if key in metrics:
                            plts[label].append(metrics[key])

                for label, plt_data in plts.items():
                    plt.plot(
                        cnts,
                        plt_data,
                        "--" if "BOOL" in index else "-",
                        label=f"[{index}] ({label})",
                    )

        # save the plot as a .png file
        plt.xlim(count_min, count_max)
        # plt.xscale("log")

        # add legend to the plot
        plt.legend(handles=[*plt.gca().get_lines()])

        plt.savefig(str(PLOT_DIR / f"QueryPerformance_{vendor}.png"))
        plt.show()


def plot_no_index_comparison(queries, rdbms="postgres", num_flags=16):
    lines = [
        ("all_time", "has_all", "r"),
        ("any_time", "has_any", "g"),
        ("exact_time", "exact", "b"),
    ]

    plots = queries.get(rdbms, {})
    bool_no_index = None
    flags_no_index = None
    for plot, flag_metrics in plots.items():
        parsed = parse_plt(plot)
        if parsed == ("BOOL", "No Index"):
            bool_no_index = flag_metrics.get(str(num_flags), {})
        if parsed == ("FLAG", "No Index"):
            flags_no_index = flag_metrics.get(str(num_flags), {})

    if not (bool_no_index and flags_no_index):
        raise ValueError(f'No "No Index data" found for {rdbms}: {num_flags} flags')

    plt.figure(figsize=(10, 6))
    plt.title(f"No Index [{rdbms}, num_flags={num_flags}]")
    plt.xlabel("Table Rows")
    plt.ylabel("Query Seconds")

    count_min = None
    count_max = None

    for label, counts, style in [
        ("BOOL", bool_no_index, "--"),
        ("FLAG", flags_no_index, "-"),
    ]:
        cnts = list(sorted((int(cnt) for cnt in counts.keys())))
        count_min = cnts[0] if count_min is None else min(cnts[0], count_min)
        count_max = cnts[-1] if count_max is None else max(cnts[-1], count_max)

        plts = {}
        for key, qry, color in lines:
            plts[qry] = ([], color)

        for count in cnts:
            metrics = counts[str(count)]
            for key, qry, color in lines:
                if key in metrics:
                    plts[qry][0].append(metrics[key])

        for qry, plt_data in plts.items():
            plt.plot(
                cnts, plt_data[0], f"{plt_data[1]}{style}", label=f"[{label}] {qry}"
            )

    # save the plot as a .png file
    plt.xlim(count_min, count_max)
    # plt.xscale("log")

    # add legend to the plot
    plt.legend(handles=[*plt.gca().get_lines()])
    plt.savefig(str(PLOT_DIR / f"NoIndexQueryPerformance_{rdbms}.png"))
    plt.show()


def plot_exact_index_comparison(queries, rdbms="postgres", num_flags=16):
    lines = [("exact_time", "exact", "b"), ("table_size", "table_size", "r")]

    plots = queries.get(rdbms, {})
    bool_no_index = None
    flags_no_index = None
    for plot, flag_metrics in plots.items():
        parsed = parse_plt(plot)
        if parsed == ("BOOL", "MultiCol Index"):
            bool_no_index = flag_metrics.get(str(num_flags), {})
        if parsed == ("FLAG", "Single Index"):
            flags_no_index = flag_metrics.get(str(num_flags), {})

    if not (bool_no_index and flags_no_index):
        raise ValueError(f'No "Exact Query" data found for {rdbms}: {num_flags} flags')

    fig, ax = plt.subplots(figsize=(10, 6))
    size_plt = ax.twinx()

    plt.title(f"Indexed - Exact Queries [{rdbms}, num_flags={num_flags}]")
    ax.set_xlabel("Table Rows")
    ax.set_ylabel("Query Seconds")
    size_plt.set_ylabel("Table Size (GB)")

    count_min = None
    count_max = None

    handles = []

    for label, counts, style in [
        ("BOOL", bool_no_index, "--"),
        ("FLAG", flags_no_index, "-"),
    ]:
        cnts = list(sorted((int(cnt) for cnt in counts.keys())))
        count_min = cnts[0] if count_min is None else min(cnts[0], count_min)
        count_max = cnts[-1] if count_max is None else max(cnts[-1], count_max)

        plts = {}
        for key, qry, color in lines:
            plts[qry] = ([], color)

        for count in cnts:
            metrics = counts[str(count)]
            for key, qry, color in lines:
                if key in metrics:
                    plts[qry][0].append(
                        metrics[key] / (1024**3)
                        if qry == "table_size"
                        else metrics[key]
                    )

        for qry, plt_data in plts.items():
            axis = ax
            if qry == "table_size":
                axis = size_plt
            handles.append(
                axis.plot(
                    cnts, plt_data[0], f"{plt_data[1]}{style}", label=f"[{label}] {qry}"
                )[0]
            )

    # save the plot as a .png file
    ax.set_xlim(count_min, count_max)
    # plt.xscale("log")

    # add legend to the plot
    ax.legend(handles=handles)
    plt.savefig(str(PLOT_DIR / f"IndexedExactQueryPerformance_{rdbms}.png"))
    plt.show()


def plot_any_all_index_comparison(queries, rdbms="postgres", num_flags=16):
    lines = [
        ("all_time", "has_all", "g"),
        ("any_time", "has_any", "b"),
        ("table_size", "table_size", "r"),
    ]

    plots = queries.get(rdbms, {})
    bool_multiindex = None
    bool_colindex = None
    flags_singleidx = None
    flags_noidx = None
    for plot, flag_metrics in plots.items():
        parsed = parse_plt(plot)
        if parsed == ("BOOL", "MultiCol Index"):
            bool_multiindex = flag_metrics.get(str(num_flags), {})
        if parsed == ("BOOL", "Col Index"):
            bool_colindex = flag_metrics.get(str(num_flags), {})
        if parsed == ("FLAG", "Single Index"):  # todo change this to multi col
            flags_singleidx = flag_metrics.get(str(num_flags), {})
        if parsed == ("FLAG", "No Index"):  # todo change this to multi col
            flags_noidx = flag_metrics.get(str(num_flags), {})

    if not (bool_multiindex and flags_singleidx):
        raise ValueError(f'No "Exact Query" data found for {rdbms}: {num_flags} flags')

    fig, ax = plt.subplots(figsize=(10, 6))
    size_plt = ax.twinx()

    plt.title(f"Indexed - Any/All Queries [{rdbms}, num_flags={num_flags}]")
    ax.set_xlabel("Table Rows")
    ax.set_ylabel("Query Seconds")
    size_plt.set_ylabel("Table Size (GB)")

    count_min = None
    count_max = None

    handles = []

    for label, counts, style in [
        ("BOOL MultiCol Index", bool_multiindex, "--"),
        # ('BOOL Col Index', bool_colindex, '-.'),
        ("FLAG Single Index", flags_singleidx, "-"),
        ("FLAG No Index", flags_singleidx, "-."),
    ]:
        cnts = list(sorted((int(cnt) for cnt in counts.keys())))
        count_min = cnts[0] if count_min is None else min(cnts[0], count_min)
        count_max = cnts[-1] if count_max is None else max(cnts[-1], count_max)

        plts = {}
        for key, qry, color in lines:
            plts[qry] = ([], color)

        for count in cnts:
            metrics = counts[str(count)]
            for key, qry, color in lines:
                if key in metrics:
                    plts[qry][0].append(
                        metrics[key] / (1024**3)
                        if qry == "table_size"
                        else metrics[key]
                    )

        for qry, plt_data in plts.items():
            axis = ax
            if qry == "table_size":
                axis = size_plt
            handles.append(
                axis.plot(
                    cnts, plt_data[0], f"{plt_data[1]}{style}", label=f"[{label}] {qry}"
                )[0]
            )

    # save the plot as a .png file
    ax.set_xlim(count_min, count_max)
    # plt.xscale("log")

    # add legend to the plot
    ax.legend(handles=handles)
    plt.savefig(str(PLOT_DIR / f"IndexedAnyAllQueryPerformance_{rdbms}.png"))
    plt.show()


def plot_table_sizes(queries, rdbms="postgres", num_flags=16):
    lines = [("table_size", "table_size", "r")]

    plots = queries.get(rdbms, {})
    lines = []
    for plot, metrics in plots.items():
        parsed = parse_plt(plot)

        index_color = {
            "No Index": "g",
            # comparable - service the same queries
            "MultiCol Index": "b",
            "Single Index": "b",
            "Col Index": "r",
        }.get(parsed[1], "b")

        if not index_color:
            continue

        lines.append(
            (
                " ".join(parsed),
                metrics.get(str(num_flags), {}),
                f'{index_color}{"--" if parsed[0] == "BOOL" else "-"}',
            )
        )

    if not lines:
        raise ValueError(f"No table size data found for {rdbms}: {num_flags} flags")

    plt.figure(figsize=(10, 6))
    plt.title(f"Table+Index Size [{rdbms}, num_flags={num_flags}]")
    plt.xlabel("Table Rows")
    plt.ylabel("Size (GB)")

    count_min = None
    count_max = None

    for label, counts, style in lines:
        cnts = list(sorted((int(cnt) for cnt in counts.keys())))
        count_min = cnts[0] if count_min is None else min(cnts[0], count_min)
        count_max = cnts[-1] if count_max is None else max(cnts[-1], count_max)

        data = []
        for count in cnts:
            metrics = counts[str(count)]
            if "table_size" in metrics:
                data.append(metrics["table_size"] / (1024**3))

        plt.plot(cnts, data, style, label=label)

    # save the plot as a .png file
    plt.xlim(count_min, count_max)

    # add legend to the plot
    plt.legend(handles=[*plt.gca().get_lines()])
    plt.savefig(str(PLOT_DIR / f"TableSize_{rdbms}.png"))
    plt.show()


if __name__ == "__main__":
    if BENCHMARKS.is_file():
        with open(BENCHMARKS, "r") as bf:
            benchmarks = json.load(bf) or {}

        if "size" in benchmarks:
            plot_size(benchmarks["size"])

        if "queries" in benchmarks:
            plot_queries(benchmarks["queries"])
            for rdbms in ["postgres", "mysql", "sqlite", "oracle"]:
                try:
                    plot_no_index_comparison(benchmarks["queries"], rdbms=rdbms)
                except ValueError:
                    print("No data for No Index plot. Skipping...")
                    continue

            for rdbms in ["postgres", "mysql", "sqlite", "oracle"]:
                try:
                    plot_exact_index_comparison(benchmarks["queries"], rdbms=rdbms)
                except ValueError:
                    print("No data for Exact comparison plot. Skipping...")
                    continue

            for rdbms in ["postgres", "mysql", "sqlite", "oracle"]:
                try:
                    plot_any_all_index_comparison(benchmarks["queries"], rdbms=rdbms)
                except ValueError:
                    print("No data for Any/All comparison plot. Skipping...")
                    continue

            for rdbms in ["postgres", "mysql", "sqlite", "oracle"]:
                try:
                    plot_table_sizes(benchmarks["queries"], rdbms=rdbms)
                except ValueError:
                    print("No data for table size comparison plot. Skipping...")
                    continue
    else:
        print("No benchmarks found - run benchmarks tests first")
