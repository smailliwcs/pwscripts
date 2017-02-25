import argparse
import math
import os
import plotlib

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("xmetric", metavar = "XMETRIC", help = "x-axis metric")
    parser.add_argument("ymetric", metavar = "YMETRIC", help = "y-axis metric")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width when XMETRIC is 'time'")
    parser.add_argument("--bins", metavar = "BINS", type = int, default = 100, help = "bin count when XMETRIC is not 'time'")
    return parser.parse_args()

def getLabel(metric):
    if metric == "time":
        return "Timestep"
    elif metric == "lifespan":
        return "Lifespan"
    else:
        return "Complexity ({0})".format(metric)

def getValues(run, metric):
    if metric == "time":
        return plotlib.getBirths(run)
    elif metric == "lifespan":
        return plotlib.getLifespans(run, plotlib.isNotTruncatedLifespan)
    else:
        values = {}
        path = os.path.join(run, "plots", "data", "complexity-{0}.txt".format(metric))
        with open(path) as f:
            for line in f:
                if line.startswith("#"):
                    continue
                if metric.find("pw") >= 0:
                    agent, value = line.split()
                    value = float(value)
                    if value != 0:
                        values[int(agent)] = value / math.log(math.e, 2)
                elif metric.find("jidt") >= 0:
                    agent, flag, value = line.split()
                    if flag == "C":
                        values[int(agent)] = float(value)
        return values

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
if args.xmetric == "time":
    for run in runs:
        x = getValues(run, args.xmetric)
        y = getValues(run, args.ymetric)
        zipped = plotlib.zipAgentData(x, y)
        binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
        axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
else:
    assert len(runs) == 1, "single run required when XMETRIC is not 'time'"
    x = getValues(runs[0], args.xmetric)
    y = getValues(runs[0], args.ymetric)
    zipped = plotlib.zipAgentData(x, y)
    image = plotlib.hist2d(axes, zipped[0], zipped[1], args.bins)
    fit = plotlib.getFit(zipped[0], zipped[1])
    axes.plot(fit[0], fit[1], linewidth = 2, color = "1")
    axes.plot(fit[0], fit[1], linewidth = 1, color = "0")
    plotlib.annotate(axes, "$r^2 = {0:.3f}$".format(fit[2] ** 2))
    colorbar = figure.colorbar(image)
    colorbar.set_label("Agent count")
    colorbar.locator = plotlib.LogLocator()
    colorbar.formatter = plotlib.LogFormatter()
    colorbar.update_ticks()
axes.set_xlabel(getLabel(args.xmetric))
axes.set_ylabel(getLabel(args.ymetric))
figure.tight_layout()
figure.savefig("complexity-{0}-{1}.pdf".format(args.ymetric, args.xmetric))
