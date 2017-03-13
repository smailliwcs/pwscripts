import argparse
import math
import matplotlib
import matplotlib.gridspec
import matplotlib.patheffects
import matplotlib.pyplot
import matplotlib.ticker
import metrics as metrics_mod
import numpy
import scipy.stats
import statsmodels.nonparametric.smoothers_lowess
import sys
import textwrap
import utility

class Hist2dNormalize(matplotlib.colors.Normalize):
    def __init__(self, vmin = None, vmax = None, clip = False):
        super(Hist2dNormalize, self).__init__(vmin = vmin, vmax = vmax, clip = clip)

    def __call__(self, value, clip = None):
        return 0.3 + 0.7 * super(Hist2dNormalize, self).__call__(value, clip = clip)

class Plot(object):
    class Type(utility.Enum):
        LOWESS = "lowess"
        REGRESSION = "regression"
    
    def __init__(self):
        self.metrics = []
        metricNames = map(lambda metric: metric.__name__, metrics_mod.iterateMetrics())
        metricNames.sort()
        for arg in sys.argv[1:]:
            if arg in metricNames:
                self.metrics.append(getattr(metrics_mod, arg)())
        wrapper = textwrap.TextWrapper(subsequent_indent = "  ")
        epilog = wrapper.fill("available metrics: {0}".format(", ".join(metricNames)))
        parser = argparse.ArgumentParser(add_help = False, epilog = epilog, formatter_class = argparse.RawDescriptionHelpFormatter)
        parser.add_argument("run", metavar = "RUN")
        parser.add_argument("--dvp", action = "store_true")
        parser.add_argument("--twinx", action = "store_true")
        parser.add_argument("--xmin", metavar = "XMIN", type = float)
        parser.add_argument("--xmax", metavar = "XMAX", type = float)
        parser.add_argument("--y1min", metavar = "Y1MIN", type = float)
        parser.add_argument("--y1max", metavar = "Y1MAX", type = float)
        parser.add_argument("--y2min", metavar = "Y2MIN", type = float)
        parser.add_argument("--y2max", metavar = "Y2MAX", type = float)
        if len(self.metrics) < 2:
            parser.add_argument("xmetric", metavar = "XMETRIC")
            parser.add_argument("ymetrics", metavar = "YMETRIC", nargs = "+")
            parser.print_help()
            sys.exit(1)
        for metric in self.metrics:
            parser.add_argument("metrics", metavar = type(metric).__name__, action = "append")
            metric.addArgs(parser)
        self.args = parser.parse_args()
        assert utility.isRun(self.args.run)
        self.xMetric = self.metrics[0]
        self.yMetrics = self.metrics[1:]
        if self.args.dvp:
            assert type(self.xMetric) is metrics_mod.Timestep
            assert len(self.yMetrics) == 1
        if len(self.yMetrics) > 1:
            assert type(self.xMetric) is metrics_mod.Timestep
        if isinstance(self.xMetric, metrics_mod.AgentMetric):
            assert isinstance(self.yMetrics[0], metrics_mod.AgentMetric)
        if self.args.twinx:
            assert len(self.yMetrics) > 1
        if len(self.yMetrics) == 1:
            self.histogram = type(self.xMetric) is not metrics_mod.Timestep or isinstance(self.yMetrics[0], metrics_mod.AgentMetric)
        else:
            self.histogram = False
        if type(self.xMetric) is metrics_mod.Timestep:
            self.type = Plot.Type.LOWESS
        else:
            self.type = Plot.Type.REGRESSION

cmapName = "YlGnBu"
cmap = matplotlib.cm.get_cmap(cmapName)

def configure():
    matplotlib.rcParams["axes.color_cycle"] = [
        cmap(1.0),
        cmap(0.6),
        cmap(0.3)
    ]
    matplotlib.rcParams["axes.grid"] = True
    matplotlib.rcParams["figure.figsize"] = (3.5, 3.0)
    matplotlib.rcParams["font.family"] = "serif"
    matplotlib.rcParams["font.serif"] = ["Times"]
    matplotlib.rcParams["font.size"] = 8.0
    matplotlib.rcParams["grid.alpha"] = 0.2
    matplotlib.rcParams["grid.linestyle"] = "-"
    matplotlib.rcParams["image.cmap"] = cmapName
    matplotlib.rcParams["legend.fontsize"] = 6.0
    matplotlib.rcParams["legend.framealpha"] = 0.5
    matplotlib.rcParams["savefig.format"] = "pdf"
    matplotlib.rcParams["text.usetex"] = True
    matplotlib.rcParams["text.latex.preamble"] = [
        r"\usepackage{amsmath}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage{newtxtext}",
        r"\usepackage{newtxmath}"
    ]

def getValues(metric, passive = False):
    try:
        return metric.read(passive)
    except IOError:
        values = {}
        count = 0
        sys.stderr.write("Calculating: {0}...".format(metric.getLabel()))
        sys.stderr.flush()
        for key, value in metric.calculate(passive):
            count += 1
            if count % 100 == 0:
                sys.stderr.write(".")
                sys.stderr.flush()
            values[key] = value
        sys.stderr.write("\n")
        metric.write(values, passive)
        return values

def iterate(values):
    if hasattr(values, "__iter__"):
        for value in values:
            yield value
    else:
        yield values

def zipValues(xValues, yValues):
    zipped = [[], []]
    for key, xValue in xValues.iteritems():
        if key not in yValues:
            continue
        for yValue in iterate(yValues[key]):
            zipped[0].append(xValue)
            zipped[1].append(yValue)
    return zipped

def getBins(data, count):
    if all(map(lambda datum: isinstance(datum, int), data)):
        dataMin = min(data)
        dataMax = max(data)
        dataRange = dataMax - dataMin
        if count > dataRange:
            return range(dataMin, dataMax + 1)
        else:
            step = int(round(float(dataRange) / count))
            count = int(math.ceil(float(dataRange) / step))
            binRange = count * step
            binFuzz = binRange - dataRange
            binMin = dataMin - 0.5 * binFuzz
            binMax = dataMax + 0.5 * binFuzz
            return numpy.linspace(binMin, binMax, count + 1)
    else:
        return numpy.linspace(min(data), max(data), count + 1)

configure()
plot = Plot()
figure = matplotlib.pyplot.figure()
if plot.args.dvp:
    size = figure.get_size_inches()
    size[1] = math.ceil(8 * float(size[1]) / 3) / 2
    figure.set_size_inches(size)
    grid = matplotlib.gridspec.GridSpec(3, 1)
    axes1 = figure.add_subplot(grid[0:-1, :])
    axes2 = figure.add_subplot(grid[-1, :])
else:
    axes1 = figure.gca()
    if plot.args.twinx:
        axes2 = axes1.twinx()
        axes1.grid(False)
        axes2.grid(False)
    else:
        axes2 = axes1
plot.xMetric.initialize(plot.args.run, plot.args)
xValues = getValues(plot.xMetric)
colors = matplotlib.rcParams["axes.color_cycle"]
lines = []
labels = []
for plotIndex in xrange(len(plot.yMetrics)):
    if plotIndex == 0:
        axes = axes1
    else:
        axes = axes2
    yMetric = plot.yMetrics[plotIndex]
    yMetric.initialize(plot.args.run, plot.args)
    if plot.args.dvp:
        drivenValues = getValues(yMetric, False)
        passiveValues = getValues(yMetric, True)
        yValues = drivenValues
        yBiases = {}
        yStdev = numpy.std(yValues.values())
        for key, drivenValue in drivenValues.iteritems():
            if key not in passiveValues:
                continue
            yBiases[key] = (drivenValue - passiveValues[key]) / yStdev
    else:
        yValues = getValues(yMetric)
    if isinstance(plot.xMetric, metrics_mod.TimeMetric):
        yValues = yMetric.getSeries(yValues)
        if plot.args.dvp:
            yBiases = yMetric.getSeries(yBiases)
    zipped = zipValues(xValues, yValues)
    if plot.args.dvp:
        zippedBiases = zipValues(xValues, yBiases)
    if plot.histogram:
        xBins = plot.xMetric.getBins()
        if xBins is None:
            xBins = getBins(zipped[0], 100)
        yBins = yMetric.getBins()
        if yBins is None:
            yBins = getBins(zipped[1], 100)
        kwargs = {"cmin": 1, "norm": Hist2dNormalize()}
        axes.hist2d(zipped[0], zipped[1], bins = [xBins, yBins], **kwargs)
        if plot.args.dvp:
            yBiasBins = getBins(zippedBiases[1], 33)
            axes2.hist2d(zippedBiases[0], zippedBiases[1], bins = [xBins, yBiasBins], **kwargs)
    if plot.type == Plot.Type.LOWESS:
        frac = 1001 * len(zipped[0]) / float(utility.getFinalTimestep(plot.args.run)) ** 2
        data = statsmodels.nonparametric.smoothers_lowess.lowess(zipped[1], zipped[0], frac = frac)
        smoothed = [data[:, 0], data[:, 1]]
        if plot.args.dvp:
            biasData = statsmodels.nonparametric.smoothers_lowess.lowess(zippedBiases[1], zippedBiases[0], frac = frac)
            smoothedBiases = [biasData[:, 0], biasData[:, 1]]
    elif plot.type == Plot.Type.REGRESSION:
        m, b, r = scipy.stats.linregress(zipped[0], zipped[1])[:3]
        xRange = [min(zipped[0]), max(zipped[0])]
        yRange = map(lambda x: m * x + b, xRange)
        smoothed = [xRange, yRange]
    else:
        assert False
    color = colors[plotIndex % len(colors)]
    if len(plot.yMetrics) == 1 and isinstance(yMetric, metrics_mod.TimeMetric):
        kwargs = {"color": cmap(0.3)}
        axes.plot(zipped[0], zipped[1], **kwargs)
        if plot.args.dvp:
            axes2.plot(zippedBiases[0], zippedBiases[1], **kwargs)
    kwargs = {"color": color}
    line = axes.plot(smoothed[0], smoothed[1], color = color)[0]
    pathEffects = [matplotlib.patheffects.withStroke(linewidth = 2.0, foreground = "1.0")]
    line.set_path_effects(pathEffects)
    lines.append(line)
    if plot.args.dvp:
        biasLine = axes2.plot(smoothedBiases[0], smoothedBiases[1], **kwargs)[0]
        biasLine.set_path_effects(pathEffects)
    labels.append(yMetric.getLabel())
    if plot.type == Plot.Type.REGRESSION:
        axes.legend([line], ["$r^2 = {0:.3f}$".format(r ** 2)])
    yMetric.customizeAxis(axes.yaxis)
plot.xMetric.customizeAxis(axes1.xaxis)
axes1.set_xlim(plot.args.xmin, plot.args.xmax)
axes2.set_xlim(plot.args.xmin, plot.args.xmax)
axes1.set_ylim(plot.args.y1min, plot.args.y1max)
axes2.set_ylim(plot.args.y2min, plot.args.y2max)
if plot.args.dvp:
    axes1.tick_params(labelbottom = False)
    axes2.set_xlabel(plot.xMetric.getLabel())
    axes2.set_ylabel("Selection bias")
    axes2.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins = 4))
else:
    axes1.set_xlabel(plot.xMetric.getLabel())
if len(plot.yMetrics) == 1 or plot.args.twinx:
    axes1.set_ylabel(plot.yMetrics[0].getLabel())
if len(plot.yMetrics) == 2 and plot.args.twinx:
    axes2.set_ylabel(plot.yMetrics[1].getLabel())
if len(plot.yMetrics) > 1:
    axes2.legend(lines, labels)
if plot.args.dvp:
    fileName = "{0}-dvp".format(plot.yMetrics[0].getKey())
else:
    yMetricsKey = "+".join(map(lambda yMetric: yMetric.getKey(), plot.yMetrics))
    fileName = "{0}-vs-{1}".format(yMetricsKey, plot.xMetric.getKey())
matplotlib.pyplot.tight_layout()
figure.savefig(fileName)
