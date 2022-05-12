import sys
import json
from math import sqrt

import matplotlib
matplotlib.use('Agg') # for systems without X11
import matplotlib.pyplot as pyplot

from scipy.stats import t as studentst

from plot_common import *

def main():
    with open("results.json", 'r') as inf:
        db = json.load(inf)

    #return test(db)

    set_plot_options()
    plot_bmark_interpose(db, 'interpose.pdf')
    plot_bmark_memmgr2(db, "memmgr.pdf")
    plot_bmark_cpusched(db, "cpusched-classic.pdf", 'classic')
    plot_bmark_cpusched(db, "cpusched-seccomp.pdf", 'seccomp')
    plot_bmark_cpusched(db, "cpusched-ptrace.pdf", 'ptrace')

    # not included in paper, keep around for posterity
    #plot_bmark_memmgr(db, "memmgr-old.pdf")
    #plot_bmark_cpusched_grouped(db, 'cpusched.pdf')

def test(db):
    result = select(db,
        "SYSCALL", 
        is_block=False,
        nbytes=None,
        method="classic",
        is_realtime=False,
        is_pin=True,
        is_singlecore=False,
        is_preloaded=None,
        use_shimsys=None,
        use_memmgr=None)
    
    print(json.dumps(result, sort_keys=True, indent=2))

def plot_bmark_interpose(db, filename):
    pyplot.figure()

    names = ['only ptrace', 'preload+ptrace', 'only seccomp', 'preload+seccomp', 'uni-process']
    colors = ['C0', 'C1', 'C2', 'C3', 'C4']

    pyplot.subplot(131)
    plot_bmark_interpose_helper(db, names, colors, "SYSCALL", True, None, "blocking nanosleep", ylabel=True)
    pyplot.subplot(132)
    plot_bmark_interpose_helper(db, names, colors, "SYSCALL", False, None, "nonblocking nanosleep")
    pyplot.subplot(133)
    plot_bmark_interpose_helper(db, names, colors, "BUFFER", None, 1024, "1k write+read")

    pyplot.tight_layout(pad=0.3)
    pyplot.savefig(filename)

def plot_bmark_interpose_helper(db, names, colors, mode, is_block, nbytes, title, ylabel=False):
    vals, errs = [], []
    get_interpose_result(db, vals, errs, mode, "ptrace", is_block=is_block, is_preloaded=False, nbytes=nbytes)
    get_interpose_result(db, vals, errs, mode, "ptrace", is_block=is_block, is_preloaded=True, nbytes=nbytes)
    get_interpose_result(db, vals, errs, mode, "seccomp", is_block=is_block, is_preloaded=False, nbytes=nbytes)
    get_interpose_result(db, vals, errs, mode, "seccomp", is_block=is_block, is_preloaded=True, nbytes=nbytes)
    get_interpose_result(db, vals, errs, mode, "classic", is_block=is_block, is_preloaded=None, nbytes=nbytes)

    rects = pyplot.bar(names, vals, yerr=errs, color=colors,
        capsize=3.0, error_kw={'linewidth': 1.0})
    pyplot.gca().bar_label(rects, label_type='edge', padding=1, fontsize=6)

    pyplot.xticks(rotation=COMMON_ROTATION, ha='right')
    pyplot.title(title)
    if ylabel:
        pyplot.ylabel("Benchmark Time (us)", horizontalalignment='right', y=1.2)
    pyplot.ylim(ymin=0, ymax=20)

def get_interpose_result(db, vals, errs, mode, method, is_block, is_preloaded, nbytes):
    result = select(db,
        mode, 
        is_block=is_block,
        nbytes=nbytes,
        method=method,
        is_realtime=False,
        is_pin=True,
        is_singlecore=False,
        is_preloaded=None if method == 'classic' else is_preloaded,
        use_shimsys=None if method == 'classic' else False,
        use_memmgr=None if method == 'classic' else True)
    m, e = compute_diff_mean_and_error(result)
    vals.append(round(m, 2))
    errs.append(e)

def plot_bmark_memmgr(db, filename):
    pyplot.figure()

    names = ['ptrace', 'preload+ptrace', 'seccomp', 'preload+seccomp']

    vals, errs = [], []
    get_memmgr_result(db, vals, errs, "ptrace", is_preloaded=False, use_memmgr=False, nbytes=16384)
    get_memmgr_result(db, vals, errs, "ptrace", is_preloaded=True, use_memmgr=False, nbytes=16384)
    get_memmgr_result(db, vals, errs, "seccomp", is_preloaded=False, use_memmgr=False, nbytes=16384)
    get_memmgr_result(db, vals, errs, "seccomp", is_preloaded=True, use_memmgr=False, nbytes=16384)

    pos = list(range(len(vals)))
    width = 0.33

    rects = pyplot.bar(pos, vals, yerr=errs,
        width=width,
        color='C1',
        capsize=0.5,
        error_kw={'linewidth': 0.5},
        label="proc vm copy")
    pyplot.gca().bar_label(rects, label_type='edge', padding=1, fontsize=6)

    vals, errs = [], []
    get_memmgr_result(db, vals, errs, "ptrace", is_preloaded=False, use_memmgr=True, nbytes=16384)
    get_memmgr_result(db, vals, errs, "ptrace", is_preloaded=True, use_memmgr=True, nbytes=16384)
    get_memmgr_result(db, vals, errs, "seccomp", is_preloaded=False, use_memmgr=True, nbytes=16384)
    get_memmgr_result(db, vals, errs, "seccomp", is_preloaded=True, use_memmgr=True, nbytes=16384)
    
    rects = pyplot.bar([p+width for p in pos], vals, yerr=errs,
        width=width,
        color='C0',
        #alpha=0.5,
        capsize=0.5,
        error_kw={'linewidth': 0.5},
        label="mem map copy")
    pyplot.gca().bar_label(rects, label_type='edge', padding=2, fontsize=6)
    
    ticks = [p + width/2 for p in pos]
    pyplot.xticks(ticks, names)#, rotation=COMMON_ROTATION, ha='right')
    pyplot.title("16k write+read")
    pyplot.ylabel("Benchmark Time (us)", horizontalalignment='right', y=1.2)
    pyplot.ylim(ymin=0, ymax=30)

    pyplot.legend()
    pyplot.tight_layout(pad=0.3)
    pyplot.savefig(filename)

def plot_bmark_memmgr2(db, filename):
    pyplot.figure()

    names = ['proc vm', 'proc mmap', 'uni-process']
    colors = ['C0', 'C1', 'C4']

    pyplot.subplot(141)
    plot_bmark_memmgr2_helper(db, names, colors, 1<<10, ylabel=True)
    pyplot.subplot(142)
    plot_bmark_memmgr2_helper(db, names, colors, 1<<12)
    pyplot.subplot(143)
    plot_bmark_memmgr2_helper(db, names, colors, 1<<14)
    pyplot.subplot(144)
    plot_bmark_memmgr2_helper(db, names, colors, 1<<16)

    #pyplot.legend()
    pyplot.tight_layout(pad=0.3)
    pyplot.subplots_adjust(right=0.975)
    pyplot.savefig(filename)

def plot_bmark_memmgr2_helper(db, names, colors, nbytes, ylabel=False):
    vals, errs = [], []
    get_memmgr_result(db, vals, errs, "seccomp", is_preloaded=True, use_memmgr=False, nbytes=nbytes)
    get_memmgr_result(db, vals, errs, "seccomp", is_preloaded=True, use_memmgr=True, nbytes=nbytes)
    get_memmgr_result(db, vals, errs, "classic", is_preloaded=None, use_memmgr=None, nbytes=nbytes)

    rects = pyplot.bar(names, vals, yerr=errs, color=colors,
        capsize=3.0, error_kw={'linewidth': 1.0})
    pyplot.gca().bar_label(rects, label_type='edge', padding=1, fontsize=6)

    pyplot.xticks(rotation=COMMON_ROTATION, ha='right')
    pyplot.title(f"{int(nbytes/1024)}k write+read")
    if ylabel:
        pyplot.ylabel("Benchmark Time (us)", horizontalalignment='right', y=1.2)
    pyplot.ylim(ymin=0, ymax=50)

def get_memmgr_result(db, vals, errs, method, is_preloaded, use_memmgr, nbytes):
    result = select(db,
        "BUFFER", 
        is_block=None,
        nbytes=nbytes,
        method=method,
        is_realtime=False,
        is_pin=True,
        is_singlecore=False,
        is_preloaded=None if method == 'classic' else is_preloaded,
        use_shimsys=None if method == 'classic' else False, # has no effect on classic,
        use_memmgr=None if method == 'classic' else use_memmgr)
    m, e = compute_diff_mean_and_error(result)
    vals.append(round(m, 2))
    errs.append(e)

def plot_bmark_cpusched(db, filename, method):
    pyplot.figure()

    names = ['standard', 'pin+standard', 'realtime', 'pin+realtime']
    colors = ['C0', 'C1', 'C2', 'C3']

    pyplot.subplot(131)
    plot_bmark_cpusched_helper(db, names, colors, method, "SYSCALL", True, None, "blocking nanosleep", ylabel=True)
    pyplot.subplot(132)
    plot_bmark_cpusched_helper(db, names, colors, method, "SYSCALL", False, None, "nonblocking nanosleep")
    pyplot.subplot(133)
    plot_bmark_cpusched_helper(db, names, colors, method, "BUFFER", None, 1024, "1k write+read")

    pyplot.tight_layout(pad=0.3)
    pyplot.savefig(filename)

def plot_bmark_cpusched_helper(db, names, colors, method, mode, is_block, nbytes, title, ylabel=False):
    vals, errs = [], []
    get_cpusched_result(db, vals, errs, mode, method, is_block=is_block, nbytes=nbytes, is_pin=False, is_realtime=False)
    get_cpusched_result(db, vals, errs, mode, method, is_block=is_block, nbytes=nbytes, is_pin=True, is_realtime=False)
    get_cpusched_result(db, vals, errs, mode, method, is_block=is_block, nbytes=nbytes, is_pin=False, is_realtime=True)
    get_cpusched_result(db, vals, errs, mode, method, is_block=is_block, nbytes=nbytes, is_pin=True, is_realtime=True)

    rects = pyplot.bar(names, vals, yerr=errs, color=colors,
        capsize=3.0, error_kw={'linewidth': 1.0})
    pyplot.gca().bar_label(rects, label_type='edge', padding=1, fontsize=6)

    pyplot.xticks(rotation=COMMON_ROTATION, ha='right')
    pyplot.title(title)
    if ylabel:
        pyplot.ylabel("Benchmark Time (us)", horizontalalignment='right', y=1.2)
    pyplot.ylim(ymin=0, ymax=30 if method == 'classic' else 60)

def get_cpusched_result(db, vals, errs, mode, method, is_block, nbytes, is_pin, is_realtime):
    result = select(db,
        mode, 
        is_block=is_block,
        nbytes=nbytes,
        method=method,
        is_realtime=is_realtime,
        is_pin=is_pin,
        is_singlecore=False,
        is_preloaded=None if method == 'classic' else True, # has no effect on classic
        use_shimsys=None if method == 'classic' else False, # has no effect on classic
        use_memmgr=None if method == 'classic' else True,) # has no effect on classic
    m, e = compute_diff_mean_and_error(result)
    vals.append(round(m, 2))
    errs.append(e)

def plot_bmark_cpusched_grouped(db, filename):
    fig = pyplot.figure()

    pyplot.subplot(131)

    plot_bmark_cpusched_grouped_helper(db, get_cpusched_syscall_block)
    pyplot.title("blocking nanosleep")
    pyplot.ylabel("Benchmark Time (us)", horizontalalignment='right', y=1.2)
    #pyplot.ylim(ymax=20)

    pyplot.subplot(132)

    plot_bmark_cpusched_grouped_helper(db, get_cpusched_syscall_nonblock)
    pyplot.title("nonblocking nanosleep")
    #pyplot.ylim(ymax=10)

    pyplot.subplot(133)

    plot_bmark_cpusched_grouped_helper(db, get_cpusched_buffer)
    pyplot.title("4k write+read")
    #pyplot.ylim(ymax=15)

    #pyplot.legend(loc="upper left", ncol=1, bbox_to_anchor=(1.0, 1.0))
    pyplot.tight_layout(pad=0.3)
    pyplot.savefig(filename)

def plot_bmark_cpusched_grouped_helper(db, metric_func):
    vals, errs = metric_func(db, is_pin=False, is_realtime=False)

    pos = list(range(len(vals)))
    width = 0.2

    loc = pos
    rects = pyplot.bar(loc, vals, yerr=errs,
        width=width,
        color='C0',
        capsize=0.5,
        error_kw={'linewidth': 0.5},
        label="Normal")
    pyplot.gca().bar_label(rects, label_type='edge', padding=2, fontsize=6, rotation=90)
    
    vals, errs = metric_func(db, is_pin=True, is_realtime=False)
    loc = [p + width for p in pos]
    rects = pyplot.bar(loc, vals, yerr=errs,
        width=width,
        color='C1',
        capsize=0.5,
        error_kw={'linewidth': 0.5},
        label="Pin")
    pyplot.gca().bar_label(rects, label_type='edge', padding=2, fontsize=6, rotation=90)

    vals, errs = metric_func(db, is_pin=False, is_realtime=True)
    loc = [p + 2*width for p in pos]
    rects = pyplot.bar(loc, vals, yerr=errs,
        width=width,
        color='C2',
        capsize=0.5,
        error_kw={'linewidth': 0.5},
        label="Realtime")
    pyplot.gca().bar_label(rects, label_type='edge', padding=2, fontsize=6, rotation=90)

    vals, errs = metric_func(db, is_pin=True, is_realtime=True)
    loc = [p + 3*width for p in pos]
    rects = pyplot.bar(loc, vals, yerr=errs,
        width=width,
        color='C3',
        capsize=0.5,
        error_kw={'linewidth': 0.5},
        label="Pin+Realtime")
    pyplot.gca().bar_label(rects, label_type='edge', padding=2, fontsize=6, rotation=90)
    
    names = ['classic', 'phantom']
    ticks = [p + 1.5*width for p in pos]
    pyplot.xticks(ticks, names)#, rotation=COMMON_ROTATION, ha='right')

def get_cpusched_syscall_nonblock(db, is_pin, is_realtime):
    vals, errs = [], []

    get_cpusched_result(db, vals, errs, "SYSCALL", "classic", is_block=False, nbytes=None, is_pin=is_pin, is_realtime=is_realtime)
    get_cpusched_result(db, vals, errs, "SYSCALL", "seccomp", is_block=False, nbytes=None, is_pin=is_pin, is_realtime=is_realtime)

    return [round(v, 2) for v in vals], errs

def get_cpusched_syscall_block(db, is_pin, is_realtime):
    vals, errs = [], []

    get_cpusched_result(db, vals, errs, "SYSCALL", "classic", is_block=True, nbytes=None, is_pin=is_pin, is_realtime=is_realtime)
    get_cpusched_result(db, vals, errs, "SYSCALL", "seccomp", is_block=True, nbytes=None, is_pin=is_pin, is_realtime=is_realtime)

    return [round(v, 2) for v in vals], errs

def get_cpusched_buffer(db, is_pin, is_realtime):
    vals, errs = [], []

    get_cpusched_result(db, vals, errs, "BUFFER", "classic", is_block=None, nbytes=4096, is_pin=is_pin, is_realtime=is_realtime)
    get_cpusched_result(db, vals, errs, "BUFFER", "seccomp", is_block=None, nbytes=4096, is_pin=is_pin, is_realtime=is_realtime)

    return [round(v, 2) for v in vals], errs

def select(sim_list, mode, is_block, nbytes, method, 
        is_realtime, is_pin, is_singlecore,
        is_preloaded, use_shimsys, use_memmgr):
    results = []
    sims_with_results = []

    for sim in sim_list:
        if sim['exe']['mode'] != mode:
            continue
        if sim['exe']['is_blocking'] != is_block:
            continue
        if sim['exe']['nbytes'] != nbytes:
            continue
        if sim['interpose_method'] != method:
            continue
        if sim['use_realtime'] != is_realtime:
            continue
        if sim['use_pinning'] != is_pin:
            continue
        if sim['use_single_core'] != is_singlecore:
            continue
        if sim['use_syscall_preloading'] != is_preloaded:
            continue
        if sim['use_shim_syscall_handler'] != use_shimsys:
            continue
        if sim['use_memory_manager'] != use_memmgr:
            continue
        results.append(sim['~results'])
        sims_with_results.append(sim)

    if len(results) != 1:
        print('######################################################################################')
        print('Your selection criteria has not resulted in a single result, please adjust your filter')
        print('######################################################################################')
        for s in sims_with_results:
            d = {k:s[k] for k in s if k != '~results'}
            print(json.dumps(d, sort_keys=True, indent=2))
    assert(len(results) == 1)
    return results[0]

# this is for computing a difference between two means
def compute_diff_mean_and_error(result, confidence_level=0.99):
    n1, n2 = result['bmark']['count'], result['noop']['count']
    m1, m2 = result['bmark']['mean'], result['noop']['mean']
    #s1, s2 = result['bmark']['std'], result['noop']['std']
    v1, v2 = result['bmark']['var'], result['noop']['var']

    m = m1 - m2
    v = v1/n1 + v2/n2
    s = sqrt(v)

    level = two_to_one_sided_confidence_level(confidence_level)
    deg_freedom = min(n1, n2) - 1
    t = studentst.ppf(level, deg_freedom)
    e = t * s

    if m < 0: # the mean can't be a negative time
        # widen the CI so that when we set the mean to 0
        # it still extends to the previous low bar
        e += abs(m)
        m = max(m, 0)

    return m, e

if __name__ == "__main__":
    sys.exit(main())