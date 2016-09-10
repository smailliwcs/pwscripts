import argparse
import os
import plotlib

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("stat", metavar = "STAT", choices = ("mean", "sum"), help = "statistic")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
for run in runs:
    births = plotlib.getBirths(run)
    values = {}
    path = os.path.join(run, "plots", "data", "info-storage.txt")
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            agent, neuron, value = line.split()
            values.setdefault(int(agent), {})[int(neuron)] = float(value)
    path = os.path.join(run, "plots", "data", "info-transfer-apparent.txt")
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            agent, preNeuron, postNeuron, value = line.split()
            if preNeuron == "-" and postNeuron == "-":
                continue
            values[int(agent)][int(postNeuron)] += float(value)
    valuesPos = {}
    valuesNeg = {}
    for agent in values:
        valuesPos[agent] = plotlib.getStatistic(values[agent].values(), args.stat, lambda value: value >= 0)
        valuesNeg[agent] = plotlib.getStatistic(values[agent].values(), args.stat, lambda value: value <= 0)
    zippedPos = plotlib.zipAgentData(births, valuesPos)
    zippedNeg = plotlib.zipAgentData(births, valuesNeg)
    binnedPos = plotlib.binData(zippedPos[0], zippedPos[1], args.bin_width)
    binnedNeg = plotlib.binData(zippedNeg[0], zippedNeg[1], args.bin_width)
    axes.plot(binnedPos[0], binnedPos[1])
    axes.plot(binnedNeg[0], binnedNeg[1])
axes.set_xlabel("Timestep")
axes.set_ylabel("Separable information")
axes.axhline(color = "0", dashes = plotlib.dashes, linewidth = 0.5)
figure.tight_layout()
figure.savefig("info-modification-{0}.pdf".format(args.stat))
