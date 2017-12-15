from pylab import *
import argparse
import os
import utility

parser = argparse.ArgumentParser()
parser.add_argument("run", metavar = "RUN")
args = parser.parse_args()

subplot(3, 1, 1)
x = []
y = []
with open(os.path.join(args.run, "population.txt")) as f:
    for line in f:
        if line == "\n" or line.startswith("#"):
            continue
        chunks = line.split()
        x.append(int(chunks[0]))
        y.append(int(chunks[1]))
plot(x, y)

subplot(3, 1, 2)
x = []
ys = []
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
for index in xrange(len(ys)):
    plot(x, ys[index])

subplot(3, 1, 3)
y = []
with open(os.path.join(args.run, "lifespans.txt")) as f:
    for line in f:
        if line == "\n" or line.startswith("#"):
            continue
        chunks = line.split()
        y.append(int(chunks[3]) - int(chunks[1]))
hist(y, bins = 50, range = [0, 1000])
xticks(range(0, 1001, 100))

show()
