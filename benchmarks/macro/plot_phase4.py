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
    with open("phase4.json", 'r') as inf:
        db.insert_multiple(json.load(inf))

    set_plot_options()
    plot_phase4_sched_barcharts(db)
    #return
    plot_phase4_sched_barchart(db)

    set_plot_options(grid='both')
    plot_all_phase4_metrics(db)

def plot_phase4_sched_barcharts(db):
    names = ['thread/host', 'thread/LP']
    sched_seccomp = [('seccomp', 'host'), ('seccomp', 'steal')]
    sched_ptrace = [('ptrace', 'host'), ('ptrace', 'steal')]
    sched_classic = [('classic', 'host'), ('classic', 'steal')]
    colors_phantom = ['C0', 'C1']
    colors_classic = ['C4', 'C5']

    # seccomp vs classic
    fig = pyplot.figure(constrained_layout=False)
    gs = fig.add_gridspec(ncols=9, nrows=1)

    #pyplot.subplot(161)
    fig.add_subplot(gs[0, 1])
    plot_phold_phase4_helper_paper(db, 'perf_duration-time-sec', 
        names, sched_seccomp, colors_phantom,
        title='seccomp', title_loc='right',
        ylabel="Benchmark Time (s)", 
        yticks=[0,20,40,60], ymax=65, val_round=1)
    #pyplot.subplot(162)
    fig.add_subplot(gs[0, 2])
    plot_phold_phase4_helper_paper(db, 'perf_duration-time-sec', 
        names, sched_classic, colors_classic,
        title='uni-proc', title_loc='left',
        yticks=[0,20,40,60], ymax=65, val_round=1)
    pyplot.gca().get_yaxis().set_ticklabels([])

    #pyplot.subplot(163)
    fig.add_subplot(gs[0, 4])
    plot_phold_phase4_helper_paper(db, 'mem_used_gib', 
        names, sched_seccomp, colors_phantom,
        title='seccomp', title_loc='right',
        ylabel="Max RAM Used (GiB)", 
        yticks=[0,1,2], ymax=2.45*1.05)
    #pyplot.subplot(164)
    fig.add_subplot(gs[0, 5])
    plot_phold_phase4_helper_paper(db, 'mem_used_gib', 
        names, sched_classic, colors_classic,
        title='uni-proc', title_loc='left',
        yticks=[0,1,2], ymax=2.45*1.05)
    pyplot.gca().get_yaxis().set_ticklabels([])

    #pyplot.subplot(165)
    fig.add_subplot(gs[0, 7])
    plot_phold_phase4_helper_paper(db, 'perf_cpu-migrations',
        names, sched_seccomp, colors_phantom,
        title='seccomp', title_loc='right',
        ylabel=r"CPU Migrations ($\times$10$^3$)", 
        val_div=1000.0, 
        yticks=[0,2,4,6,8,10], ymax=11*1.05)
    #pyplot.subplot(166)
    fig.add_subplot(gs[0, 8])
    plot_phold_phase4_helper_paper(db, 'perf_cpu-migrations',
        names, sched_classic, colors_classic,
        title='uni-proc', title_loc='left',
        val_div=1000.0, 
        yticks=[0,2,4,6,8,10], ymax=11*1.05)
    pyplot.gca().get_yaxis().set_ticklabels([])

    #pyplot.tight_layout(pad=0.3)
    pyplot.subplots_adjust(left=0.01, right=0.98, bottom=0.3)
    pyplot.savefig('phold-phase4-sched-bar-seccomp.pdf')

    ################################
    # ptrace vs classic
    fig = pyplot.figure(constrained_layout=False)
    gs = fig.add_gridspec(ncols=9, nrows=1)

    #pyplot.subplot(161)
    fig.add_subplot(gs[0, 1])
    plot_phold_phase4_helper_paper(db, 'perf_duration-time-sec', 
        names, sched_ptrace, colors_phantom,
        title='ptrace', 
        ylabel="Benchmark Time (s)", 
        yticks=[0,20,40,60,80], ymax=95, val_round=1)
    #pyplot.subplot(162)
    fig.add_subplot(gs[0, 2])
    plot_phold_phase4_helper_paper(db, 'perf_duration-time-sec', 
        names, sched_classic, colors_classic,
        title='uni-proc', 
        yticks=[0,20,40,60,80], ymax=95, val_round=1)
    pyplot.gca().get_yaxis().set_ticklabels([])

    #pyplot.subplot(163)
    fig.add_subplot(gs[0, 4])
    plot_phold_phase4_helper_paper(db, 'mem_used_gib', 
        names, sched_ptrace, colors_phantom,
        title='ptrace', 
        ylabel="Max RAM Used (GiB)", 
        yticks=[0,1,2], ymax=2.45*1.05)
    #pyplot.subplot(164)
    fig.add_subplot(gs[0, 5])
    plot_phold_phase4_helper_paper(db, 'mem_used_gib', 
        names, sched_classic, colors_classic,
        title='uni-proc', yticks=[0,1,2], ymax=2.45*1.05)
    pyplot.gca().get_yaxis().set_ticklabels([])

    #pyplot.subplot(165)
    fig.add_subplot(gs[0, 7])
    plot_phold_phase4_helper_paper(db, 'perf_cpu-migrations',
        names, sched_ptrace, colors_phantom,
        title='ptrace',
        ylabel=r"CPU Migrations ($\times$10$^3$)", 
        val_div=1000.0, 
        yticks=[0,2,4,6,8], ymax=9)
    #pyplot.subplot(166)
    fig.add_subplot(gs[0, 8])
    plot_phold_phase4_helper_paper(db, 'perf_cpu-migrations',
        names, sched_classic, colors_classic,
        title='uni-proc', 
        val_div=1000.0, 
        yticks=[0,2,4,6,8], ymax=9)
    pyplot.gca().get_yaxis().set_ticklabels([])

    #pyplot.tight_layout(pad=0.3)
    pyplot.subplots_adjust(left=0.01, right=0.98, bottom=0.3)
    pyplot.savefig('phold-phase4-sched-bar-ptrace.pdf')

def plot_phold_phase4_helper_paper(db, metric_key, names, sched_modes, colors,
        val_div=1, val_round=2, title=None, title_loc='center', ymax=None, ylabel=None, yticks=None):
    vals, errs = [], []
    for _, (im, sp) in enumerate(sched_modes):
        result = select(db, im=im, sp=sp)
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
        pyplot.title(title, loc=title_loc)

def plot_phase4_sched_barchart(db):
    # seccomp vs classic
    pyplot.figure()

    pyplot.subplot(131)
    plot_phold_phase4_helper(db, 'perf_duration-time-sec', ylabel="Benchmark Time (s)", ymax=95*1.05, val_round=1)
    
    pyplot.subplot(132)
    plot_phold_phase4_helper(db, 'mem_used_gib', ylabel="Max RAM Used (GiB)", yticks=[0,1,2], ymax=2.45*1.05)
    
    pyplot.subplot(133)
    plot_phold_phase4_helper(db, 'perf_cpu-migrations', ylabel=r"CPU Migrations ($\times$10$^3$)", val_div=1000.0, yticks=[0,2,4,6,8,10], ymax=11*1.05)

    pyplot.tight_layout(pad=0.3)
    pyplot.savefig('phold-phase4-sched-bar.pdf')

def plot_all_phase4_metrics(db):
    metric_keys = select(db, im='ptrace', sp='host').keys()
    for metric_key in metric_keys:
        metric_label = metric_key.replace('_', '-')
        dir = 'phase4_metrics'
        filename = f"phold-phase4-{metric_label}.pdf"

        if dir != None:
            os.makedirs(dir, exist_ok = True)
            filename = os.path.join(dir, filename)

        pyplot.figure()
        plot_phold_phase4_helper(db, metric_key, ylabel=metric_label)
        pyplot.tight_layout(pad=0.3)
        pyplot.savefig(filename)

def plot_phold_phase4_helper(db, metric_key, val_div=1, val_round=2, title=None, ymax=None, ylabel=None, yticks=None):
    c = '$\sim$'
    names = [
        f'ptrace: {c}host', 
        f'ptrace: {c}LP', 
        f'seccomp: {c}host', 
        f'seccomp: {c}LP',
        f'uni-process: {c}host',
        f'uni-process: {c}LP'
    ]
    sched_modes = [
        ('ptrace', 'host'), 
        ('ptrace', 'steal'), 
        ('seccomp', 'host'), 
        ('seccomp', 'steal'), 
        ('classic', 'host'),
        ('classic', 'steal')
    ]
    colors = ['C0', 'C1', 'C2', 'C3', 'C4', 'C5']

    vals, errs = [], []
    for _, (im, sp) in enumerate(sched_modes):
        result = select(db, im=im, sp=sp)
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

def select(db, im, sp):
    exp = Query()

    records = db.search(
        (exp.exe.msgload == 100) &
        (exp.exe.quantity == 1000) &
        (exp.exe.weights == 'skewed') &
        (exp.interpose_method == im) &
        (exp.num_workers == 28) &
        (exp.scheduling_policy == sp) &
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