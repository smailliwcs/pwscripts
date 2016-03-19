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
runs = list(plotlib.getRunPaths(args.runs))
for run in runs:
    path = os.path.join(run, "energy", "food.txt")
    data = plotlib.getDataColumns(path, "FoodEnergy")
    axes.plot(data["Timestep"], data["Energy"], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel(r"Food energy $(\times 10^3)$")
axes.set_ylim(bottom = 0)
axes.yaxis.set_major_formatter(plotlib.getScaleFormatter(3))
figure.tight_layout()
figure.savefig("food-1d.pdf")
