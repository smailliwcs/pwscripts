import argparse
import graph as graph_mod
import matplotlib.pyplot
import numpy

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("run", metavar = "RUN")
    parser.add_argument("agent", metavar = "AGENT", type = int)
    parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"))
    parser.add_argument("--passive", action = "store_true")
    return parser.parse_args()

matplotlib.rcParams["axes.grid"] = True
matplotlib.rcParams["figure.figsize"] = (3.0, 3.0)
matplotlib.rcParams["font.family"] = "serif"
matplotlib.rcParams["font.serif"] = ["Times"]
matplotlib.rcParams["font.size"] = 8.0
matplotlib.rcParams["grid.alpha"] = 0.2
matplotlib.rcParams["grid.linestyle"] = "-"
matplotlib.rcParams["image.cmap"] = "bwr"
matplotlib.rcParams["image.interpolation"] = "none"
matplotlib.rcParams["savefig.format"] = "pdf"
matplotlib.rcParams["text.usetex"] = True
matplotlib.rcParams["text.latex.preamble"] = [
    r"\usepackage{amsmath}",
    r"\usepackage[T1]{fontenc}",
    r"\usepackage{newtxtext}",
    r"\usepackage{newtxmath}"
]
args = parseArgs()
graph = graph_mod.Graph.read(args.run, args.agent, args.stage, graph_mod.Graph.Type.ALL, args.passive)
weights = [None] * graph.size
for preNode in xrange(graph.size):
    weights[preNode] = [None] * graph.size
    for postNode in xrange(graph.size):
        weight = graph.weights[preNode][postNode]
        if weight is None:
            weight = 0.0
        weights[preNode][postNode] = weight
figure = matplotlib.pyplot.figure()
axes = figure.gca()
axes.imshow(weights, vmin = -1.0, vmax = 1.0)
inputCount = graph.getTypeCount(graph_mod.Graph.Type.INPUT)
outputCount = graph.getTypeCount(graph_mod.Graph.Type.OUTPUT)
ticks = [inputCount - 0.5, inputCount + outputCount - 0.5]
axes.set_xticks(ticks)
axes.set_yticks(ticks)
axes.set_xticklabels([])
axes.set_yticklabels([])
# TODO: Add group labels
matplotlib.pyplot.tight_layout()
figure.savefig("brain-{0}-{1}.pdf".format(args.agent, args.stage))
