import argparse
import os
import plotlib

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", metavar = "RUN", help = "run directory")
    parser.add_argument("xmetric", metavar = "XMETRIC", help = "x-axis metric")
    parser.add_argument("ymetric", metavar = "YMETRIC", help = "y-axis metric")
    parser.add_argument("--bins", metavar = "BINS", type = int, default = 100, help = "bin count")
    return parser.parse_args()

def getLabel(metric):
    return "Complexity ({0})".format(metric)

def getValues(run, metric):
    values = {}
    path = os.path.join(run, "plots", "data", "complexity-{0}.txt".format(metric))
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            if metric in ("pw", "hybrid-ts"):
                agent, value = line.split()
                value = float(value)
                if value != 0:
                    values[int(agent)] = value
            else:
                agent, neuron, value = line.split()
                agent = int(agent)
                value = float(value)
                if neuron == "-":
                    value *= -1
                values[agent] = values.get(agent, 0) + value
    return values

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
x = getValues(args.run, args.xmetric)
y = getValues(args.run, args.ymetric)
zipped = plotlib.zipAgentData(x, y)
image = plotlib.hist2d(axes, zipped[0], zipped[1], args.bins)
fit = plotlib.getFit(zipped[0], zipped[1])
axes.plot(fit[0], fit[1], linewidth = 2, color = "1")
axes.plot(fit[0], fit[1], linewidth = 1, color = "0")
plotlib.annotate(axes, "$r^2 = {0:.3f}$".format(fit[2] ** 2))
axes.set_xlabel(getLabel(args.xmetric))
axes.set_ylabel(getLabel(args.ymetric))
colorbar = figure.colorbar(image)
colorbar.set_label("Agent count")
colorbar.locator = plotlib.LogLocator()
colorbar.formatter = plotlib.LogFormatter()
colorbar.update_ticks()
figure.tight_layout()
figure.savefig("complexities-{0}-{1}.pdf".format(args.xmetric, args.ymetric))
