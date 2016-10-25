import argparse
import os
import plotlib

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"), help = "life stage")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
for run in runs:
    births = plotlib.getBirths(run)
    values = {}
    path = os.path.join(run, "plots", "data", "onset-{0}.txt".format(args.stage))
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            agent, value = line.split()
            if value == "-":
                value = float("inf")
            else:
                value = float(value)
            values[int(agent)] = value
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width, "median")
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel("Onset of criticality")
axes.set_yscale("log")
figure.tight_layout()
figure.savefig("onset-{0}.pdf".format(args.stage))
