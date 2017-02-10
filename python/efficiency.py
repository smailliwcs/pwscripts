import argparse
import plotlib
import sys

inf = float("inf")

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"), help = "life stage")
    parser.add_argument("graph", metavar = "GRAPH", choices = ("input", "output", "internal", "processing", "all"), help = "graph type")
    parser.add_argument("metric", metavar = "METRIC", choices = ("global", "local"), help = "metric type")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

# https://en.wikipedia.org/wiki/Dijkstra's_algorithm
def getDistances(W):
    N = len(W)
    L = {}
    for i in range(N):
        L[i] = {}
        for j in range(N):
            if j == i:
                continue
            W_ij = W[i][j]
            if W_ij is not None and W_ij != 0:
                L[i][j] = 1.0 / abs(W_ij)
    D = {}
    for i in range(N):
        D[i] = {}
        for j in range(N):
            if j == i:
                D[i][j] = 0
            else:
                D[i][j] = inf
        Q = set(range(N))
        while len(Q) > 0:
            j = min(Q, key = lambda j: D[i][j])
            D_ij = D[i][j]
            for k, L_jk in L[j].items():
                D_ijk = D_ij + L_jk
                if D_ijk < D[i][k]:
                    D[i][k] = D_ijk
            Q.remove(j)
    return D

def getEfficiency(D):
    N = len(D)
    sum_D_inv = 0
    for i in range(N):
        for j in range(N):
            if j == i:
                continue
            sum_D_inv += 1.0 / D[i][j]
    return sum_D_inv / (N * (N - 1))

def getLabel(metric):
    return "{0} efficiency".format(metric.capitalize())

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
fileName = "efficiency-{0}-{1}-{2}.txt".format(args.metric, args.stage, args.graph)
for run in runs:
    births = plotlib.getBirths(run)
    values = plotlib.readAgentData(run, fileName)
    if values is None:
        values = {}
    if len(values) < len(births):
        for agent in births:
            if agent % 100 == 0:
                plotlib.writeAgentData(run, fileName, values)
                sys.stderr.write("{0}\n".format(agent))
            if agent in values:
                continue
            graph = plotlib.Graph.read(run, agent, args.stage, args.graph)
            if graph is None:
                continue
            if args.metric == "global":
                if graph.size <= 1:
                    value = 0
                else:
                    distances = getDistances(graph.weights)
                    value = getEfficiency(distances)
            elif args.metric == "local":
                efficiencies = [None] * graph.size
                for neuron in range(graph.size):
                    neighborhood = graph.getNeighborhood(neuron, False)
                    if neighborhood.size <= 1:
                        efficiencies[neuron] = 0
                    else:
                        distances = getDistances(neighborhood.weights)
                        efficiencies[neuron] = getEfficiency(distances)
                value = plotlib.getMean(efficiencies)
            values[agent] = value
        plotlib.writeAgentData(run, fileName, values)
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel(getLabel(args.metric))
figure.tight_layout()
figure.savefig("efficiency-{0}-{1}-{2}.pdf".format(args.metric, args.stage, args.graph))
