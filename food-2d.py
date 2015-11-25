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
    energies = plotlib.getDataColumns(path, "FoodEnergy")["Energy"]
    path = os.path.join(run, "population.txt")
    populations = plotlib.getDataColumns(path, "Population")["Population"]
    axes.plot(energies, populations, alpha = 1.0 / len(runs))
axes.set_xlabel(r"Food energy $(\times 10^3)$")
axes.set_xlim(left = 0)
axes.xaxis.set_major_formatter(plotlib.getScaleFormatter(3))
axes.set_ylabel("Population")
axes.set_ylim(bottom = 0)
figure.tight_layout()
figure.savefig("food-2d.pdf")
