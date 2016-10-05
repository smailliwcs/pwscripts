import argparse
import plotlib
import sys

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
fileName = "density.txt"
for run in runs:
    births = plotlib.getBirths(run)
    values = plotlib.readAgentData(run, fileName)
    if values is None:
        values = {}
        for agent in births:
            if agent % 1000 == 0:
                sys.stderr.write("{0}\n".format(agent))
            graph = plotlib.getGraph(run, agent, "birth")
            count = 0
            for preNeuron in range(graph.size):
                for postNeuron in range(graph.size):
                    if graph.weights[preNeuron][postNeuron] is not None:
                        assert preNeuron != postNeuron, "self-loop in agent {0}".format(agent)
                        count += 1
            countMax = graph.inputSize * graph.processingSize + graph.processingSize * (graph.processingSize - 1)
            values[agent] = float(count) / countMax
        plotlib.writeAgentData(run, fileName, values)
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel("Synapse density")
figure.tight_layout()
figure.savefig("density.pdf")
