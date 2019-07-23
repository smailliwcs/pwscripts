import argparse
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
figure, axes1, axes2 = plot.getAxes(True)
axes1.tick_params(axis = "x", bottom = False, labelbottom = False)
axes1.set_xticks(XTICKS)
ymargin = 0.2
axes2.set_ylim(-ymargin, 2.0 + ymargin)
axes2.set_yticks((0.0, 1.0, 2.0))
axes2.set_ylabel("State space\nexpansion")
ymargin_display = ymargin / (2.0 + ymargin * 2) * plot.getBbox(axes2).height
ymargin = ymargin_display / (plot.getBbox(axes1).height - ymargin_display * 2)
axes1.set_ylim(-ymargin, 1.0 + ymargin)
axes1.set_ylabel("Neural activation")
axes2.set_xticks(XTICKS)
axes2.set_xlabel("Maximum synaptic weight")
kwargs = {
    "alpha": 0.05,
    "color": "C0",
    "linestyle": "None",
    "marker": "o",
    "markeredgewidth": 0.0,
    "markersize": plot.LINEWIDTH * 0.5,
    "rasterized": True
}

# Plot bifurcation diagram
path = os.path.join(args.run, "data", "bifurcation-{0}-{1}.txt.gz".format(args.stage, args.agent))
data = numpy.loadtxt(path)
axes1.plot(data[:, 0], data[:, NEURONS.index(args.neuron) + 1], **kwargs)

# Plot state space expansion
path = os.path.join(args.run, "data", "expansion-{0}-{1}.txt".format(args.stage, args.agent))
data = numpy.loadtxt(path)
axes2.plot(data[:, 0], data[: ,1], **kwargs)

# Save plot
figure.set_tight_layout(plot.PAD)
figure.savefig("bifurcation-{0}-{1}.pdf".format(args.stage, args.agent))
