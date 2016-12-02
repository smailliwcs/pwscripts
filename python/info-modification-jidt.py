import argparse
import os
import plotlib

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"), help = "life stage")
    parser.add_argument("metric", metavar = "METRIC", choices = ("positive", "negative"), help = "metric type")
    parser.add_argument("stat", metavar = "STAT", choices = ("mean", "median", "sum"), help = "statistic")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

def getStatistic(values, metric, stat):
    if metric == "positive":
        predicate = lambda value: value >= 0
    elif metric == "negative":
        predicate = lambda value: value <= 0
    return plotlib.getStatistic(values, stat, predicate)

def getLabel(metric):
    return "{0} separable information".format(metric.capitalize())

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
for run in runs:
    births = plotlib.getBirths(run)
    data = {}
    path = os.path.join(run, "plots", "data", "info-storage-jidt-{0}.txt".format(args.stage))
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            agent, neuron, value = line.split()
            data.setdefault(int(agent), {})[int(neuron)] = float(value)
    path = os.path.join(run, "plots", "data", "info-transfer-jidt-apparent-{0}.txt".format(args.stage))
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            agent, preNeuron, postNeuron, value = line.split()
            if preNeuron == "-" and postNeuron == "-":
                continue
            data[int(agent)][int(postNeuron)] += float(value)
    values = {}
    for agent in data:
        values[agent] = getStatistic(data[agent].values(), args.metric, args.stat)
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel(getLabel(args.metric))
if args.metric == "positive":
    axes.set_ylim(bottom = max(0, axes.get_ylim()[0]))
elif args.metric == "negative":
    axes.set_ylim(top = min(0, axes.get_ylim()[1]))
    axes.invert_yaxis()
figure.tight_layout()
figure.savefig("info-modification-jidt-{0}-{1}-{2}.pdf".format(args.metric, args.stage, args.stat))
