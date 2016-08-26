import argparse
import plotlib
import sys

inf = float("inf")

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("type", metavar = "TYPE", choices = ("global", "local"), help = "efficiency type")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

# https://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm
def getDistances(G):
    N = len(G)
    D = [None] * N
    for i in range(N):
        D_i = [inf] * N
        D_i[i] = 0
        D[i] = D_i
    for i in range(N):
        for j in range(N):
            w_ij = G[i][j]
            if w_ij is not None and w_ij != 0:
                D[i][j] = 1.0 / abs(w_ij)
    for k in range(N):
        for i in range(N):
            D_ik = D[i][k]
            for j in range(N):
                D_ikj = D_ik + D[k][j]
                if D[i][j] > D_ikj:
                    D[i][j] = D_ikj
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

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
fileName = "efficiency-{0}.txt".format(args.type)
for run in runs:
    births = plotlib.getBirths(run)
    values = plotlib.readAgentData(run, fileName)
    if values is None:
        values = {}
        for agent in births:
            if agent % 1000 == 0:
                sys.stderr.write("{0}\n".format(agent))
            graph = plotlib.getGraph(run, agent, "birth")
            if graph is None:
                continue
            if args.type == "global":
                distances = getDistances(graph.weights)
                value = getEfficiency(distances)
            elif args.type == "local":
                efficiencies = [None] * graph.size
                for neuron in range(graph.size):
                    subgraph = graph.getSubgraph(neuron, False)
                    if subgraph.size <= 1:
                        efficiencies[neuron] = 0
                    else:
                        distances = getDistances(subgraph.weights)
                        efficiencies[neuron] = getEfficiency(distances)
                value = plotlib.getMean(efficiencies)
            values[agent] = value
        plotlib.writeAgentData(run, fileName, values)
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel("{0} efficiency".format(args.type.title()))
figure.tight_layout()
figure.savefig("efficiency-{0}.pdf".format(args.type))
