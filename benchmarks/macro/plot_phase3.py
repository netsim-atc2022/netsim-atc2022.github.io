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
    with open("phase3.json", 'r') as inf:
        db.insert_multiple(json.load(inf))

    set_plot_options()
    plot_phase3_memmgr_barcharts(db)

    set_plot_options(grid='both')
    plot_all_phase3_metrics(db)

def plot_phase3_memmgr_barcharts(db,):
    # seccomp vs classic
    pyplot.figure()

    pyplot.subplot(131)
    plot_phold_phase3_helper_paper(db, 'perf_duration-time-sec', is_seccomp=True,
        ylabel="Benchmark Time (s)", val_round=1, ymax=60)

    pyplot.subplot(132)
    plot_phold_phase3_helper_paper(db, 'mem_used_gib', is_seccomp=True,
        ylabel="Max RAM Used (GiB)", yticks=[0,1,2], ymax=2.5)
    
    pyplot.subplot(133)
    plot_phold_phase3_helper_paper(db, 'perf_page-faults', is_seccomp=True,
        ylabel=r"Page Faults ($\times$10$^6$)", val_div=10**6, ymax=1.85)

    pyplot.tight_layout(pad=0.3)
    pyplot.savefig(f'phold-phase3-memmgr-bar-seccomp.pdf')

    # ptrace vs classic
    pyplot.figure()

    pyplot.subplot(131)
    plot_phold_phase3_helper_paper(db, 'perf_duration-time-sec', is_seccomp=False,
        ylabel="Benchmark Time (s)", val_round=1, ymax=90)

    pyplot.subplot(132)
    plot_phold_phase3_helper_paper(db, 'mem_used_gib', is_seccomp=False,
        ylabel="Max RAM Used (GiB)", yticks=[0,1,2], ymax=2.5)
    
    pyplot.subplot(133)
    plot_phold_phase3_helper_paper(db, 'perf_page-faults', is_seccomp=False,
        ylabel=r"Page Faults ($\times$10$^6$)", val_div=10**6, ymax=1.85)

    pyplot.tight_layout(pad=0.3)
    pyplot.savefig(f'phold-phase3-memmgr-bar-ptrace.pdf')

def plot_phold_phase3_helper_paper(db, metric_key, is_seccomp=True, val_div=1, val_round=2, title=None, ymax=None, ylabel=None, yticks=None):
    if is_seccomp:
        names = [
            'proc vm', 
            'proc mmap',
            'uni-process'
        ]
        memmgr_modes = [
            ('seccomp', False), 
            ('seccomp', True), 
            ('classic', None)
        ]
    else:
        names = [
            'proc vm', 
            'proc mmap', 
            'uni-process'
        ]
        memmgr_modes = [
            ('ptrace', False), 
            ('ptrace', True), 
            ('classic', None)
        ]
    colors = ['C0', 'C1', 'C4']

    vals, errs = [], []
    for _, (im, umm) in enumerate(memmgr_modes):
        result = select(db, im=im, umm=umm)
        m, e = compute_mean_and_error(result[metric_key])
        m /= val_div
        e /= val_div
        m = round(m, val_round)
        vals.append(m)
        errs.append(e)

    rects = pyplot.bar(names, vals, yerr=errs, color=colors,
        capsize=3.0, error_kw={'linewidth': 1.0})
    pyplot.gca().bar_label(rects, label_type='edge', padding=1, fontsize=6)

    pyplot.xticks(rotation=COMMON_ROTATION, ha='right')
    if yticks != None:
        pyplot.yticks(yticks)
    if ymax != None:
        pyplot.ylim(ymax=ymax)
    if ylabel != None:
        pyplot.ylabel(ylabel, horizontalalignment='right', y=1.0)
    if title != None:
        pyplot.title(title)

def plot_all_phase3_metrics(db):
    metric_keys = select(db, im='ptrace', umm=True).keys()
    for metric_key in metric_keys:
        metric_label = metric_key.replace('_', '-')
        dir = 'phase3_metrics'
        filename = f"phold-phase3-{metric_label}.pdf"

        if dir != None:
            os.makedirs(dir, exist_ok = True)
            filename = os.path.join(dir, filename)

        pyplot.figure()
        plot_phold_phase3_helper(db, metric_key, ylabel=metric_label)
        pyplot.tight_layout(pad=0.3)
        pyplot.savefig(filename)
        
def plot_phold_phase3_helper(db, metric_key, val_div=1, val_round=2, title=None, ymax=None, ylabel=None, yticks=None):
    names = [
        'ptrace: proc vm', 
        'ptrace: proc mmap', 
        'seccomp: proc vm', 
        'seccomp: proc mmap',
        'uni-process'
    ]
    memmgr_modes = [
        ('ptrace', False), 
        ('ptrace', True), 
        ('seccomp', False), 
        ('seccomp', True), 
        ('classic', None)
    ]
    colors = ['C0', 'C1', 'C2', 'C3', 'C4']

    vals, errs = [], []
    for _, (im, umm) in enumerate(memmgr_modes):
        result = select(db, im=im, umm=umm)
        m, e = compute_mean_and_error(result[metric_key])
        m /= val_div
        e /= val_div
        m = round(m, val_round)
        vals.append(m)
        errs.append(e)

    rects = pyplot.bar(names, vals, yerr=errs, color=colors,
        capsize=3.0, error_kw={'linewidth': 1.0})
    pyplot.gca().bar_label(rects, label_type='edge', padding=1, fontsize=6)

    pyplot.xticks(rotation=COMMON_ROTATION2, ha='right')
    if yticks != None:
        pyplot.yticks(yticks)
    if ymax != None:
        pyplot.ylim(ymax=ymax)
    if ylabel != None:
        pyplot.ylabel(ylabel, horizontalalignment='right', y=1.0)
    if title != None:
        pyplot.title(title)

def select(db, im, umm):
    exp = Query()

    records = db.search(
        (exp.exe.msgload == 100) &
        (exp.exe.quantity == 1000) &
        (exp.exe.weights == 'skewed') &
        (exp.interpose_method == im) &
        (exp.num_workers == 28) &
        (exp.scheduling_policy == 'host') &
        (exp.use_memory_manager == umm) &
        (exp.use_pinning == True) &
        (exp.use_realtime == False) &
        (exp.use_syscall_preloading == (None if im == 'classic' else True))
    )

    #print(json.dumps(records, sort_keys=True, indent=2))
    assert len(records) == 1
    return records[0]['~results']

if __name__ == "__main__":
    sys.exit(main())