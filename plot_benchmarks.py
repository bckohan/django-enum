#!/usr/bin/env python3
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import json


BENCHMARKS = Path(__file__).parent / 'benchmarks.json'


def plot_size(size_benchmarks):

    plt.figure(figsize=(10, 6))
    plt.title('Number of Bytes Saved per Row by Using a Mask')
    plt.xlabel('Number of Flags')
    plt.ylabel('Bytes / Row')

    # color different x-ranges
    plt.axvspan(1, 15, color='#D8DDEF', alpha=0.75)
    plt.axvspan(15, 31, color='#A0A4B8', alpha=0.75)
    plt.axvspan(31, 63, color='#7293A0', alpha=0.75)
    # plt.axvspan(63, 127, color='#45B69C', alpha=0.75)

    # create patches for the legend
    small_int = mpatches.Patch(
        color='#D8DDEF', alpha=0.75, label='Small Int'
    )
    int = mpatches.Patch(
        color='#A0A4B8', alpha=0.75, label='Integer'
    )
    big_int = mpatches.Patch(
        color='#7293A0', alpha=0.75, label='Big Integer'
    )
    # extra_big_int = mpatches.Patch(
    #     color='#45B69C', alpha=0.75, label='Big Integer'
    # )

    count = size_benchmarks.pop('count', None)
    if not count:
        raise ValueError('No count found in benchmarks')

    num_flags = []
    for vendor, metrics in size_benchmarks.items():

        num_flags = []
        bytes_saved = []

        for idx, (bools, flags) in enumerate(zip(
            metrics['bools']['table'],
            metrics['flags']['table']
        )):
            num_flags.append(idx+1)
            bytes_saved.append((bools - flags) / count)

        plt.plot(num_flags, bytes_saved, label=vendor)

    # save the plot as a .png file
    plt.xlim(min(num_flags), max(num_flags))
    # add legend to the plot
    plt.legend(handles=[
        small_int,
        int,
        big_int,
        #extra_big_int,
        *plt.gca().get_lines()
    ])

    plt.savefig('FlagSizeBenchmark.png')
    plt.show()


if __name__ == '__main__':

    if BENCHMARKS.is_file():
        with open(BENCHMARKS, 'r') as bf:
            benchmarks = json.load(bf) or {}

        if 'size' in benchmarks:
            plot_size(benchmarks['size'])
    else:
        print('No benchmarks found - run benchmarks tests first')
