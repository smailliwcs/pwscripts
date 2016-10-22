import argparse
import plotlib
import sys

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("graph", metavar = "GRAPH", choices = ("output", "internal", "processing", "all"), help = "graph type")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
fileName = "density-{0}.txt".format(args.graph)
for run in runs:
    births = plotlib.getBirths(run)
    values = plotlib.readAgentData(run, fileName)
    if values is None:
        values = {}
        for agent in births:
            if agent % 1000 == 0:
                sys.stderr.write("{0}\n".format(agent))
            graph = plotlib.getGraph(run, agent, "birth", args.graph)
            count = 0
            for preNeuron in range(graph.size):
                for postNeuron in range(graph.size):
                    if graph.weights[preNeuron][postNeuron] is not None:
                        count += 1
            if args.graph == "all":
                countMax = graph.size * (graph.size - graph.getTypeCount("input") - 1)
            else:
                countMax = graph.size * (graph.size - 1)
            if countMax == 0:
                value = 0
            else:
                value = float(count) / countMax
            values[agent] = value
        plotlib.writeAgentData(run, fileName, values)
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel("Density")
figure.tight_layout()
figure.savefig("density-{0}.pdf".format(args.graph))
