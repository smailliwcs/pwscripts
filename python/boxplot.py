import argparse
import matplotlib
import matplotlib.colors
import matplotlib.pyplot
import numpy
import os
import patches
import plot
import scipy.stats
import utility

ANGLE = 5.0
CMAP = matplotlib.colors.LinearSegmentedColormap.from_list("boxplot", ["1.0", plot.COLOR[0]])
FONT_SIZE = matplotlib.rcParams["font.size"]
LINEWIDTH = matplotlib.rcParams["lines.linewidth"]
SHRINK = 10.0
YTEXT = 0.9

def parseArgs():
    global metric
    metrics = plot.Plot.getMetrics()
    parser = argparse.ArgumentParser(add_help = False)
    parser.add_argument("--tmin", metavar = "TMIN", type = int)
    parser.add_argument("--tmax", metavar = "TMAX", type = int)
    parser.add_argument("--ymin", metavar = "YMIN", type = float)
    parser.add_argument("--ymax", metavar = "YMAX", type = float)
    parser.add_argument("runs", metavar = "RUNS", nargs = "+")
    if len(metrics) != 1:
        parser.add_argument("metric", metavar = "METRIC")
        parser.print_help()
        raise SystemExit
    metric = metrics[0]
    parser.add_argument("metric", metavar = metric.getName())
    metric.addArgs(parser)
    return parser.parse_args()

def getData(args):
    global metric
    data = []
    for runs in args.runs:
        ax = []
        for run in utility.getRuns(runs):
            metric.initialize(run, False, args)
            dx = metric.toTimeBased(metric.read(), [args.tmin, args.tmax])
            for values in dx.values():
                ax.extend(values)
        data.append(ax)
    return data

def getKey(runs):
    return "\\texttt{{{0}}}".format(os.path.basename(os.path.realpath(runs)))

def getDirection(mean1, mean2, p):
    if p < 0.05:
        return "$<$" if mean1 < mean2 else "$>$"
    else:
        return "NS"

def getSignificance(p):
    if p < 0.001:
        return "$p < 0.001$"
    else:
        return "$p = {0:.3f}$".format(p)

# Configure plot
args = parseArgs()
data = getData(args)
figure = matplotlib.pyplot.figure()
figure.set_size_inches(plot.SIZE, 0.8 * plot.SIZE)
axes = figure.gca()
axes.grid(False, "both", "x")
axes.set_xticks(range(len(data)))
axes.set_xticklabels(map(getKey, args.runs))
axes.set_xlim(-0.5, len(data) - 0.5)
axes.set_ylabel(metric.getLabel())
if args.ymin is not None:
    axes.set_ylim(bottom = args.ymin)
if args.ymax is not None:
    axes.set_ylim(top = args.ymax)

# Plot violins
bodies = axes.violinplot(data, positions = range(len(data)), showextrema = False)["bodies"]
for body in bodies:
    body.set_alpha(1.0)
    body.set_edgecolor(CMAP(0.1))
    body.set_facecolor(CMAP(0.1))
    body.set_linewidth(LINEWIDTH)

# Plot boxes
means = map(lambda ax: numpy.mean(ax), data)
percentiles = map(lambda ax: numpy.percentile(ax, [10, 25, 75, 90]), data)
for index, ax in enumerate(data):
    axes.vlines(index, percentiles[index][0], percentiles[index][-1], color = CMAP(1.0))
    axes.vlines(index, percentiles[index][1], percentiles[index][-2], color = CMAP(1.0), linewidth = LINEWIDTH * 4.0)
    axes.scatter(index, means[index], color = "1.0", edgecolors = CMAP(1.0), linewidth = LINEWIDTH, zorder = 2)

# Label significance
for index1 in xrange(len(data) - 1):
    index2 = index1 + 1
    xytext = (float(index2) / len(data), YTEXT)
    p = scipy.stats.ttest_ind(data[index1], data[index2], equal_var = False)[1]
    kwargs = {
        "arrowprops": {
            "arrowstyle": "-",
            "connectionstyle": "angle, angleA=180, angleB={0}".format(90.0 - ANGLE / 2.0),
            "shrinkA": 0.0,
            "shrinkB": SHRINK
        },
        "textcoords": "axes fraction",
        "xytext": xytext
    }
    patch = axes.annotate("", xy = (index1, percentiles[index1][-1]), **kwargs).arrow_patch
    patches.fix(patch)
    kwargs["arrowprops"]["connectionstyle"] = "angle, angleA=180, angleB={0}".format(90.0 + ANGLE / 2.0)
    patch = axes.annotate("", xy = (index2, percentiles[index2][-1]), **kwargs).arrow_patch
    patches.fix(patch)
    kwargs = {
        "horizontalalignment": "center",
        "textcoords": "offset points",
        "verticalalignment": "baseline",
        "xy": xytext,
        "xycoords": "axes fraction",
        "xytext": [0.0, FONT_SIZE / 2.0]
    }
    axes.annotate(getDirection(means[index1], means[index2], p), **kwargs)
    kwargs["verticalalignment"] = "top"
    kwargs["xytext"][1] *= -1
    axes.annotate(getSignificance(p), **kwargs)

# Save plot
figure.savefig(metric.getKey())
