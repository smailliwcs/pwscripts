import argparse
import math
import metrics as metrics_mod
import operator
import os
import sys
import utility

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS")
    parser.add_argument("--condition", metavar = "CONDITION")
    return parser.parse_args()

args = parseArgs()
data = {}
quantiles = {}
metric = metrics_mod.Adaptivity()
metric.condition = args.condition
types = list(metrics_mod.Adaptivity.Type.getValues())
for type in types:
    sys.stderr.write("{0}\n".format(type))
    data[type] = []
    quantiles[type] = {}
    metric.type = type
    for run in utility.getRuns(args.runs):
        sys.stderr.write("{0}\n".format(run))
        quantiles[type][run] = {}
        metric.initialize(run)
        for agent, value in metric.read().iteritems():
            data[type].append({
                "run": run,
                "agent": agent,
                "value": value
            })
    data[type].sort(key = operator.itemgetter("value"), reverse = True)
    count = len(data[type])
    lastValue = None
    sameCount = 0
    for index, datum in enumerate(data[type]):
        if datum["value"] == lastValue:
            sameCount += 1
        else:
            sameCount = 0
        quantiles[type][datum["run"]][datum["agent"]] = 1.0 - float(index - sameCount) / (count - 1)
        lastValue = datum["value"]
if args.condition is None:
    name = "fitness.txt"
else:
    name = "fitness-{0}.txt".format(args.condition)
for run in utility.getRuns(args.runs):
    path = os.path.join(run, "data", name)
    with open(path, "w") as f:
        for agent in utility.getAgents(run):
            values = [quantiles[type][run][agent] for type in types]
            assert len(values) == 3
            fitness = math.sqrt(sum(map(lambda value: value ** 2, values)) / len(values))
            f.write("{0} {1}\n".format(agent, fitness))
