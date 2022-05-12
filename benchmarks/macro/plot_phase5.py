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
    with open("phase5.json", 'r') as inf:
        db.insert_multiple(json.load(inf))

    set_plot_options()
    plot_phase5_cpuload(db)
    plot_phase5_msgload(db)
    plot_phase5_weights(db)

    plot_all_phase5_metrics(db)

def plot_all_phase5_metrics(db):
    metric_keys = select(db, im='ptrace', ec=0, em=1, ew='skewed').keys()
    for metric_key in metric_keys:
        metric_label = metric_key.replace('_', '-')

        filename_cpu = f"phold-phase5-{metric_label}-cpuload.pdf"
        filename_msg = f"phold-phase5-{metric_label}-msgload.pdf"
        filename_wgt = f"phold-phase5-{metric_label}-weights.pdf"

        dir = 'phase5_metrics'
        if dir != None:
            os.makedirs(dir, exist_ok = True)
            filename_cpu = os.path.join(dir, filename_cpu)
            filename_msg = os.path.join(dir, filename_msg)
            filename_wgt = os.path.join(dir, filename_wgt)

        pyplot.figure()
        pyplot.subplot(141)
        plot_phase5_cpuload_helper(db, metric_key, ec=0, ylabel=metric_label)
        pyplot.subplot(142)
        plot_phase5_cpuload_helper(db, metric_key, ec=1)
        pyplot.subplot(143)
        plot_phase5_cpuload_helper(db, metric_key, ec=2)
        pyplot.subplot(144)
        plot_phase5_cpuload_helper(db, metric_key, ec=3)
        pyplot.tight_layout(pad=0.3)
        pyplot.savefig(filename_cpu)

        pyplot.figure()
        pyplot.subplot(141)
        plot_phase5_msgload_helper(db, metric_key, em=1, ylabel=metric_label)
        pyplot.subplot(142)
        plot_phase5_msgload_helper(db, metric_key, em=10)
        pyplot.subplot(143)
        plot_phase5_msgload_helper(db, metric_key, em=100)
        pyplot.subplot(144)
        plot_phase5_msgload_helper(db, metric_key, em=1000)
        pyplot.tight_layout(pad=0.3)
        pyplot.savefig(filename_msg)

        pyplot.figure()
        pyplot.subplot(131)
        plot_phase5_weights_helper(db, metric_key, ew='uniform', ylabel=metric_label)
        pyplot.subplot(132)
        plot_phase5_weights_helper(db, metric_key, ew='skewed')
        pyplot.subplot(133)
        plot_phase5_weights_helper(db, metric_key, ew='ring')
        pyplot.tight_layout(pad=0.3)
        pyplot.savefig(filename_wgt)

def plot_phase5_cpuload(db):
    metric_key = 'perf_duration-time-sec'

    pyplot.figure()

    pyplot.subplot(141)
    plot_phase5_cpuload_helper(db, metric_key, ec=0, ylabel="Benchmark Time (s)", ymax=375)
    pyplot.subplot(142)
    plot_phase5_cpuload_helper(db, metric_key, ec=1, ymax=375)
    pyplot.subplot(143)
    plot_phase5_cpuload_helper(db, metric_key, ec=2, ymax=375, val_round=0)
    pyplot.subplot(144)
    plot_phase5_cpuload_helper(db, metric_key, ec=3, ymax=375, val_round=0)

    pyplot.tight_layout(pad=0.3)
    pyplot.savefig('phold-phase5-cpuload-bar.pdf')

def plot_phase5_cpuload_helper(db, metric_key, ec, val_div=1, val_round=1, title=None, ymax=None, ylabel=None, yticks=None):
    names = ['ptrace', 'seccomp', 'uni-process']
    modes = ['ptrace', 'seccomp', 'classic']
    colors = ['C0', 'C1', 'C4']

    em = 100
    ew = 'skewed'

    vals, errs = [], []
    for _, im in enumerate(modes):
        result = select(db, im=im, ec=ec, em=em, ew=ew)
        m, e = compute_mean_and_error(result[metric_key])
        m /= val_div
        e /= val_div
        m = round(m, val_round)
        vals.append(m)
        errs.append(e)

    rects = pyplot.bar(names, vals, yerr=errs, color=colors,
        capsize=3.0, error_kw={'linewidth': 1.0})
    pyplot.gca().bar_label(rects, label_type='edge', padding=1, fontsize=6)

    if yticks != None:
        pyplot.yticks(yticks)
    if ymax != None:
        pyplot.ylim(ymax=ymax)
    if ylabel != None:
        pyplot.ylabel(ylabel)#, horizontalalignment='right', y=1.0)

    pyplot.xticks(rotation=COMMON_ROTATION, ha='right')
    pyplot.title(f'{ec} AES/msg')

def plot_phase5_msgload(db):
    metric_key = 'perf_duration-time-sec'

    pyplot.figure()

    pyplot.subplot(141)
    plot_phase5_msgload_helper(db, metric_key, em=1, ylabel="Benchmark Time (s)", ymax=20)
    pyplot.subplot(142)
    plot_phase5_msgload_helper(db, metric_key, em=10, ymax=20)
    pyplot.subplot(143)
    plot_phase5_msgload_helper(db, metric_key, em=100, ymax=100)
    pyplot.subplot(144)
    plot_phase5_msgload_helper(db, metric_key, em=1000, ymax=850, val_round=0)

    pyplot.tight_layout(pad=0.3)
    pyplot.savefig('phold-phase5-msgload-bar.pdf')

def plot_phase5_msgload_helper(db, metric_key, em, val_div=1, val_round=1, title=None, ymax=None, ylabel=None, yticks=None):
    names = ['ptrace', 'seccomp', 'uni-process']
    modes = ['ptrace', 'seccomp', 'classic']
    colors = ['C0', 'C1', 'C4']

    ec = 0
    ew = 'skewed'

    vals, errs = [], []
    for _, im in enumerate(modes):
        result = select(db, im=im, ec=ec, em=em, ew=ew)
        m, e = compute_mean_and_error(result[metric_key])
        m /= val_div
        e /= val_div
        m = round(m, val_round)
        vals.append(m)
        errs.append(e)

    rects = pyplot.bar(names, vals, yerr=errs, color=colors,
        capsize=3.0, error_kw={'linewidth': 1.0})
    pyplot.gca().bar_label(rects, label_type='edge', padding=1, fontsize=6)

    if yticks != None:
        pyplot.yticks(yticks)
    if ymax != None:
        pyplot.ylim(ymax=ymax)
    if ylabel != None:
        pyplot.ylabel(ylabel)#, horizontalalignment='right', y=1.0)

    pyplot.xticks(rotation=COMMON_ROTATION, ha='right')
    pyplot.title('1k msg/host' if em == 1000 else f'{em} msg/host')

def plot_phase5_weights(db):
    metric_key = 'perf_duration-time-sec'

    pyplot.figure()

    pyplot.subplot(131)
    plot_phase5_weights_helper(db, metric_key, ew='uniform', ylabel="Benchmark Time (s)", ymax=90)
    pyplot.subplot(132)
    plot_phase5_weights_helper(db, metric_key, ew='skewed', ymax=90)
    pyplot.subplot(133)
    plot_phase5_weights_helper(db, metric_key, ew='ring', ymax=90)

    pyplot.tight_layout(pad=0.3)
    pyplot.savefig('phold-phase5-weights-bar.pdf')

def plot_phase5_weights_helper(db, metric_key, ew, val_div=1, val_round=1, title=None, ymax=None, ylabel=None, yticks=None):
    names = ['ptrace', 'seccomp', 'uni-process']
    modes = ['ptrace', 'seccomp', 'classic']
    colors = ['C0', 'C1', 'C4']

    ec = 0
    em = 100

    vals, errs = [], []
    for _, im in enumerate(modes):
        result = select(db, im=im, ec=ec, em=em, ew=ew)
        m, e = compute_mean_and_error(result[metric_key])
        m /= val_div
        e /= val_div
        m = round(m, val_round)
        vals.append(m)
        errs.append(e)

    rects = pyplot.bar(names, vals, yerr=errs, color=colors,
        capsize=3.0, error_kw={'linewidth': 1.0})
    pyplot.gca().bar_label(rects, label_type='edge', padding=1, fontsize=6)

    if yticks != None:
        pyplot.yticks(yticks)
    if ymax != None:
        pyplot.ylim(ymax=ymax)
    if ylabel != None:
        pyplot.ylabel(ylabel)#, horizontalalignment='right', y=1.0)

    pyplot.xticks(rotation=COMMON_ROTATION, ha='right')
    pyplot.title(f'exponential workload' if ew == 'skewed' else f'{ew} workload')

def select(db, im, ec, em, ew):
    exp = Query()

    records = db.search(
        (exp.exe.cpuload == ec) &
        (exp.exe.msgload == em) &
        (exp.exe.quantity == 1000) &
        (exp.exe.weights == ew) &
        (exp.interpose_method == im) &
        (exp.num_workers == 28) &
        (exp.scheduling_policy == 'host') &
        (exp.use_memory_manager == (None if im == 'classic' else True)) &
        (exp.use_pinning == True) &
        (exp.use_realtime == False) &
        (exp.use_syscall_preloading == (None if im == 'classic' else True))
    )

    #print(json.dumps(records, sort_keys=True, indent=2))
    assert len(records) == 1
    return records[0]['~results']

if __name__ == "__main__":
    sys.exit(main())