import sys
import json
from math import log, exp, sqrt
from statistics import mean, stdev

from scipy.stats import t as studentst

import matplotlib
matplotlib.use('Agg') # for systems without X11
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as pyplot
from matplotlib.ticker import MaxNLocator

def main():
    set_plot_options()
    plot_all_metrics()


def plot_all_metrics():
    metrics = [
        [get_run_time, "run_time", "Relative Run Time (\%)", "Absolute Run Time (h)"],
        [get_ram_used, "ram_used", "Relative RAM Used (\%)", "Absolute RAM Used (GiB)"],
        [get_packets_per_second, "tput_pps", "Relative Throughput (\%)", "Absolute Throughput (pkt/s)"],
        [get_microseconds_per_packet, 'lat_ppus', "Relative Latency (\%)", "Absolute Latency ($\mu$s/pkt)"]
    ]

    for [metric_func, file_tag, rel_ylabel, abs_ylabel] in metrics:
        x, y_abs, y_rel, y_abs_err, y_rel_err = load_metric_values(metric_func)
        plot(f'tor_rel_{file_tag}.pdf', x, y_rel, yerr=y_rel_err, ylabel=rel_ylabel)
        plot(f'tor_abs_{file_tag}.pdf', x, y_abs, yerr=y_abs_err, ylabel=abs_ylabel)

def load_metric_values(metric_func):
    x = []
    y_abs, y_rel, y_abs_err, y_rel_err = {}, {}, {}, {}

    for netsize in ['0.05', '0.1', '0.15', '0.2', '0.25', '0.3']:
        percent_size = int(float(netsize) * 100.0) # convert to percentage
        x.append(percent_size)

        for mode in ['classic', 'phantom-preload']: #, 'phantom-ptrace']:
            vals_abs, vals_rel = get_trial_values(netsize, mode, metric_func)

            # we use the arithmetic mean of the abs values
            m, e = compute_arithmetic_mean_and_error(vals_abs)
            y_abs.setdefault(mode, []).append(m)
            y_abs_err.setdefault(mode, []).append(e)

            # we use the geometric mean of the rel values (i.e., ratios)
            m, [e_lo, e_hi] = compute_geometric_mean_and_error(vals_rel)
            # convert to percentages
            y_rel.setdefault(mode, []).append(m*100.0)
            y_rel_err.setdefault(mode, [[], []])
            y_rel_err[mode][0].append(e_lo*100.0)
            y_rel_err[mode][1].append(e_hi*100.0)

    return x, y_abs, y_rel, y_abs_err, y_rel_err

def plot(filename, x, y, yerr=None, ylabel='Performance'):
    print(filename)
    print(json.dumps(y))

    fig = pyplot.figure()

    # pyplot.errorbar(x, y['phantom-ptrace'], 
    #     yerr=yerr['phantom-ptrace'] if yerr != None else None, 
    #     fmt='o--', 
    #     capsize=5.0, 
    #     capthick=1.0,
    #     linewidth=2.0,
    #     zorder=3,
    #     label='ptrace')

    pyplot.errorbar(x, y['phantom-preload'], 
        yerr=yerr['phantom-preload'] if yerr != None else None, 
        fmt='^:', 
        capsize=5.0,
        capthick=1.0,
        linewidth=2.0,
        color='C1',
        zorder=3,
        label='phantom')

    pyplot.errorbar(x, y['classic'], 
        yerr=yerr['classic'] if yerr != None else None, 
        fmt='s-', 
        capsize=5.0,
        capthick=1.0,
        linewidth=2.0,
        color='C4',
        zorder=2,
        label='shadow')

    legloc = None
    if 'Absolute Run' in ylabel:
        #fig.gca().yaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
        #legloc = 'upper left'
        pyplot.yticks([5, 10, 15, 20, 25, 30])
    elif 'Relative Run' in ylabel:
        #fig.gca().yaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
        legloc = 'lower right'
        pyplot.yticks([90, 95, 100, 105, 110])
    elif 'Relative RAM' in ylabel:
        #fig.gca().yaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
        legloc = 'center left'
        pyplot.yticks([90, 92, 94, 96, 98, 100])

    pyplot.xticks(x, [str(v) for v in x])
    pyplot.xlabel("Tor Network Model Scale (\%)")
    pyplot.ylabel(ylabel, horizontalalignment='right', y=1.0)
    #pyplot.legend(loc='lower center', bbox_to_anchor=(0.5, 1.10), ncol=3)
    #pyplot.legend(loc='upper left' if "Absolute Run Time" in ylabel else 'center')
    pyplot.legend(loc=legloc)
    pyplot.tight_layout(pad=0.3)

    pyplot.savefig(filename)

# The scipy t.ppf distributed is for one-sided hypothesis tests.
# If we want to compute a two-sided error, then we must convert a two-sided
# confidence level to an equivalent one-side confidence level for scipy.
def two_to_one_sided_confidence_level(two_sided_level):
    return two_sided_level / 2.0 + 0.5

def compute_arithmetic_mean_and_error(trial_values, confidence_level=0.95):
    n = len(trial_values)

    m = mean(trial_values)
    s = stdev(trial_values)
    #sem = s / sqrt(n) # equivalent to scipy.stats.sem(trial_values)

    level = two_to_one_sided_confidence_level(confidence_level)
    t = studentst.ppf(level, n-1)
    e = t * s / sqrt(n-1)

    # symmetric error
    return m, e

# https://stats.stackexchange.com/questions/8306/confidence-interval-for-geometric-mean
def compute_geometric_mean_and_error(trial_values, confidence_level=0.95):
    # Convert to arithmetic space, where CI error is additively related to the mean
    trial_values_log = [log(v) for v in trial_values]
    m_a, e_a = compute_arithmetic_mean_and_error(trial_values_log)
    ci_lo_a, ci_hi_a = m_a - e_a, m_a + e_a

    # Convert back to geometric, where CIs are multiplicatively related to the mean
    # Note: m_g is equivalent to scipy.stats.gmean(trial_values)
    m_g, e_g = exp(m_a), exp(e_a)
    ci_lo_g, ci_hi_g = m_g / e_g, m_g * e_g

    # Now converting the arithmetic CIs should match the geometric CIs
    assert(round(ci_lo_g, 9) == round(exp(ci_lo_a), 9))
    assert(round(ci_hi_g, 9) == round(exp(ci_hi_a), 9))

    # pyplot wants relative error, i.e., the abs length of the error bars
    e_lo = m_g - ci_lo_g
    e_hi = ci_hi_g - m_g
    return m_g, [e_lo, e_hi]

def get_trial_values(netsize, mode, metric_func):
    y_abs, y_rel = [], []

    num_trials = 10
    trial_nums = [str(i+1) for i in range(num_trials)]

    for trial_num in trial_nums:
        value = metric_func(f'shadowtor-{netsize}-{trial_num}-{mode}')
        y_abs.append(value)
        baseline = metric_func(f'shadowtor-{netsize}-{trial_num}-classic')
        y_rel.append(value / baseline)

    return y_abs, y_rel

def get_ram_used(dirname):
    with open(f'data/{dirname}/resource_usage.json') as inf:
        d = json.load(inf)
    return float(d['ram']['gib_used_max'])

def get_run_time(dirname):
    with open(f'data/{dirname}/resource_usage.json') as inf:
        d = json.load(inf)
    return float(d['run_time']['hours'])

def get_packet_count(dirname):
    with open(f'data/{dirname}/packet_counts.json') as inf:
        d = json.load(inf)
    return float(int(d['total_packets_sent']))

def get_packets_per_second(dirname):
    p, s = get_packets_seconds(dirname)
    return p / s

def get_microseconds_per_packet(dirname):
    p, s = get_packets_seconds(dirname)
    us = s * 1000.0 * 1000.0
    return us / p

def get_packets_seconds(dirname):
    with open(f'data/{dirname}/packet_counts.json') as inf:
        d = json.load(inf)
    parts = d['real_time'].strip().split(':')
    h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
    s += (m*60.0 + h*3600.0)
    p = float(int(d['total_packets_sent']))
    return p, s

def set_plot_options():
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
        'axes.grid.axis' : 'both',
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
        #'ps.useafm' : True,
        #'pdf.use14corefonts' : True,
        #'text.usetex' : True,
    }

    for option_key in options:
        matplotlib.rcParams[option_key] = options[option_key]

    if 'figure.max_num_figures' in matplotlib.rcParams:
        matplotlib.rcParams['figure.max_num_figures'] = 50
    if 'figure.max_open_warning' in matplotlib.rcParams:
        matplotlib.rcParams['figure.max_open_warning'] = 50
    if 'legend.ncol' in matplotlib.rcParams:
        matplotlib.rcParams['legend.ncol'] = 50

if __name__ == "__main__":
    sys.exit(main())
