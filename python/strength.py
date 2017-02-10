import argparse
import plotlib
import sys

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"), help = "life stage")
    parser.add_argument("graph", metavar = "GRAPH", choices = ("input", "output", "internal", "processing", "all"), help = "graph type")
    parser.add_argument("metric", metavar = "METRIC", choices = ("excitatory", "inhibitory", "absolute"), help = "metric type")
    parser.add_argument("stat", metavar = "STAT", choices = ("mean", "median", "sum"), help = "statistic")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

def getWeight(metric, graph, preNeuron, postNeuron):
    weight = graph.weights[preNeuron][postNeuron]
    if weight is None:
        return 0
    elif metric == "excitatory":
        return max(0, weight)
    elif metric == "inhibitory":
        return max(0, -weight)
    elif metric == "absolute":
        return abs(weight)

def getLabel(metric):
    name = "strength"
    if metric == "absolute":
        return name.capitalize()
    else:
        return "{0} {1}".format(metric.capitalize(), name)

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
fileName = "strength-{0}-{1}-{2}-{3}.txt".format(args.metric, args.stage, args.graph, args.stat)
for run in runs:
    births = plotlib.getBirths(run)
    values = plotlib.readAgentData(run, fileName)
    if values is None:
        values = {}
        for agent in births:
            if agent % 1000 == 0:
                sys.stderr.write("{0}\n".format(agent))
            graph = plotlib.Graph.read(run, agent, args.stage, args.graph)
            if graph is None:
                continue
            strengths = [0] * graph.size
            for neuron1 in range(graph.size):
                for neuron2 in range(neuron1 + 1, graph.size):
                    weight1To2 = getWeight(args.metric, graph, neuron1, neuron2)
                    weight2To1 = getWeight(args.metric, graph, neuron2, neuron1)
                    strengths[neuron1] += weight1To2 + weight2To1
                    strengths[neuron2] += weight1To2 + weight2To1
            values[agent] = plotlib.getStatistic(strengths, args.stat)
        plotlib.writeAgentData(run, fileName, values)
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel(getLabel(args.metric))
figure.tight_layout()
figure.savefig("strength-{0}-{1}-{2}-{3}.pdf".format(args.metric, args.stage, args.graph, args.stat))
