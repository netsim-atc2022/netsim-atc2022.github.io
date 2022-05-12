import sys
import os
import json

import matplotlib
matplotlib.use('Agg') # for systems without X11
import matplotlib.pyplot as pyplot
from matplotlib.ticker import FuncFormatter

from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage

from plot_common import *

def main():
    # koios experiments
    run("phase6.json", 
        "phase6_metrics", 
        pdf_name_suffix='',
        thread_low=14, 
        thread_high=28, 
        thread_classic_lim=16000, 
        thread_phantom_lim=64000
    )

def run(db_filename, pdf_dir, pdf_name_suffix, 
        thread_low, thread_high, thread_classic_lim, thread_phantom_lim):
    # load the db into ram
    db = TinyDB(storage=MemoryStorage)
    with open(db_filename, 'r') as inf:
        db.insert_multiple(json.load(inf))

    set_plot_options_custom(grid='both')
    
    # the ones we might want in the paper
    plot_phase6_metric(db, f'perf_duration-time-sec{pdf_name_suffix}',
        nw=thread_high,
        thread_classic_lim=thread_classic_lim,
        thread_phantom_lim=thread_phantom_lim,
        val_div=60.0, # converts seconds to minutes
        ylabel="Total Time (m)", ylabel_ralign=True)
    plot_phase6_metric(db, f'seconds_to_init{pdf_name_suffix}', 
        nw=thread_high,
        thread_classic_lim=thread_classic_lim,
        thread_phantom_lim=thread_phantom_lim,
        ylabel="Initialize Time (s)", ylabel_ralign=True)
    plot_phase6_metric(db, f'seconds_post_init{pdf_name_suffix}', 
        nw=thread_high,
        thread_classic_lim=thread_classic_lim,
        thread_phantom_lim=thread_phantom_lim,
        val_div=60.0, # converts seconds to minutes
        ylabel="Post-Initialize Time (m)", ylabel_ralign=True)
    plot_phase6_metric(db, f'mem_used_gib{pdf_name_suffix}', 
        nw=thread_high,
        thread_classic_lim=thread_classic_lim,
        thread_phantom_lim=thread_phantom_lim,
        ylabel="Max RAM Used (GiB)", ylabel_ralign=True)

    # all of the results for analysis, 14 and 28 LPs
    plot_all_phase6_metrics(db, pdf_dir, pdf_name_suffix,
        nw=thread_low, 
        thread_classic_lim=thread_classic_lim,
        thread_phantom_lim=thread_phantom_lim)
    plot_all_phase6_metrics(db, pdf_dir, pdf_name_suffix,
        nw=thread_high, 
        thread_classic_lim=thread_classic_lim,
        thread_phantom_lim=thread_phantom_lim)

def plot_all_phase6_metrics(db, pdf_dir, pdf_name_suffix, nw, thread_classic_lim, thread_phantom_lim):
    metric_keys = select(db, im='ptrace', nw=nw, eq=1000).keys()

    for metric_key in metric_keys:
        metric_label = metric_key.replace('_', '-')
        plot_phase6_metric(db, metric_key, nw=nw, 
            thread_classic_lim=thread_classic_lim,
            thread_phantom_lim=thread_phantom_lim,
            pdf_name_suffix=pdf_name_suffix,
            title=f'{nw} logical processors',
            ylabel=metric_label, 
            dir=pdf_dir)

def plot_phase6_metric(db, metric_key, nw, thread_classic_lim, thread_phantom_lim,
        title=None, ncol=1, dir=None, pdf_name_suffix='', val_div=1,
        ylabel=None, ylabel_ralign=False, yscale=None, ymin=None, ymax=None, yticks=None, bbox=None):
    names = ['ptrace', 'seccomp', 'uni-process']
    colors = ['C0', 'C1', 'C4']
    formats = ['o--', '^:', 's-']

    methods = ['ptrace', 'seccomp', 'classic']
    x_numhosts_phantom = [1000*2**i for i in range(10) if 1000*2**i <= thread_phantom_lim] # 1000 to 32000
    x_numhosts_classic = [1000*2**i for i in range(10) if 1000*2**i <= thread_classic_lim] # 1000 to 16000

    pyplot.figure()

    for i, im in enumerate(methods):
        y_vals, y_errs = [], []

        x_numhosts = x_numhosts_classic if im == 'classic' else x_numhosts_phantom

        for eq in x_numhosts:
            result = select(db, im=im, nw=nw, eq=eq)
            m, e = compute_mean_and_error(result[metric_key])
            y_vals.append(m/val_div)
            y_errs.append(e/val_div)

        pyplot.errorbar(x_numhosts, y_vals, yerr=y_errs,
            label=names[i], color=colors[i], fmt=formats[i],
            zorder=2 if i == 2 else 3, # uniproc is a solid line, put it on the bottom
            capsize=2.0, linewidth=2.0) #markersize=4, 

    pyplot.xscale('log')
    pyplot.yscale('log')
    pyplot.gca().get_xaxis().set_major_formatter(FuncFormatter(lambda x, pos: "{}k".format(int(x/1000))))
    # turns off minor ticks on the x axis
    pyplot.gca().get_xaxis().set_tick_params(which='minor', bottom=False)
    # turns off minor ticks on both axes
    #pyplot.minorticks_off()

    pyplot.xticks(x_numhosts_phantom)
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
    pyplot.xlabel('Virtual Host Count')

    if title != None:
        pyplot.title(title)

    if bbox != None:
        pyplot.legend(ncol=ncol, loc='upper left', bbox_to_anchor=bbox)
    else:
        pyplot.legend(ncol=ncol)
    pyplot.tight_layout(pad=0.3)

    metric_label = metric_key.replace('_', '-')
    filename = f"phold-phase6-{metric_label}-{nw}{pdf_name_suffix}.pdf"
    if dir != None:
        os.makedirs(dir, exist_ok = True)
        filename = os.path.join(dir, filename)
    pyplot.savefig(filename)

def select(db, im, nw, eq):
    exp = Query()

    records = db.search(
        (exp.exe.msgload == 100) &
        (exp.exe.quantity == eq) &
        (exp.exe.weights == 'skewed') &
        (exp.interpose_method == im) &
        (exp.num_workers == nw) &
        (exp.scheduling_policy == 'host') &
        (exp.use_memory_manager == (None if im == 'classic' else True)) &
        (exp.use_pinning == True) &
        (exp.use_realtime == False) &
        (exp.use_syscall_preloading == (None if im == 'classic' else True))
    )

    #print(json.dumps(records, sort_keys=True, indent=2))
    assert len(records) == 1
    return records[0]['~results']

def set_plot_options_custom(grid='y'):
    options = {
        'backend': 'PDF',
        'font.size': 12,
        'figure.figsize': (4,2),
        'figure.dpi': 100.0,
        #'grid.color': '0.1',
        'grid.linestyle': ':',
        #'grid.linewidth': 0.5,
        #'grid.alpha': 0.1,
        'axes.grid' : True,
        'axes.grid.axis' : grid,
        #'axes.axisbelow': True,
        'axes.titlesize' : 'x-small',
        'axes.labelsize' : 14,
        'axes.formatter.limits': (-4,4),
        'xtick.labelsize' : 12,
        'ytick.labelsize' : 12,
        'lines.linewidth' : 1.5,
        'lines.markeredgewidth' : 0.5,
        'lines.markersize' : 5,
        'legend.fontsize' : 12,
        'legend.fancybox' : False,
        'legend.shadow' : False,
        'legend.borderaxespad' : 0.5,
        'legend.numpoints' : 1,
        'legend.handletextpad' : 0.25,
        'legend.handlelength' : 1.0,
        'legend.labelspacing' : .25,
        'legend.markerscale' : 1.0,
        # turn on the following to embedd fonts; requires latex
        'ps.useafm' : True,
        'pdf.use14corefonts' : True,
        'text.usetex' : True,
    }

    for option_key in options:
        matplotlib.rcParams[option_key] = options[option_key]

    if 'figure.max_num_figures' in matplotlib.rcParams:
        matplotlib.rcParams['figure.max_num_figures'] = 100
    if 'figure.max_open_warning' in matplotlib.rcParams:
        matplotlib.rcParams['figure.max_open_warning'] = 100
    if 'legend.ncol' in matplotlib.rcParams:
        matplotlib.rcParams['legend.ncol'] = 100

if __name__ == "__main__":
    sys.exit(main())