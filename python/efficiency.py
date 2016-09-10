import argparse
import plotlib
import sys

inf = float("inf")

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"), help = "life stage")
    parser.add_argument("type", metavar = "TYPE", choices = ("global", "local"), help = "efficiency type")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

# https://en.wikipedia.org/wiki/Dijkstra's_algorithm
def getDistances(G):
    N = len(G)
    L = {}
    for i in range(N):
        L_i = {}
        for j in range(N):
            if j == i:
                continue
            w_ij = G[i][j]
            if w_ij is not None and w_ij != 0:
                L_i[j] = 1.0 / abs(w_ij)
        L[i] = L_i
    D = {}
    for i in range(N):
        D_i = {}
        for j in range(N):
            if j == i:
                D_i[j] = 0
            else:
                D_i[j] = inf
        Q = set(range(N))
        while len(Q) > 0:
            j = min(Q, key = lambda j: D_i[j])
            D_ij = D_i[j]
            for k, L_jk in L[j].items():
                D_ijk = D_ij + L_jk
                if D_ijk < D_i[k]:
                    D_i[k] = D_ijk
            Q.remove(j)
        D[i] = D_i
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
    if len(values) < len(births):
        for agent in births:
            if agent % 100 == 0:
                plotlib.writeAgentData(run, fileName, values)
                sys.stderr.write("{0}\n".format(agent))
            if agent in values:
                continue
            graph = plotlib.getGraph(run, agent, args.stage)
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
