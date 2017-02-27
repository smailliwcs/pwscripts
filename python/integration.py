import argparse
import os
import plotlib

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("metric", metavar = "METRIC", help = "metric")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
for run in runs:
    births = plotlib.getBirths(run)
    values = {}
    path = os.path.join(run, "plots", "data", "complexity-{0}.txt".format(args.metric))
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            agent, flag, value = line.split()
            if flag == "I":
                values[int(agent)] = float(value)
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel("Integration ({0})".format(args.metric))
figure.tight_layout()
figure.savefig("integration-{0}.pdf".format(args.metric))
