from math import sqrt

import matplotlib
from scipy.stats import t as studentst

COMMON_ROTATION=35
COMMON_ROTATION2=45

# The scipy t.ppf distributed is for one-sided hypothesis tests.
# If we want to compute a two-sided error, then we must convert a two-sided
# confidence level to an equivalent one-side confidence level for scipy.
def two_to_one_sided_confidence_level(two_sided_level):
    return two_sided_level / 2.0 + 0.5

def compute_mean_and_error(result, confidence_level=0.99):
    n = result['count']
    m = result['mean']
    s = result['std']
    #sem = s / sqrt(n) # equivalent to scipy.stats.sem(trial_values)

    level = two_to_one_sided_confidence_level(confidence_level)
    t = studentst.ppf(level, n-1)
    e = t * s / sqrt(n-1)

    # symmetric error
    return m, e

def set_plot_options(grid='y'):
    options = {
        'backend': 'PDF',
        'font.size': 12,
        'figure.figsize': (4,1.75),
        'figure.dpi': 100.0,
        #'grid.color': '0.1',
        'grid.linestyle': ':',
        #'grid.linewidth': 0.5,
        #'grid.alpha': 0.1,
        'axes.grid' : True,
        'axes.grid.axis' : grid,
        #'axes.axisbelow': True,
        'axes.titlesize' : 'x-small',
        'axes.labelsize' : 10,
        'axes.formatter.limits': (-4,4),
        'xtick.labelsize' : 8,
        'ytick.labelsize' : 10,
        'lines.linewidth' : 1.5,
        'lines.markeredgewidth' : 0.5,
        'lines.markersize' : 4,
        'legend.fontsize' : 8,
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
        matplotlib.rcParams['figure.max_num_figures'] = 100
    if 'figure.max_open_warning' in matplotlib.rcParams:
        matplotlib.rcParams['figure.max_open_warning'] = 100
    if 'legend.ncol' in matplotlib.rcParams:
        matplotlib.rcParams['legend.ncol'] = 100