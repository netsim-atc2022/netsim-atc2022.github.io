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
    with open("phase1.json", 'r') as inf:
        db.insert_multiple(json.load(inf))

    set_plot_options(grid='both')
    
    # the ones we might want in the paper
    plot_phase1_metric(db, 'skewed', 'perf_duration-time-sec', ylabel="Benchmark Time (s)",
        yscale='log', ymin=None, yticks=[50, 100, 500, 1000], bbox=(0.1, 1))
    plot_phase1_metric(db, 'skewed', 'seconds_to_init', ylabel="Initialization Time (s)",
        ymax=8, bbox=(0.1, 1))

    plot_phase1_metric(db, 'skewed', 'perf_branch-misses', 
        ncol=3, ymax=2*10**10, ylabel="Branch Misses")
    plot_phase1_metric(db, 'skewed', 'perf_page-faults', 
        ncol=3, ymax=2.5*10**6, ylabel="Page Faults")

    # all of the results for analysis
    plot_all_phase1_metrics(db, 'uniform')
    plot_all_phase1_metrics(db, 'skewed')

def plot_all_phase1_metrics(db, ew):
    metric_keys = select(db, ew='skewed', im='ptrace', nw=35, usp=True).keys()
    for metric_key in metric_keys:
        plot_phase1_metric(db, ew, metric_key, 
            title=ew, ylabel=metric_key.replace('_', '-'), dir='phase1_metrics')

def plot_phase1_metric(db, ew, metric_key, 
        title=None, ncol=1, dir=None,
        ylabel=None, ylabel_ralign=False, yscale=None, ymin=0, ymax=None, yticks=None, bbox=None):
    names = ['only ptrace', 'preload+ptrace', 'only seccomp', 'preload+seccomp', 'uni-process']
    colors = ['C0', 'C1', 'C2', 'C3', 'C4']
    formats = ['o-', '^-', 's-', 'v-', '*-']

    methods = [('ptrace', False), ('ptrace', True), ('seccomp', False), ('seccomp', True), ('classic', None)]

    x_threads = [7, 14, 21, 28, 35, 42, 49, 56]

    pyplot.figure()

    for i, (im, usp) in enumerate(methods):
        y_vals, y_errs = [], []

        for nw in x_threads:
            result = select(db, ew=ew, im=im, nw=nw, usp=usp)
            m, e = compute_mean_and_error(result[metric_key])
            y_vals.append(m)
            y_errs.append(e)

        pyplot.errorbar(x_threads, y_vals, yerr=y_errs,
            label=names[i], color=colors[i], fmt=formats[i],
            capsize=3.0, linewidth=1.0)

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
    pyplot.xlabel('Logical Processors Count')

    if title != None:
        pyplot.title(title)

    if bbox != None:
        pyplot.legend(ncol=ncol, loc='upper left', bbox_to_anchor=bbox)
    else:
        pyplot.legend(ncol=ncol)
    pyplot.tight_layout(pad=0.3)

    filename = f"phold-phase1-{metric_key.replace('_', '-')}-{ew}.pdf"
    if dir != None:
        os.makedirs(dir, exist_ok = True)
        filename = os.path.join(dir, filename)
    pyplot.savefig(filename)

def select(db, ew, im, nw, usp):
    exp = Query()

    records = db.search(
        (exp.exe.msgload == 100) &
        (exp.exe.quantity == 1000) &
        (exp.exe.weights == ew) &
        (exp.interpose_method == im) &
        (exp.num_workers == nw) &
        (exp.scheduling_policy == 'host') &
        (exp.use_memory_manager == (None if im == 'classic' else True)) &
        (exp.use_pinning == True) &
        (exp.use_realtime == False) &
        (exp.use_syscall_preloading == (None if im == 'classic' else usp))
    )

    #print(json.dumps(records, sort_keys=True, indent=2))
    assert len(records) == 1
    return records[0]['~results']

if __name__ == "__main__":
    sys.exit(main())