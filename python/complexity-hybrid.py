import argparse
import os
import plotlib

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS", help = "runs directory")
    parser.add_argument("format", metavar = "FORMAT", choices = ("bf", "ts"), help = "data format")
    parser.add_argument("--bin-width", metavar = "BIN_WIDTH", type = int, default = 1000, help = "bin width")
    return parser.parse_args()

args = parseArgs()
figure = plotlib.getFigure()
axes = figure.gca()
runs = list(plotlib.getRuns(args.runs))
for run in runs:
    births = plotlib.getBirths(run)
    values = {}
    path = os.path.join(run, "plots", "data", "complexity-hybrid-{0}.txt".format(args.format))
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            if args.format == "bf":
                agent, neuron, value = line.split()
                agent = int(agent)
                value = float(value)
                if neuron == "-":
                    value *= -1
                values[agent] = values.get(agent, 0) + value
            elif args.format == "ts":
                agent, value = line.split()
                value = float(value)
                if value != 0:
                    values[int(agent)] = value
    zipped = plotlib.zipAgentData(births, values)
    binned = plotlib.binData(zipped[0], zipped[1], args.bin_width)
    axes.plot(binned[0], binned[1], alpha = 1.0 / len(runs))
axes.set_xlabel("Timestep")
axes.set_ylabel("Complexity")
figure.tight_layout()
figure.savefig("complexity-hybrid-{0}.pdf".format(args.format))
