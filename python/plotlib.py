import datalib
import gzip
import math
import matplotlib
import matplotlib.backends.backend_pdf
import matplotlib.pyplot
import numpy
import os
import re
import scipy.stats

matplotlib.rcParams["axes.color_cycle"] = ["0"]
matplotlib.rcParams["font.family"] = "serif"
matplotlib.rcParams["font.serif"] = ["Times"]
matplotlib.rcParams["text.usetex"] = True
matplotlib.rcParams["text.latex.preamble"] = [
    r"\usepackage{amsmath}",
    r"\usepackage[T1]{fontenc}",
    r"\usepackage{newtxtext}",
    r"\usepackage{newtxmath}"
]

dashes = (4, 1)
gray_partial = matplotlib.colors.LinearSegmentedColormap.from_list("gray_partial", ("0", "0.9"))
gray_r_partial = matplotlib.colors.LinearSegmentedColormap.from_list("gray_r_partial", ("0.9", "0"))

synapseHeader = re.compile(r"^synapses (?P<agent>\d+) maxweight=(?P<weightMax>[^ ]+) numsynapses=(?P<synapses>\d+) numneurons=(?P<neurons>\d+) numinputneurons=(?P<inputs>\d+) numoutputneurons=(?P<outputs>\d+)$")

class Graph:
    def __init__(self, size, inputSize, outputSize):
        self.size = size
        self.inputSize = inputSize
        self.outputSize = outputSize
        self.internalSize = size - inputSize - outputSize
        self.processingSize = size - inputSize
        self.weights = [None] * size
        for neuron in range(size):
            self.weights[neuron] = [None] * size
    
    def getSubgraph(self, target, include):
        neurons = []
        if include:
            neurons.append(target)
        for neuron in range(self.size):
            if neuron == target:
                continue
            if self.weights[neuron][target] is not None or self.weights[target][neuron] is not None:
                neurons.append(neuron)
        size = len(neurons)
        inputSize = len([neuron for neuron in neurons if neuron < self.inputSize])
        outputSize = len([neuron for neuron in neurons if neuron >= self.inputSize and neuron < self.inputSize + self.outputSize])
        subgraph = Graph(size, inputSize, outputSize)
        for preIndex in range(size):
            preNeuron = neurons[preIndex]
            for postIndex in range(size):
                postNeuron = neurons[postIndex]
                subgraph.weights[preIndex][postIndex] = self.weights[preNeuron][postNeuron]
        return subgraph

class LogLocator(matplotlib.ticker.Locator):
    def __call__(self):
        bounds = self.axis.get_view_interval()
        start = int(math.floor(math.log10(bounds[0])))
        stop = int(math.ceil(math.log10(bounds[1])))
        ticks = [10 ** power for power in range(start, stop)]
        ticks.append(bounds[1])
        return ticks

class LogFormatter(matplotlib.ticker.Formatter):
    def __init__(self, formatSpec = "g"):
        self.formatSpec = formatSpec
    
    def __call__(self, tick, index):
        def getDistance(tick1, tick2):
            return math.log10(tick2 / tick1)
        
        bounds = self.axis.get_view_interval()
        if tick < bounds[1] and getDistance(tick, bounds[1]) / getDistance(bounds[0], bounds[1]) < 0.1:
            return ""
        else:
            return self.format(tick)
    
    def format(self, tick):
        return format(tick, self.formatSpec)

def binData(x, y, width, statistic = "mean"):
    xMax = max(x)
    bins = [0] + list(numpy.arange(1, xMax, width)) + [xMax]
    edges = list(numpy.arange(0, xMax, width)) + [xMax]
    binned = scipy.stats.binned_statistic(x, numpy.asarray(y), statistic, bins)[0]
    return edges, binned

def close(figure):
    matplotlib.pyplot.close(figure)

def getBirths(run, predicate = lambda row: True):
    return getLifeSpanData(run, predicate, "BirthStep")

def getData(path, tableNames = None):
    multiple = tableNames is None or isIterable(tableNames)
    if multiple:
        _tableNames = tableNames
    else:
        _tableNames = [tableNames]
    data = datalib.parse(path, _tableNames, True)
    if multiple:
        return data
    else:
        return data[tableNames]

def getDataColumns(path, tableName):
    data = getData(path, tableName)
    columns = {}
    for column in data.columns():
        columns[column.name] = column.data
    return columns

def getDataRows(path, tableName):
    data = getData(path, tableName)
    for row in data.rows():
        yield row

def getDeaths(run, predicate = lambda row: True):
    return getLifeSpanData(run, predicate, "DeathStep")

def getEndTimestep(run):
    with open(os.path.join(run, "endStep.txt")) as f:
        return int(f.readline())

def getFigure(width = 4, height = 3, fontSize = 8):
    matplotlib.rcParams["font.size"] = fontSize
    return matplotlib.pyplot.figure(figsize = (width, height))

def getGeneTitle(run, index):
    return getGeneTitles(run, index, index + 1)[index]

def getGeneTitles(run, start = 0, stop = float("inf")):
    titles = {}
    path = os.path.join(run, "genome", "meta", "geneindex.txt")
    for line, index in readLines(path, start, stop):
        titles[index] = line.split()[1]
    path = os.path.join(run, "genome", "meta", "genetitle.txt")
    for line, index in readLines(path, start, stop):
        titles[index] = line.split(" :: ")[0]
    return titles

def getGraph(run, agent, stage, sizeOnly = False):
    path = os.path.join(run, "brain", "synapses", "synapses_{0}_{1}.txt.gz".format(agent, stage))
    if not os.path.isfile(path):
        return None
    with gzip.open(path) as f:
        match = synapseHeader.match(f.readline())
        weightMax = float(match.group("weightMax"))
        neurons = int(match.group("neurons"))
        inputs = int(match.group("inputs"))
        outputs = int(match.group("outputs"))
        graph = Graph(neurons, inputs, outputs)
        if sizeOnly:
            return graph
        while True:
            line = f.readline()
            if line == "":
                break
            chunks = line.split()
            preNeuron = int(chunks[0])
            postNeuron = int(chunks[1])
            weight = float(chunks[2]) / weightMax
            if graph.weights[preNeuron][postNeuron] is None:
                graph.weights[preNeuron][postNeuron] = weight
            else:
                graph.weights[preNeuron][postNeuron] += weight
    return graph

def getGraphSize(run, agent, type):
    graph = getGraph(run, agent, "birth", True)
    if type == "all":
        return graph.size
    else:
        return getattr(graph, "{0}Size".format(type))

def getLifeSpanData(run, predicate, key = lambda row: row):
    values = {}
    path = os.path.join(run, "lifespans.txt")
    for row in getDataRows(path, "LifeSpans"):
        if not predicate(row):
            continue
        if isinstance(key, basestring):
            value = row[key]
        else:
            value = key(row)
        values[row["Agent"]] = value
    return values

def getLifeSpans(run, predicate = lambda row: True):
    return getLifeSpanData(run, predicate, lambda row: row["DeathStep"] - (row["BirthStep"] - 1))

def getMean(values, predicate = lambda value: True):
    count = 0
    total = 0
    for value in values:
        if predicate(value):
            count += 1
            total += value
    if count == 0:
        return 0
    else:
        return total / count

def getOffspring(run):
    values = {}
    path = os.path.join(run, "BirthsDeaths.log")
    with open(path) as f:
        for line in f:
            if line.startswith("%"):
                continue
            data = line.split()
            if data[1] == "BIRTH":
                agent = int(data[2])
                parent1 = int(data[3])
                parent2 = int(data[4])
                values.setdefault(parent1, []).append(agent)
                values.setdefault(parent2, []).append(agent)
    return values

def getPdf(path):
    return matplotlib.backends.backend_pdf.PdfPages(path)

def getRuns(path):
    if isRun(path):
        yield path
    else:
        for directory in os.listdir(path):
            subpath = os.path.join(path, directory)
            if isRun(subpath):
                yield subpath

def getScaleFormatter(power, formatSpec = "g"):
    divisor = 10 ** power
    formatter = lambda tick, position: format(tick / divisor, formatSpec)
    return matplotlib.ticker.FuncFormatter(formatter)

def getStatistic(values, statistic, predicate = lambda value: True):
    if statistic == "mean":
        return getMean(values, predicate)
    elif statistic == "sum":
        return getSum(values, predicate)
    else:
        raise ValueError("unrecognized statistic '{0}'".format(statistic))

def getSum(values, predicate = lambda value: True):
    total = 0
    for value in values:
        if predicate(value):
            total += value
    return total

def isIterable(obj):
    return hasattr(obj, "__iter__")

def isNotSeedLifeSpan(row):
    return not isSeedLifeSpan(row)

def isNotTruncatedLifeSpan(row):
    return not isTruncatedLifeSpan(row)

def isReadable(obj):
    return hasattr(obj, "readline")

def isRun(path):
    return os.path.isfile(os.path.join(path, "endStep.txt"))

def isSeedLifeSpan(row):
    return row["BirthReason"] == "SIMINIT"

def isTruncatedLifeSpan(row):
    return row["DeathReason"] == "SIMEND"

def makeDirectory(*args):
    path = os.path.join(*args)
    if not os.path.isdir(path):
        os.makedirs(path, 0755)
    return path

def printProperties(artist):
    return matplotlib.artist.getp(artist)

def readAgentData(run, fileName):
    values = {}
    path = os.path.join(run, "plots", "data", fileName)
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        for line in f:
            agent, value = line.split()
            values[int(agent)] = float(value)
    return values

def readLine(f, index):
    return list(readLines(f, index, index + 1))[0][0]

def readLines(f, start = 0, stop = float("inf")):
    if isReadable(f):
        return readLinesFromFile(f, start, stop)
    else:
        return readLinesFromPath(f, start, stop)

def readLinesFromFile(f, start, stop):
    for index in range(start):
        if f.readline() == "":
            return
    for index in range(start, stop):
        line = f.readline()
        if line == "":
            return
        yield line, index

def readLinesFromPath(path, start, stop):
    with open(path) as f:
        for line, index in readLinesFromFile(f, start, stop):
            yield line, index

def smoothData(values, window):
    weights = numpy.repeat(1.0, window) / window
    return numpy.convolve(values, weights, "same")

def writeAgentData(run, fileName, values):
    path = makeDirectory(run, "plots", "data")
    with open(os.path.join(path, fileName), "w") as f:
        for agent in values:
            f.write("{0} {1}\n".format(agent, values[agent]))

def zipAgentData(x, y):
    zipped = [[], []]
    for agent in x:
        if agent not in y:
            continue
        zipped[0].append(x[agent])
        zipped[1].append(y[agent])
    return zipped
