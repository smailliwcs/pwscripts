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

gray_partial = matplotlib.colors.LinearSegmentedColormap.from_list("gray_partial", ("0", "0.9"))
gray_r_partial = matplotlib.colors.LinearSegmentedColormap.from_list("gray_r_partial", ("0.9", "0"))

synapsesHeader = re.compile(r"^synapses (?P<agent>\d+) numsynapses=(?P<synapses>\d+) numneurons=(?P<neurons>\d+) numinputneurons=(?P<inputs>\d+) numoutputneurons=(?P<outputs>\d+)$")

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

def isIterable(obj):
    return hasattr(obj, "__iter__")

def isReadable(obj):
    return hasattr(obj, "readline")

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

def getGraph(run, agent, stage):
    path = os.path.join(run, "brain", "synapses", "synapses_{0}_{1}.txt.gz".format(agent, stage))
    with gzip.open(path) as f:
        match = synapsesHeader.match(f.readline())
        neurons = int(match.group("neurons"))
        inputs = int(match.group("inputs"))
        outputs = int(match.group("outputs"))
        nodes = neurons - inputs
        graph = []
        for node in range(nodes):
            graph.append([None] * nodes)
        while True:
            line = f.readline()
            if line == "":
                break
            chunks = line.split()
            preNeuron = int(chunks[0]) - inputs
            postNeuron = int(chunks[1]) - inputs
            if preNeuron < 0 or postNeuron < 0:
                continue
            weight = float(chunks[2])
            if graph[preNeuron][postNeuron] is None:
                graph[preNeuron][postNeuron] = weight
            else:
                graph[preNeuron][postNeuron] += weight
    return graph

def getLifeSpans(run, predicate = lambda row: True):
    births = {}
    deaths = {}
    lifeSpans = {}
    path = os.path.join(run, "lifespans.txt")
    for row in getDataRows(path, "LifeSpans"):
        if not predicate(row):
            continue
        agent = row["Agent"]
        birth = row["BirthStep"]
        death = row["DeathStep"]
        births[agent] = birth
        deaths[agent] = death
        lifeSpans[agent] = death - (birth - 1)
    return lifeSpans, births, deaths

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
    divisor = 10.0 ** power
    formatter = lambda tick, position: format(tick / divisor, formatSpec)
    return matplotlib.ticker.FuncFormatter(formatter)

def getStatistic(values, statistic, predicate = lambda value: True):
    if statistic == "mean":
        count = 0
        total = 0.0
        for value in values:
            if predicate(value):
                count += 1
                total += value
        if count == 0:
            return 0.0
        else:
            return total / count
    elif statistic == "sum":
        total = 0.0
        for value in values:
            if predicate(value):
                total += value
        return total
    else:
        raise ValueError("unrecognized statistic '{0}'".format(statistic))

def isRun(path):
    return os.path.isfile(os.path.join(path, "endStep.txt"))

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

def writeAgentData(run, fileName, values):
    path = makeDirectory(run, "plots", "data")
    with open(os.path.join(path, fileName), "w") as f:
        for agent in values:
            f.write("{0} {1}\n".format(agent, values[agent]))

def zipAgentData(x, y):
    zipped = numpy.empty((2, len(x)))
    index = 0
    for agent in x:
        if agent not in y:
            continue
        zipped[0, index] = x[agent]
        zipped[1, index] = y[agent]
        index += 1
    return zipped
