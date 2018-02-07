import argparse
import graph as graph_mod
import matplotlib.pyplot
import numpy

matplotlib.rcParams["figure.figsize"] = (5.0, 5.0)
matplotlib.rcParams["image.interpolation"] = "none"
matplotlib.rcParams["savefig.format"] = "pdf"
parser = argparse.ArgumentParser()
parser.add_argument("run", metavar = "RUN")
parser.add_argument("agent", metavar = "AGENT", type = int)
parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"))
parser.add_argument("--save", action = "store_true")
args = parser.parse_args()
graph = graph_mod.Graph.read(args.run, args.agent, args.stage, graph_mod.GraphType.ALL)
weights = [None] * graph.size
for nodeOut in xrange(graph.size):
    weights[nodeOut] = [None] * graph.size
    for nodeIn in xrange(graph.size):
        weight = graph.weights[nodeOut][nodeIn]
        if nodeIn == nodeOut:
            assert weight is None
            weight = float("nan")
        elif weight is None:
            weight = 0.0
        weights[nodeOut][nodeIn] = weight
figure = matplotlib.pyplot.figure()
axes = figure.gca()
cmap = matplotlib.cm.get_cmap("bwr")
cmap.set_bad("0.5")
axes.imshow(weights, vmin = -1.0, vmax = 1.0, cmap = cmap)
axes.set_xticks([])
axes.set_yticks([])
inputCount = graph.getNodeCount(graph_mod.GraphType.INPUT)
outputCount = graph.getNodeCount(graph_mod.GraphType.OUTPUT)
def axline(x, alpha):
    axes.axhline(x, color = "0", alpha = alpha)
    axes.axvline(x, color = "0", alpha = alpha)
for node in xrange(graph.size):
    axline(node - 0.5, 0.1)
axline(inputCount - 0.5, 0.5)
axline(inputCount + outputCount - 0.5, 0.5)
if args.save:
    matplotlib.pyplot.tight_layout()
    figure.savefig("brain-{0}-{1}".format(args.agent, args.stage))
else:
    matplotlib.pyplot.show()
