import argparse
import os
import plotlib
import sys

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("metric", metavar = "METRIC", choices = ("in", "out", "total"), help = "metric type")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

def getLabel(metric):
    name = "energy"
    if metric == "total":
        return name.capitalize()
    else:
        return "{0} {1}".format(name.capitalize(), metric)

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
fileName = "agent-energy-{0}.txt".format(args.metric)
for run in runs:
    births = plotlib.getBirths(run)
    lifespans = plotlib.getLifespans(run)
    values = plotlib.readAgentData(run, fileName)
    if values is None:
        values = {}
        for agent in births:
            if agent % 1000 == 0:
                sys.stderr.write("{0}\n".format(agent))
            path = os.path.join(run, "energy", args.metric, "agent_{0}.txt".format(agent))
            data = plotlib.getDataColumns(path, "AgentEnergy{0}".format(args.metric.capitalize()))
            if lifespans[agent] == 0:
                continue
            values[agent] = sum(data["Energy"]) / lifespans[agent]
        plotlib.writeAgentData(run, fileName, values)
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel(getLabel(args.metric))
figure.tight_layout()
figure.savefig("agent-energy-{0}.pdf".format(args.metric))
