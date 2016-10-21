import argparse
import plotlib
import random
import sys

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"), help = "life stage")
    parser.add_argument("graph", metavar = "GRAPH", choices = ("input", "output", "internal", "processing", "all"), help = "graph type")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

def shuffled(items):
    result = list(items)
    random.shuffle(result)
    return result

# https://arxiv.org/abs/0803.0476
def getModularity(W):
    def clean(W0):
        N = len(W0)
        W = [None] * N
        for i in range(N):
            W[i] = [0] * N
            for j in range(N):
                W0_ij = W0[i][j]
                if W0_ij is not None:
                    W[i][j] = abs(float(W0_ij))
        return W
    
    def init():
        global C, E, S, S_out, S_in
        C = range(N)
        E = [None] * N
        for i in range(N):
            E[i] = set()
        S = 0
        S_out = [0] * N
        S_in = [0] * N
        for i in range(N):
            for j in range(N):
                W_ij = W[i][j]
                if W_ij == 0:
                    continue
                E[i].add(j)
                E[j].add(i)
                S += W_ij
                S_out[i] += W_ij
                S_in[j] += W_ij
    
    def get_Q_ij(i, j):
        return (W[i][j] - S_out[i] * S_in[j] / S) / S
    
    def get_dQ_i(i, C_i):
        if C_i is None:
            sign = -1
            C_i = C[i]
        else:
            sign = 1
        dQ = 0
        for j in range(N):
            if C[j] == C_i and j != i:
                dQ += sign * get_Q_ij(i, j)
                dQ += sign * get_Q_ij(j, i)
        return dQ
    
    def get_Q():
        Q = 0
        for i in range(N):
            C_i = C[i]
            for j in range(N):
                if C[j] == C_i:
                    Q += get_Q_ij(i, j)
        return Q
    
    def group(W0):
        N0 = len(W0)
        C_map = {}
        for i, C_i in enumerate(set(C)):
            C_map[C_i] = i
        N = len(C_map)
        W = [None] * N
        for i in range(N):
            W[i] = [0] * N
        for i0 in range(N0):
            i = C_map[C[i0]]
            for j0 in range(N0):
                j = C_map[C[j0]]
                W[i][j] += W0[i0][j0]
        return W
    
    W = clean(W)
    N = len(W)
    Q0 = 0
    while True:
        init()
        if N <= 1 or S == 0:
            return 0
        while True:
            done = True
            for i in shuffled(range(N)):
                dQ = {}
                dQ[C[i]] = 0
                dQ0 = get_dQ_i(i, None)
                for j in E[i]:
                    C_j = C[j]
                    if C_j not in dQ:
                        dQ[C_j] = dQ0 + get_dQ_i(i, C_j)
                dQ_best = max(dQ.values())
                if dQ_best > 0:
                    C_best = [C_j for C_j, dQ_C_j in dQ.items() if dQ_C_j == dQ_best]
                    C[i] = random.choice(C_best)
                    done = False
            if done:
                break
        Q = get_Q()
        if Q - Q0 < 1e-6:
            return Q0
        W = group(W)
        N = len(W)
        Q0 = Q

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
fileName = "modularity-{0}-{1}.txt".format(args.stage, args.graph)
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
            graph = plotlib.getGraph(run, agent, args.stage, args.graph)
            if graph is None:
                continue
            values[agent] = getModularity(graph.weights)
        plotlib.writeAgentData(run, fileName, values)
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel("Modularity")
figure.tight_layout()
figure.savefig("modularity-{0}-{1}.pdf".format(args.stage, args.graph))
