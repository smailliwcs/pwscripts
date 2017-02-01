import argparse
import matplotlib
import os
import plotlib

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", metavar = "RUN", help = "run directory")
    parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"), help = "life stage")
    parser.add_argument("--norm", action = "store_true", help = "normalize by neuron count")
    parser.add_argument("--bins", metavar = "BINS", type = int, default = 100, help = "bin count")
    return parser.parse_args()

def getMetric(norm):
    if norm:
        return "norm"
    else:
        return "raw"

def getPolyworldValues():
    values = {}
    path = os.path.join(args.run, "plots", "data", "complexity-pw.txt")
    with open(path) as f:
        for line in f:
            agent, value = line.split()
            value = float(value)
            if value != 0:
                values[int(agent)] = value
    return values

def getJidtValues():
    mutualInfoValues = {}
    integrationValues = {}
    path = os.path.join(args.run, "plots", "data", "complexity-jidt-{0}.txt".format(args.stage))
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            agent, neuron, value = line.split()
            agent = int(agent)
            value = float(value)
            if neuron == "-":
                integrationValues[agent] = value
            else:
                mutualInfoValues.setdefault(agent, []).append(value)
    values = {}
    for agent in mutualInfoValues:
        value = sum(mutualInfoValues[agent]) - integrationValues[agent]
        if args.norm:
            value /= len(mutualInfoValues[agent])
        values[agent] = value
    return values

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
zipped = plotlib.zipAgentData(getPolyworldValues(), getJidtValues())
image = axes.hist2d(zipped[0], zipped[1], args.bins, cmap = plotlib.colormaps["gray_partial_r"], norm = matplotlib.colors.LogNorm())[3]
fit = plotlib.getFit(zipped[0], zipped[1])
axes.plot(fit[0], fit[1], linewidth = 2, color = "1")
axes.plot(fit[0], fit[1], linewidth = 1, color = "0")
axes.set_xlabel("Complexity (Polyworld)")
axes.set_ylabel("Complexity (JIDT)")
colorbar = figure.colorbar(image)
colorbar.set_label("Agent count")
colorbar.locator = plotlib.LogLocator()
colorbar.formatter = plotlib.LogFormatter()
colorbar.update_ticks()
figure.tight_layout()
figure.savefig("complexities-{0}-{1}.pdf".format(getMetric(args.norm), args.stage))
