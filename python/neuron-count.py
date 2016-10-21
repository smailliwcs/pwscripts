import argparse
import plotlib
import sys

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("graph", metavar = "GRAPH", choices = ("input", "output", "internal", "processing", "all"), help = "graph type")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

def getLabel(graph):
    name = "neuron count"
    if graph == "all":
        return name.capitalize()
    else:
        return "{0} {1}".format(graph.capitalize(), name)

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
fileName = "neuron-count-{0}.txt".format(args.graph)
for run in runs:
    births = plotlib.getBirths(run)
    values = plotlib.readAgentData(run, fileName)
    if values is None:
        values = {}
        for agent in births:
            if agent % 1000 == 0:
                sys.stderr.write("{0}\n".format(agent))
            values[agent] = plotlib.getGraphSize(run, agent, args.graph)
        plotlib.writeAgentData(run, fileName, values)
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel(getLabel(args.graph))
figure.tight_layout()
figure.savefig("neuron-count-{0}.pdf".format(args.graph))
