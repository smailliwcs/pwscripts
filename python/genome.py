import argparse
import gzip
import matplotlib
import numpy
import os
import plotlib
import sys

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", metavar = "RUN", help = "run directory")
    parser.add_argument("gene-min", metavar = "GENE_MIN", type = int, help = "minimum gene index")
    parser.add_argument("gene-max", metavar = "GENE_MAX", type = int, nargs = "?", help = "maximum gene index")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 250, help = "bin width")
    return parser.parse_args()

args = parseArgs()
geneMin = getattr(args, "gene-min")
geneMax = getattr(args, "gene-max")
if geneMax is None:
    geneMax = geneMin
births = plotlib.getBirths(args.run, plotlib.isNotSeedLifespan)
data = {}
for index in range(geneMin, geneMax + 1):
    data[index] = [[], []]
for agent in births:
    if agent % 1000 == 0:
        sys.stderr.write("{0}\n".format(agent))
    birth = births[agent]
    path = os.path.join(args.run, "genome", "agents", "genome_{0}.txt.gz".format(agent))
    with gzip.open(path) as f:
        for line, index in plotlib.readLines(f, geneMin, geneMax + 1):
            data[index][0].append(birth)
            data[index][1].append(int(line))
endStep = plotlib.getEndTimestep(args.run)
bins = [
    numpy.arange(0, endStep + args.bin_width, args.bin_width),
    numpy.arange(0, 257, 4)
]
titles = plotlib.getGeneTitles(args.run, geneMin, geneMax + 1)
with plotlib.getPdf("genome.pdf") as pdf:
    for index in range(geneMin, geneMax + 1):
        sys.stderr.write("{0}\n".format(index))
        figure = plotlib.getFigure()
        axes = figure.gca()
        image = axes.hist2d(data[index][0], data[index][1], bins, cmap = plotlib.colormaps["gray_partial_r"], norm = matplotlib.colors.LogNorm())[3]
        binned = plotlib.binData(data[index][0], data[index][1], args.bin_width)
        axes.plot(binned[0], binned[1], linewidth = 2, color = "1")
        axes.plot(binned[0], binned[1], linewidth = 1, color = "0")
        axes.set_xlabel("Timestep")
        axes.set_ylabel(titles[index])
        axes.set_ylim(0, 256)
        axes.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(32))
        colorbar = figure.colorbar(image)
        colorbar.set_label("Birth count")
        colorbar.locator = plotlib.LogLocator()
        colorbar.formatter = plotlib.LogFormatter()
        colorbar.update_ticks()
        figure.tight_layout()
        pdf.savefig(figure)
        plotlib.close(figure)
