import argparse
import math
import matplotlib.gridspec
import matplotlib.pyplot
import numpy
import os
import plot

NEURONS = ("eat", "mate", "fight", "move", "turn", "light", "focus")
XTICKS = (0.0, 8.0, 20.0, 40.0, 60.0, 80.0, 100.0)

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", metavar = "RUN")
    parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"))
    parser.add_argument("agent", metavar = "AGENT", type = int)
    parser.add_argument("neuron", metavar = "NEURON", choices = NEURONS)
    return parser.parse_args()

# Configure plot
args = parseArgs()
figure = matplotlib.pyplot.figure()
figure.set_size_inches(plot.SIZE, plot.SIZE)
grid = matplotlib.gridspec.GridSpec(4, 1)
axes1 = figure.add_subplot(grid[0:-1, :])
axes2 = figure.add_subplot(grid[-1, :])
axes1.tick_params(axis = "x", bottom = False, labelbottom = False)
axes1.set_xticks(XTICKS)
axes1.set_ylim(-0.056, 1.056)
axes1.set_ylabel("Neural activation")
axes2.set_xticks(XTICKS)
axes2.set_xlabel("Maximum synaptic weight")
axes2.set_ylim(-0.5, 2.5)
axes2.set_yticks((0.0, 1.0, 2.0))
axes2.set_ylabel("PSE")
kwargs = {
    "alpha": 0.1,
    "color": plot.COLOR[0],
    "linestyle": "None",
    "marker": "o",
    "markeredgewidth": 0.0,
    "markersize": 0.6,
    "rasterized": True
}

# Plot bifurcation diagram
path = os.path.join(args.run, "data", "bifurcation-{0}-{1}.txt.gz".format(args.stage, args.agent))
data = numpy.loadtxt(path)
axes1.plot(data[:, 0], data[:, NEURONS.index(args.neuron) + 1], **kwargs)

# Plot phase space expansion
path = os.path.join(args.run, "data", "expansion-{0}-{1}.txt".format(args.stage, args.agent))
data = numpy.loadtxt(path)
axes2.plot(data[:, 0], data[: ,1], **kwargs)

# Save plot
figure.set_tight_layout(plot.PAD)
figure.savefig("bifurcation-{0}-{1}.pdf".format(args.stage, args.agent))
