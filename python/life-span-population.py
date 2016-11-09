import argparse
import matplotlib
import os
import plotlib

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", metavar = "RUN", help = "run directory")
    parser.add_argument("--bins", metavar = "BINS", type = int, default = 100, help = "bin count")
    return parser.parse_args()

def getPopulations(run):
    path = os.path.join(run, "population.txt")
    populationData = plotlib.getDataColumns(path, "Population")["Population"]
    lifeSpanData = plotlib.getLifeSpanData(run, plotlib.isNotTruncatedLifeSpan)
    populations = {}
    for agent in lifeSpanData:
        birth = lifeSpanData[agent]["BirthStep"]
        death = lifeSpanData[agent]["DeathStep"]
        populations[agent] = plotlib.getMean(populationData[birth + 1:death + 1])
    return populations

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
populations = getPopulations(args.run)
lifeSpans = plotlib.getLifeSpans(args.run, plotlib.isNotTruncatedLifeSpan)
zipped = plotlib.zipAgentData(populations, lifeSpans)
image = axes.hist2d(zipped[0], zipped[1], args.bins, cmap = plotlib.colormaps["gray_partial_r"], norm = matplotlib.colors.LogNorm())[3]
trend = plotlib.getTrend(zipped[0], zipped[1])
axes.plot(trend[0], trend[1], linewidth = 2, color = "1")
axes.plot(trend[0], trend[1], linewidth = 1, color = "0")
axes.set_xlabel("Population")
axes.set_ylabel("Life span")
colorbar = figure.colorbar(image)
colorbar.set_label("Agent count")
colorbar.locator = plotlib.LogLocator()
colorbar.formatter = plotlib.LogFormatter()
colorbar.update_ticks()
figure.tight_layout()
figure.savefig("life-span-population.pdf")
