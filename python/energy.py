import argparse
import os
import plotlib
import sys

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("type", metavar = "TYPE", choices = ("in", "out", "total"), help = "energy type")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRunPaths(args.runs))
fileName = "energy-{0}.txt".format(args.type)
for run in runs:
    lifeSpans, births, deaths = plotlib.getLifeSpans(run)
    energies = plotlib.readAgentData(run, fileName)
    if energies is None:
        energies = {}
        for agent in lifeSpans:
            if agent % 1000 == 0:
                sys.stderr.write("{0}\n".format(agent))
            path = os.path.join(run, "energy", args.type, "agent_{0}.txt".format(agent))
            data = plotlib.getDataColumns(path, "AgentEnergy{0}".format(args.type.title()))
            energies[agent] = sum(data["Energy"]) / lifeSpans[agent]
        plotlib.saveAgentData(run, fileName, energies)
    zipped = plotlib.zipAgentData(deaths, energies)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
if args.type == "total":
    ylabel = "Total energy"
else:
    ylabel = "Energy {0}".format(args.type)
axes.set_ylabel(ylabel)
axes.set_ylim(bottom = 0)
figure.tight_layout()
figure.savefig("energy-{0}.pdf".format(args.type))