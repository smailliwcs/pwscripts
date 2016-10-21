import argparse
import plotlib

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"), help = "life stage")
    parser.add_argument("graph", metavar = "GRAPH", choices = ("input", "output", "internal", "processing", "all"), help = "graph type")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
for run in runs:
    births = plotlib.getBirths(run)
    localValues = plotlib.readAgentData(run, "efficiency-local-{0}-{1}.txt".format(args.stage, args.graph))
    globalValues = plotlib.readAgentData(run, "efficiency-global-{0}-{1}.txt".format(args.stage, args.graph))
    values = {}
    for agent in births:
        if agent not in localValues or agent not in globalValues:
            continue
        values[agent] = localValues[agent] * globalValues[agent]
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel("Small-worldness")
figure.tight_layout()
figure.savefig("small-worldness-{0}-{1}.pdf".format(args.stage, args.graph))
