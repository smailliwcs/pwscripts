import argparse
import plotlib
import sys

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"), help = "life stage")
    parser.add_argument("type", metavar = "TYPE", choices = ("excitatory", "inhibitory", "absolute"), help = "weight type")
    parser.add_argument("stat", metavar = "STAT", choices = ("mean", "median", "sum"), help = "statistic")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

def getLabel(type):
    metric = "strength"
    if type == "absolute":
        return metric.capitalize()
    else:
        return "{0} {1}".format(type.capitalize(), metric)

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
fileName = "strength-{0}-{1}-{2}.txt".format(args.type, args.stage, args.stat)
for run in runs:
    births = plotlib.getBirths(run)
    values = plotlib.readAgentData(run, fileName)
    if values is None:
        values = {}
        for agent in births:
            if agent % 1000 == 0:
                sys.stderr.write("{0}\n".format(agent))
            graph = plotlib.getGraph(run, agent, args.stage)
            if graph is None:
                continue
            weights = []
            for preNeuron in range(graph.size):
                for postNeuron in range(graph.size):
                    weight = graph.weights[preNeuron][postNeuron]
                    if weight is None:
                        continue
                    if args.type == "excitatory" and weight >= 0:
                        weights.append(weight)
                    elif args.type == "inhibitory" and weight <= 0:
                        weights.append(-weight)
                    elif args.type == "absolute":
                        weights.append(abs(weight))
            values[agent] = plotlib.getStatistic(weights, args.stat)
        plotlib.writeAgentData(run, fileName, values)
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel(getLabel(args.type))
figure.tight_layout()
figure.savefig("strength-{0}-{1}-{2}.pdf".format(args.type, args.stage, args.stat))
