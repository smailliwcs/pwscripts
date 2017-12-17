from pylab import *
import argparse
import os
import sys
import utility

parser = argparse.ArgumentParser()
parser.add_argument("run", metavar = "RUN")
args = parser.parse_args()
ion()

def population():
    x = []
    y = []
    with open(os.path.join(args.run, "population.txt")) as f:
        for line in f:
            if line == "\n" or line.startswith("#"):
                continue
            chunks = line.split()
            x.append(int(chunks[0]))
            y.append(int(chunks[1]))
    subplot(3, 1, 1)
    plot(x, y)

def food():
    x = []
    ys = []
    cs = ["g", "r"]
    with open(os.path.join(args.run, "energy/food.txt")) as f:
        for line in f:
            if line.startswith("#@L"):
                for index in xrange(len(line.split()) - 2):
                    ys.append([])
                continue
            elif line == "\n" or line.startswith("#"):
                continue
            chunks = line.split()
            x.append(int(chunks[0]))
            for index in xrange(len(ys)):
                ys[index].append(float(chunks[1 + index]))
    subplot(3, 1, 2)
    for index in xrange(len(ys)):
        plot(x, ys[index], cs[index % len(cs)])

def lifespans():
    y = []
    with open(os.path.join(args.run, "lifespans.txt")) as f:
        for line in f:
            if line == "\n" or line.startswith("#"):
                continue
            chunks = line.split()
            y.append(int(chunks[3]) - int(chunks[1]))
    subplot(3, 1, 3)
    hist(y, bins = 20, range = [0, 500])

def _plot(fn):
    try:
        fn()
    except Exception as ex:
        sys.stderr.write("{0}\n".format(ex))

while True:
    _plot(population)
    _plot(food)
    _plot(lifespans)
    pause(10)
    clf()
