import argparse
import os
import plotlib

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"), help = "life stage")
    parser.add_argument("--norm", action = "store_true")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

def getType(norm):
    if norm:
        return "norm"
    else:
        return "raw"

def getLabel(norm):
    metric = "complexity"
    if norm:
        return "Normalized {0}".format(metric)
    else:
        return metric.capitalize()

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
for run in runs:
    births = plotlib.getBirths(run)
    mutualInfoValues = {}
    integrationValues = {}
    path = os.path.join(run, "plots", "data", "complexity-{0}.txt".format(args.stage))
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            agent, neuron, value = line.split()
            if neuron == "-":
                integrationValues[int(agent)] = float(value)
            else:
                mutualInfoValues.setdefault(int(agent), []).append(float(value))
    values = {}
    for agent in mutualInfoValues:
        value = sum(mutualInfoValues[agent]) - integrationValues[agent]
        if args.norm:
            value /= len(mutualInfoValues[agent])
        values[agent] = value
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel(getLabel(args.norm))
figure.tight_layout()
figure.savefig("complexity-{0}-{1}.pdf".format(getType(args.norm), args.stage))
