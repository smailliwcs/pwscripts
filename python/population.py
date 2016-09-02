import argparse
import os
import plotlib

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    return parser.parse_args()

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
for run in runs:
    path = os.path.join(run, "population.txt")
    data = plotlib.getDataColumns(path, "Population")
    axes.plot(data["T"], data["Population"], linewidth = 0.5, alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel("Population")
figure.tight_layout()
figure.savefig("population.pdf")
