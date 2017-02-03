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
import viridis

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
colormaps = {
    "gray": matplotlib.colors.LinearSegmentedColormap.from_list("gray", ("0", "1")),
    "gray_r": matplotlib.colors.LinearSegmentedColormap.from_list("gray_r", ("1", "0")),
    "gray_partial": matplotlib.colors.LinearSegmentedColormap.from_list("gray_partial", ("0", "0.9")),
    "gray_partial_r": matplotlib.colors.LinearSegmentedColormap.from_list("gray_partial_r", ("0.9", "0")),
    "viridis": matplotlib.colors.ListedColormap(viridis.data, "viridis"),
    "viridis_r": matplotlib.colors.ListedColormap(list(reversed(viridis.data)), "viridis_r")
}
dashes = (4, 1)

class Graph:
    header = re.compile(r"^synapses (?P<agent>\d+) maxweight=(?P<weightMax>[^ ]+) numsynapses=(?P<synapses>\d+) numneurons=(?P<neurons>\d+) numinputneurons=(?P<inputs>\d+) numoutputneurons=(?P<outputs>\d+)$")
    
    def __init__(self, size):
        self.size = size
        self.types = [None] * size
        self.weights = [None] * size
        for neuron in range(size):
            self.weights[neuron] = [None] * size
    
    def getTypeCount(self, type):
        count = 0
        for _type in self.types:
            if _type == type:
                count += 1
        return count
    
    def getSubgraph(self, neurons):
        size = len(neurons)
        subgraph = Graph(size)
        for index in range(size):
            neuron = neurons[index]
            subgraph.types[index] = self.types[neuron]
        for preIndex in range(size):
            preNeuron = neurons[preIndex]
            for postIndex in range(size):
                postNeuron = neurons[postIndex]
                subgraph.weights[preIndex][postIndex] = self.weights[preNeuron][postNeuron]
        return subgraph
    
    def getNeighborhood(self, neuron, include):
        neurons = []
        if include:
            neurons.append(neuron)
        for _neuron in range(self.size):
            if _neuron == neuron:
                continue
            if self.weights[_neuron][neuron] is not None or self.weights[neuron][_neuron] is not None:
                neurons.append(_neuron)
        return self.getSubgraph(neurons)

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
    return getLifespanData(run, predicate, "BirthStep")

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
    return getLifespanData(run, predicate, "DeathStep")

def getEndTimestep(run):
    with open(os.path.join(run, "endStep.txt")) as f:
        return int(f.readline())

def getFigure(width = 4, height = 3, fontSize = 8):
    matplotlib.rcParams["font.size"] = fontSize
    return matplotlib.pyplot.figure(figsize = (width, height))

def getFit(x, y, degree = 1, count = 100):
    fit = numpy.polyfit(x, y, degree)
    fitFn = numpy.poly1d(fit)
    points = numpy.linspace(min(x), max(x), count)
    return points, fitFn(points)

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

def getGraph(run, agent, stage, type, sizeOnly = False):
    path = os.path.join(run, "brain", "synapses", "synapses_{0}_{1}.txt.gz".format(agent, stage))
    if not os.path.isfile(path):
        return None
    with gzip.open(path) as f:
        match = Graph.header.match(f.readline())
        weightMax = float(match.group("weightMax"))
        neuronCount = int(match.group("neurons"))
        inputCount = int(match.group("inputs"))
        outputCount = int(match.group("outputs"))
        if type == "input":
            neurons = range(inputCount)
        elif type == "output":
            neurons = range(inputCount, inputCount + outputCount)
        elif type == "internal":
            neurons = range(inputCount + outputCount, neuronCount)
        elif type == "processing":
            neurons = range(inputCount, neuronCount)
        elif type == "all":
            neurons = range(neuronCount)
        else:
            raise ValueError("unrecognized type '{0}'".format(type))
        size = len(neurons)
        if sizeOnly:
            return size
        graph = Graph(size)
        for index in range(size):
            neuron = neurons[index]
            if neuron < inputCount:
                graph.types[index] = "input"
            elif neuron < inputCount + outputCount:
                graph.types[index] = "output"
            else:
                graph.types[index] = "internal"
        while True:
            line = f.readline()
            if line == "":
                break
            chunks = line.split()
            preNeuron = int(chunks[0])
            postNeuron = int(chunks[1])
            assert preNeuron != postNeuron, "self-loop in agent {0}".format(agent)
            if preNeuron not in neurons or postNeuron not in neurons:
                continue
            preIndex = neurons.index(preNeuron)
            postIndex = neurons.index(postNeuron)
            weight = float(chunks[2]) / weightMax
            if graph.weights[preIndex][postIndex] is None:
                graph.weights[preIndex][postIndex] = weight
            else:
                graph.weights[preIndex][postIndex] += weight
    return graph

def getGraphSize(run, agent, type):
    return getGraph(run, agent, "birth", type, True)

def getLifespanData(run, predicate, key = lambda row: row):
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

def getLifespans(run, predicate = lambda row: True):
    return getLifespanData(run, predicate, lambda row: row["DeathStep"] - row["BirthStep"])

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
        return float(total) / count

def getMedian(values, predicate = lambda value: True):
    filtered = filter(predicate, values)
    count = len(filtered)
    if count == 0:
        return 0
    else:
        filtered.sort()
        index = count / 2
        if count % 2 == 0:
            return getMean(filtered[index - 1:index + 1])
        else:
            return filtered[index]

def getOffspring(run):
    values = {}
    path = os.path.join(run, "BirthsDeaths.log")
    with open(path) as f:
        for line in f:
            if line.startswith("%"):
                continue
            chunks = line.split()
            if chunks[1] == "BIRTH":
                agent = int(chunks[2])
                parent1 = int(chunks[3])
                parent2 = int(chunks[4])
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
    return matplotlib.ticker.FuncFormatter(lambda tick, position: format(tick / 10 ** power, formatSpec))

def getStatistic(values, statistic, predicate = lambda value: True):
    if statistic == "mean":
        return getMean(values, predicate)
    elif statistic == "median":
        return getMedian(values, predicate)
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

def getWeightMax(run):
    return float(getWorldfileParameter(run, "MaxSynapseWeight"))

def getWorldfileParameter(run, parameterName):
    path = os.path.join(run, "normalized.wf")
    with open(path) as f:
        for line in f:
            chunks = line.strip().split()
            if chunks[0] == parameterName:
                return chunks[1]

def isIterable(obj):
    return hasattr(obj, "__iter__")

def isNotSeedLifespan(row):
    return not isSeedLifespan(row)

def isNotTruncatedLifespan(row):
    return not isTruncatedLifespan(row)

def isReadable(obj):
    return hasattr(obj, "readline")

def isRun(path):
    return os.path.isfile(os.path.join(path, "endStep.txt"))

def isSeedLifespan(row):
    return row["BirthReason"] == "SIMINIT"

def isTruncatedLifespan(row):
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

def smoothData(x, y, window):
    start = window / 2
    end = len(x) - window / 2
    if window % 2 == 0:
        end += 1
    weights = numpy.repeat(1.0, window) / window
    return x[start:end], numpy.convolve(y, weights, "valid")

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
