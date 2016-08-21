import argparse
import plotlib
import sys

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("type", metavar = "TYPE", choices = ("pos", "neg", "both", "abs"), help = "weight type")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

def getValues(type, births):
    fileName = "synapse-weight-{0}.txt".format(type)
    values = plotlib.readAgentData(run, fileName)
    if values is None:
        values = {}
        for agent in births:
            if agent % 1000 == 0:
                sys.stderr.write("{0}\n".format(agent))
            graph = plotlib.getGraph(run, agent, "birth")
            neuronCount = len(graph)
            weights = []
            for preNeuron in range(neuronCount):
                for postNeuron in range(neuronCount):
                    weight = graph[preNeuron][postNeuron]
                    if weight is None:
                        continue
                    if args.type == "pos" and weight >= 0:
                        weights.append(weight)
                    elif args.type == "neg" and weight <= 0:
                        weights.append(-weight)
                    elif args.type == "abs":
                        weights.append(abs(weight))
            values[agent] = plotlib.getMean(weights)
        plotlib.writeAgentData(run, fileName, values)
    return values

def getLabel(type):
    metric = "Synapse weight"
    if type == "pos":
        return "{0} (excitatory)".format(metric)
    elif type == "neg":
        return "{0} (inhibitory)".format(metric)
    else:
        return metric

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
if args.type == "both":
    types = ("pos", "neg")
else:
    types = (args.type,)
for run in runs:
    births = plotlib.getBirths(run)
    for type in types:
        values = getValues(type, births)
        zipped = plotlib.zipAgentData(births, values)
        binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
        if args.type == "both" and type == "neg":
            style = "dotted"
        else:
            style = "solid"
        axes.plot(binned[0], binned[1], linestyle = style, alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel(getLabel(args.type))
axes.set_ylim(bottom = 0)
figure.tight_layout()
figure.savefig("synapse-weight-{0}.pdf".format(args.type))
