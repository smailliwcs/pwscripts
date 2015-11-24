import datalib
import math
import matplotlib
import matplotlib.backends.backend_pdf
import matplotlib.pyplot
import numpy
import os
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
        bounds = self.axis.get_view_interval()
        if tick < bounds[1] and math.log10(bounds[1] / tick) / math.log10(bounds[1] / bounds[0]) < 0.1:
            return ""
        else:
            return self.format(tick)
    
    def format(self, tick):
        return format(tick, self.formatSpec)

def binData(x, y, width, statistic = "mean"):
    xMax = max(x)
    bins = numpy.arange(0, xMax, width)
    bins = numpy.append(bins, xMax + 1)
    centers = (bins + width / 2.0)[:-1]
    binned = scipy.stats.binned_statistic(x, numpy.asarray(y), statistic, bins)[0]
    return centers, binned

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

def getGeneTitles(run, start = 0, stop = float("inf")):
    titles = {}
    path = os.path.join(run, "genome", "meta", "geneindex.txt")
    for line, index in readLines(path, start, stop):
        titles[index] = line.split()[1]
    path = os.path.join(run, "genome", "meta", "genetitle.txt")
    for line, index in readLines(path, start, stop):
        titles[index] = line.split(" :: ")[0]
    return titles

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

def getPdf(*args):
    return matplotlib.backends.backend_pdf.PdfPages(*args)

def getRunPaths(path):
    if isRunPath(path):
        yield path
    else:
        for directory in os.listdir(path):
            subpath = os.path.join(path, directory)
            if isRunPath(subpath):
                yield subpath

def getScaleFormatter(power, formatSpec = "g"):
    divisor = 10.0 ** power
    formatter = lambda tick, position: format(tick / divisor, formatSpec)
    return matplotlib.ticker.FuncFormatter(formatter)

def isRunPath(path):
    return os.path.isfile(os.path.join(path, "endStep.txt"))

def printProperties(artist):
    return matplotlib.artist.getp(artist)

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

def zipData(x, y):
    zipped = numpy.empty((2, len(x)))
    index = 0
    for key in x:
        zipped[0, index] = x[key]
        zipped[1, index] = y[key]
        index += 1
    return zipped
