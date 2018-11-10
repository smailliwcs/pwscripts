import argparse
import graph as graph_mod
import matplotlib
import matplotlib.cm
import sys
import utility

parser = argparse.ArgumentParser()
parser.add_argument("run", metavar = "RUN")
parser.add_argument("agent", metavar = "AGENT", type = int)
parser.add_argument("stage", metavar = "STAGE", choices = ("incept", "birth", "death"))
parser.add_argument("format", metavar = "FORMAT", choices = ("matrix", "text"))
args = parser.parse_args()
graph = graph_mod.Graph.read(args.run, args.agent, args.stage, graph_mod.GraphType.ALL)
if args.format == "matrix":
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
    matplotlib.use("TkAgg")
    import matplotlib.pyplot
    import plot
    figure = matplotlib.pyplot.figure()
    axes = figure.gca()
    cmap = matplotlib.cm.RdBu
    cmap.set_bad("0.5")
    axes.imshow(weights, vmin = -1.0, vmax = 1.0, cmap = cmap)
    axes.set_xticks(())
    axes.set_yticks(())
    inputCount = graph.getNodeCount(graph_mod.GraphType.INPUT)
    outputCount = graph.getNodeCount(graph_mod.GraphType.OUTPUT)
    def axline(x, alpha):
        kwargs = {"color": "0.0", "alpha": alpha}
        axes.axhline(x, **kwargs)
        axes.axvline(x, **kwargs)
    for node in xrange(graph.size):
        axline(node - 0.5, 0.1)
    axline(inputCount - 0.5, 0.5)
    axline(inputCount + outputCount - 0.5, 0.5)
    figure.set_tight_layout(plot.PAD)
    matplotlib.pyplot.show()
elif args.format == "text":
    node = 0
    counts = utility.getNeuronCounts(args.run)[args.agent]
    for nerve in utility.getNerves(args.run):
        if nerve in ("Red", "Green", "Blue"):
            type = "Input-" + nerve
        elif node < counts["Input"]:
            type = "Input-Other"
        else:
            type = "Output"
        for index in xrange(counts[nerve]):
            sys.stdout.write("node {0} {1}\n".format(node, type))
            node += 1
    for index in xrange(counts["Internal"]):
        sys.stdout.write("node {0} Internal\n".format(node))
        node += 1
    for nodeOut in xrange(graph.size):
        for nodeIn in xrange(graph.size):
            weight = graph.weights[nodeOut][nodeIn]
            if weight is None:
                continue
            sys.stdout.write("edge {0} {1} {2}\n".format(nodeOut, nodeIn, weight))
else:
    assert False
