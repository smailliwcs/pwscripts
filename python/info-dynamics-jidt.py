import argparse
import os
import plotlib

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"), help = "life stage")
    parser.add_argument("metric", metavar = "METRIC", choices = ("storage", "transfer-apparent", "transfer-complete", "modification"), help = "metric type")
    parser.add_argument("stat", metavar = "STAT", choices = ("mean", "median", "sum"), help = "statistic")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

def getLabel(metric):
    if metric == "storage":
        return "Active information storage"
    elif metric == "transfer-apparent":
        return "Apparent transfer entropy"
    elif metric == "transfer-complete":
        return "Complete transfer entropy"
    elif metric == "modification":
        return "Separable information"

def getValues(run, metric, stage):
    path = os.path.join(run, "plots", "data", "info-{0}-jidt-{1}.txt".format(metric, stage))
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            if metric == "storage":
                agent, neuron, value = line.split()
                yield int(agent), int(neuron), float(value)
            else:
                agent, preNeuron, postNeuron, value = line.split()
                if preNeuron == "-" and postNeuron == "-":
                    continue
                yield int(agent), int(postNeuron), float(value)

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
for run in runs:
    births = plotlib.getBirths(run)
    values = {}
    if args.metric == "modification":
        for agent, neuron, value in getValues(run, "storage", args.stage):
            values.setdefault(agent, {})[neuron] = value
        for agent, neuron, value in getValues(run, "transfer-apparent", args.stage):
            values[agent][neuron] += value
        for agent in values:
            values[agent] = plotlib.getStatistic(values[agent].values(), args.stat)
    else:
        for agent, neuron, value in getValues(run, args.metric, args.stage):
            values.setdefault(agent, []).append(value)
        for agent in values:
            values[agent] = plotlib.getStatistic(values[agent], args.stat)
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel(getLabel(args.metric))
axes.set_ylim(bottom = max(0, axes.get_ylim()[0]))
figure.tight_layout()
figure.savefig("info-{0}-jidt-{1}-{2}.pdf".format(args.metric, args.stage, args.stat))
