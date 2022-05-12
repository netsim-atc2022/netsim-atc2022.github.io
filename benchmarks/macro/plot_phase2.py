import sys
import os
import json

import matplotlib
matplotlib.use('Agg') # for systems without X11
import matplotlib.pyplot as pyplot

from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage

from plot_common import *

def main():
    db = TinyDB(storage=MemoryStorage)
    with open("phase2.json", 'r') as inf:
        db.insert_multiple(json.load(inf))
    
    set_plot_options()
    plot_phase2_cpusched_barchart(db)

    set_plot_options(grid='both')

    # duration-time
    # cpu migrations
    # maybe show cache-misses, context switches, and branch misses in a table for the threads=28 case
    plot_phase2_metric(db, 'perf_duration-time-sec', 
        ylabel="Benchmark Time (s)")

    
    # all of the results for analysis
    plot_all_phase2_metrics(db)

def plot_all_phase2_metrics(db):
    metric_keys = select(db, im='ptrace', nw=14, up=True, ur=True).keys()
    for metric_key in metric_keys:
        plot_phase2_metric(db,metric_key, title=True,
            ylabel=metric_key.replace('_', '-'), dir='phase2_metrics')

def plot_phase2_metric(db, metric_key, 
        title=None, ncol=1, dir=None,
        ylabel=None, ylabel_ralign=False, yscale=None, ymin=0, ymax=None, yticks=None):

    names = ['standard', 'pin+standard', 'realtime', 'pin+realtime']
    cpu_modes = [(False, False), (True, False), (False, True), (True, True)]
    colors = ['C0', 'C1', 'C2', 'C3']
    formats = ['o-', '^-', 's-', '*-']

    methods = ['ptrace', 'seccomp', 'classic']
    x_threads = [14, 28, 42, 56]

    for _, im in enumerate(methods):
        pyplot.figure()

        for i, (up, ur) in enumerate(cpu_modes):
            y_vals, y_errs = [], []

            for nw in x_threads:
                result = select(db, im=im, nw=nw, up=up, ur=ur)
                m, e = compute_mean_and_error(result[metric_key])
                y_vals.append(m)
                y_errs.append(e)

            pyplot.errorbar(x_threads, y_vals, yerr=y_errs,
                label=names[i], color=colors[i], fmt=formats[i],
                capsize=2.0, linewidth=1.0)

        pyplot.xticks(x_threads)
        if yticks != None:
            pyplot.yticks(yticks)

        if yscale != None:
            pyplot.yscale(yscale)
        if ymin != None:
            pyplot.ylim(ymin=ymin)
        if ymax != None:
            pyplot.ylim(ymax=ymax)
        if ylabel != None:
            if ylabel_ralign:
                pyplot.ylabel(ylabel, horizontalalignment='right', y=1.0)
            else:
                pyplot.ylabel(ylabel)
        pyplot.xlabel('Logical Processor Count')

        if title != None:
            pyplot.title(im)

        pyplot.legend(ncol=ncol)
        pyplot.tight_layout(pad=0.3)

        filename = f"phold-phase2-{metric_key.replace('_', '-')}-{im}.pdf"
        if dir != None:
            os.makedirs(dir, exist_ok = True)
            filename = os.path.join(dir, filename)
        pyplot.savefig(filename)

def plot_phase2_cpusched_barchart(db):
    pyplot.figure()

    pyplot.subplot(131)
    plot_phold_cpusched_helper(db, im='ptrace', title="ptrace", ylabel=True)
    pyplot.subplot(132)
    plot_phold_cpusched_helper(db, im='seccomp', title="seccomp")
    pyplot.subplot(133)
    plot_phold_cpusched_helper(db, im='classic', title="uni-process")

    pyplot.tight_layout(pad=0.3)
    pyplot.savefig('phold-phase2-cpusched-bar.pdf')

def plot_phold_cpusched_helper(db, im, title=None, ylabel=False):
    names = ['standard', 'pin+standard', 'realtime', 'pin+realtime']
    cpu_modes = [(False, False), (True, False), (False, True), (True, True)]
    colors = ['C0', 'C1', 'C2', 'C3']
    nw = 28

    vals, errs = [], []
    for _, (up, ur) in enumerate(cpu_modes):
        result = select(db, im=im, nw=nw, up=up, ur=ur)
        m, e = compute_mean_and_error(result['perf_duration-time-sec'])
        m = round(m, 2)
        vals.append(m)
        errs.append(e)

    rects = pyplot.bar(names, vals, yerr=errs, color=colors,
        capsize=3.0, error_kw={'linewidth': 1.0})
    pyplot.gca().bar_label(rects, label_type='edge', padding=1, fontsize=6)

    pyplot.xticks(rotation=COMMON_ROTATION, ha='right')
    pyplot.ylim(ymax=175)
    if ylabel:
        pyplot.ylabel("Benchmark Time (s)", horizontalalignment='right', y=1.0)
    if title != None:
        pyplot.title(title)

def select(db, im, nw, up, ur):
    exp = Query()

    records = db.search(
        (exp.exe.msgload == 100) &
        (exp.exe.quantity == 1000) &
        (exp.exe.weights == 'skewed') &
        (exp.interpose_method == im) &
        (exp.num_workers == nw) &
        (exp.scheduling_policy == 'host') &
        (exp.use_memory_manager == (None if im == 'classic' else True)) &
        (exp.use_pinning == up) &
        (exp.use_realtime == ur) &
        (exp.use_syscall_preloading == (None if im == 'classic' else True))
    )

    #print(json.dumps(records, sort_keys=True, indent=2))
    assert len(records) == 1
    return records[0]['~results']

if __name__ == "__main__":
    sys.exit(main())