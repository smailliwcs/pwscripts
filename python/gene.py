import argparse
import gzip
import matplotlib
import os
import plotlib
import sys

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("gene", metavar = "GENE", type = int, help = "gene index")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
for run in runs:
    births = plotlib.getBirths(run)
    values = {}
    for agent in births:
        if agent % 1000 == 0:
            sys.stderr.write("{0}\n".format(agent))
        path = os.path.join(run, "genome", "agents", "genome_{0}.txt.gz".format(agent))
        with gzip.open(path) as f:
            line = plotlib.readLine(f, args.gene)
            values[agent] = int(line)
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel(plotlib.getGeneTitle(runs[0], args.gene))
axes.set_ylim(0, 256)
axes.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(32))
figure.tight_layout()
figure.savefig("gene-{0}.pdf".format(args.gene))
