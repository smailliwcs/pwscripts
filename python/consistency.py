import argparse
import numpy
import os
import plotlib
import subprocess
import sys

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("base", metavar = "BASE", type = int, choices = range(8), help = "base-2 log of group size")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
for run in runs:
    endStep = plotlib.getEndTimestep(run)
    x = numpy.linspace(0, endStep, endStep / args.bin_width + 1)
    agents = [None] * len(x)
    for index in range(len(x)):
        agents[index] = []
    births = plotlib.getBirths(run)
    for agent in births:
        birth = births[agent]
        for index in range(len(x)):
            if birth <= x[index]:
                agents[index].append(agent)
                break
    y = [None] * len(x)
    for index in range(len(x)):
        sys.stderr.write("{0}\n".format(int(x[index])))
        process = subprocess.Popen(("infodynamics", "Consistency", str(args.base)), stdin = subprocess.PIPE, stdout = subprocess.PIPE)
        paths = [os.path.join(run, "genome", "agents", "genome_{0}.txt.gz".format(agent)) for agent in agents[index]]
        values = []
        for line in process.communicate(os.linesep.join(paths))[0].splitlines():
            values.append(float(line))
        y[index] = plotlib.getMean(values)
    axes.plot(x, y, alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel("Genetic consistency")
figure.tight_layout()
figure.savefig("consistency-{0}.pdf".format(args.base))
