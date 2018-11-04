import argparse
import math
import metrics as metrics_mod
import numpy
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
caps = {}
metric = metrics_mod.Adaptivity()
metric.condition = args.condition
types = list(metrics_mod.Adaptivity.Type.getValues())
for type in types:
    sys.stderr.write("{0}\n".format(type))
    data[type] = {}
    values = []
    metric.type = type
    for run in utility.getRuns(args.runs):
        sys.stderr.write("{0}\n".format(run))
        data[type][run] = {}
        metric.initialize(run)
        for agent, value in metric.read().iteritems():
            data[type][run][agent] = {
                "run": run,
                "agent": agent,
                "value": value
            }
            values.append(value)
    caps[type] = numpy.nanpercentile(values, 99.9)
if args.condition is None:
    name = "fitness.txt"
else:
    name = "fitness-{0}.txt".format(args.condition)
for run in utility.getRuns(args.runs):
    path = os.path.join(run, "data", name)
    with open(path, "w") as f:
        for agent in utility.getAgents(run):
            values = []
            for type in types:
                value = data[type][run][agent]["value"] / caps[type]
                if value > 1.0:
                    value = 1.0
                values.append(value)
            fitness = numpy.nanmean(values)
            f.write("{0} {1}\n".format(agent, fitness))
