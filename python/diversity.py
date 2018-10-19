import argparse
import collections
import numpy
import operator
import os
import sys
import utility

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", metavar = "RUNS")
    parser.add_argument("group_size", metavar = "GROUP_SIZE", type = int, choices = tuple(xrange(8)))
    return parser.parse_args()

args = parseArgs()
titles = None
values = collections.defaultdict(list)
for run in utility.getRuns(args.runs):
    if titles is None:
        titles = utility.getGeneTitles(run, False)
    path = os.path.join(run, "data", "diversity-{0}-mean.txt".format(args.group_size))
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            chunks = line.split()
            assert chunks[0] == "mean"
            for index, value in enumerate(chunks[1:]):
                values[index].append(float(value))
means = {index: numpy.mean(values[index]) for index in values}
for index, mean in sorted(means.iteritems(), key = operator.itemgetter(1)):
    sys.stdout.write("{0} {1:.3f}\n".format(titles[index], mean))
