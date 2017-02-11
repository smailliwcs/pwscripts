import argparse
import os
import plotlib

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", metavar = "RUN", help = "run directory")
    parser.add_argument("metric", metavar = "METRIC", help = "complexity metric")
    parser.add_argument("--bins", metavar = "BINS", type = int, default = 100, help = "bin count")
    return parser.parse_args()

def getLabel(metric):
    return "Complexity ({0})".format(metric)

def getComplexities(run, metric):
    complexities = {}
    path = os.path.join(run, "plots", "data", "complexity-{0}.txt".format(metric))
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            if metric in ("pw", "hybrid-ts"):
                agent, value = line.split()
                value = float(value)
                if value != 0:
                    complexities[int(agent)] = value
            else:
                agent, neuron, value = line.split()
                agent = int(agent)
                value = float(value)
                if neuron == "-":
                    value *= -1
                complexities[agent] = complexities.get(agent, 0) + value
    return complexities

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
lifespans = plotlib.getLifespans(args.run, plotlib.isNotTruncatedLifespan)
complexities = getComplexities(args.run, args.metric)
zipped = plotlib.zipAgentData(lifespans, complexities)
image = plotlib.hist2d(axes, zipped[0], zipped[1], args.bins)
fit = plotlib.getFit(zipped[0], zipped[1])
axes.plot(fit[0], fit[1], linewidth = 2, color = "1")
axes.plot(fit[0], fit[1], linewidth = 1, color = "0")
axes.set_xlabel("Lifespan")
axes.set_ylabel(getLabel(args.metric))
colorbar = figure.colorbar(image)
colorbar.set_label("Agent count")
colorbar.locator = plotlib.LogLocator()
colorbar.formatter = plotlib.LogFormatter()
colorbar.update_ticks()
figure.tight_layout()
figure.savefig("lifespan-complexity-{0}.pdf".format(args.metric))
