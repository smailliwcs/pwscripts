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
for run in plotlib.getRunPaths(args.runs):
    path = os.path.join(run, "population.txt")
    data = plotlib.getDataColumns(path, "Population")
    axes.plot(data["T"], data["Population"], alpha = 0.2)
axes.set_xlabel("Timestep")
axes.set_ylabel("Population")
axes.set_ylim(bottom = 0)
figure.tight_layout()
figure.savefig("population.pdf")
