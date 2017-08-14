import argparse
import collections
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

class Hist2dNormalize(matplotlib.colors.LogNorm):
    def __init__(self, offset = 0.1, vmin = None, vmax = None, clip = False):
        super(Hist2dNormalize, self).__init__(vmin = vmin, vmax = vmax, clip = clip)
        self.offset = offset

    def __call__(self, value, clip = None):
        return self.offset + (1.0 - self.offset) * super(Hist2dNormalize, self).__call__(value, clip = clip)

class Plot(object):
    @staticmethod
    def parseArgs(metrics):
        wrapper = textwrap.TextWrapper(subsequent_indent = "  ")
        epilog = wrapper.fill("available metrics: {0}".format(", ".join(sorted(metrics_mod.metrics.iterkeys()))))
        parser = argparse.ArgumentParser(add_help = False, epilog = epilog, formatter_class = argparse.RawDescriptionHelpFormatter)
        parser.add_argument("runs", metavar = "RUNS")
        group = parser.add_mutually_exclusive_group(required = True)
        group.add_argument("--lowess", action = "store_true")
        group.add_argument("--regress", action = "store_true")
        parser.add_argument("--bias", action = "store_true")
        parser.add_argument("--hist2d", action = "store_true")
        parser.add_argument("--raw", action = "store_true")
        parser.add_argument("--twinx", action = "store_true")
        parser.add_argument("--xmin", metavar = "XMIN", type = float)
        parser.add_argument("--xmax", metavar = "XMAX", type = float)
        parser.add_argument("--y1min", metavar = "Y1MIN", type = float)
        parser.add_argument("--y1max", metavar = "Y1MAX", type = float)
        parser.add_argument("--y2min", metavar = "Y2MIN", type = float)
        parser.add_argument("--y2max", metavar = "Y2MAX", type = float)
        if len(metrics) < 2:
            parser.add_argument("xmetric", metavar = "XMETRIC")
            parser.add_argument("ymetrics", metavar = "YMETRIC", nargs = "+")
            parser.print_help()
            sys.exit(1)
        for metric in metrics:
            parser.add_argument("metrics", metavar = metric.getName(), action = "append")
            metric.addArgs(parser)
        return parser.parse_args()
    
    def __init__(self):
        self.metrics = []
        for arg in sys.argv[1:]:
            if arg in metrics_mod.metrics:
                self.metrics.append(getattr(metrics_mod, arg)())
        self.args = Plot.parseArgs(self.metrics)
        self.runs = list(utility.getRuns(self.args.runs))
        assert len(self.runs) > 0
        self.xMetric = self.metrics[0]
        self.yMetrics = self.metrics[1:]
        if self.args.bias:
            assert isinstance(self.xMetric, metrics_mod.Timestep)
        if self.args.raw:
            assert isinstance(self.xMetric, metrics_mod.Timestep)
            assert all(map(lambda yMetric: isinstance(yMetric, metrics_mod.TimeMetric), self.yMetrics))
        if self.args.twinx:
            assert len(self.yMetrics) > 1

CMAP_NAME = "YlGnBu"
CMAP = matplotlib.cm.get_cmap(CMAP_NAME)
BIN_COUNT_RAW = 100
BIN_COUNT_BIAS = 33
MULTI_RUN_ALPHA = 0.2
HIST2D_ALPHA = 0.8
RAW_ALPHA = 0.2

def configure():
    matplotlib.rcParams["axes.color_cycle"] = [
        CMAP(1.0),
        CMAP(0.5),
        CMAP(0.25)
    ]
    matplotlib.rcParams["axes.grid"] = True
    matplotlib.rcParams["figure.figsize"] = (3.5, 3.0)
    matplotlib.rcParams["font.family"] = "serif"
    matplotlib.rcParams["font.serif"] = ["Times"]
    matplotlib.rcParams["font.size"] = 8.0
    matplotlib.rcParams["grid.alpha"] = 0.2
    matplotlib.rcParams["grid.linestyle"] = "-"
    matplotlib.rcParams["image.cmap"] = CMAP_NAME
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

def getData(metric, passive = False):
    try:
        return metric.read(passive)
    except IOError:
        count = 0
        values = {}
        sys.stderr.write("Calculating {0}...".format(type(metric).__name__))
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

def zipData(xValues, yValues):
    result = [[], []]
    for key, xValue in xValues.iteritems():
        for yValue in utility.iterate(yValues.get(key)):
            result[0].append(xValue)
            result[1].append(yValue)
    return result

def smoothData(zipped, multiRun = False):
    if plot.args.lowess:
        frac = min(1.0, 1000.0 / len(zipped[0]))
        if multiRun:
            frac *= len(plot.runs)
        delta = 0.001 * (max(zipped[0]) - min(zipped[0]))
        result = statsmodels.nonparametric.smoothers_lowess.lowess(zipped[1], zipped[0], frac = frac, delta = delta)
        return [result[:, 0], result[:, 1]], None
    elif plot.args.regress:
        slope, intercept, correlation = scipy.stats.linregress(zipped[0], zipped[1])[:3]
        xRange = [min(zipped[0]), max(zipped[0])]
        yRange = map(lambda x: slope * x + intercept, xRange)
        return [xRange, yRange], correlation
    else:
        assert False

def flattenData(zippeds):
    result = [[], []]
    for zipped in zippeds:
        for index in xrange(len(zipped[0])):
            result[0].append(zipped[0][index])
            result[1].append(zipped[1][index])
    return result

def getBins(values, count, symmetric = False):
    valueMin = min(values)
    valueMax = max(values)
    if symmetric:
        valueAbsMax = max(abs(valueMin), abs(valueMax))
        valueMin = -valueAbsMax
        valueMax = valueAbsMax
    if all(map(lambda value: isinstance(value, int), values)):
        valueRange = valueMax - valueMin
        if count > valueRange:
            return numpy.arange(valueMin, valueMax + 1)
        else:
            step = int(round(float(valueRange) / count))
            count = int(math.ceil(float(valueRange) / step))
            binRange = count * step
            fuzz = binRange - valueRange
            binMin = valueMin - 0.5 * fuzz
            binMax = valueMax + 0.5 * fuzz
            return numpy.linspace(binMin, binMax, count + 1)
    else:
        return numpy.linspace(valueMin, valueMax, count + 1)

# Pre-configure plot
configure()
plot = Plot()
figure = matplotlib.pyplot.figure()
if plot.args.bias:
    size = figure.get_size_inches()
    size[1] *= 4.0 / 3.0
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
plot.xMetric.formatAxis(axes1.xaxis)
colors = matplotlib.rcParams["axes.color_cycle"]
lines = []
labels = []
if len(plot.runs) > 1:
    alpha = MULTI_RUN_ALPHA
else:
    alpha = 1.0

# Iterate y-metrics
for plotIndex in xrange(len(plot.yMetrics)):
    if plotIndex == 0:
        axes = axes1
    else:
        axes = axes2
    xMetric = plot.xMetric
    yMetric = plot.yMetrics[plotIndex]
    yMetric.formatAxis(axes.yaxis)
    sys.stderr.write("Plotting {0}...\n".format(type(yMetric).__name__))
    color = colors[plotIndex % len(colors)]
    zippedsRaw = [None] * len(plot.runs)
    zippedsBias = [None] * len(plot.runs)
    
    # Iterate runs
    for runIndex in xrange(len(plot.runs)):
        run = plot.runs[runIndex]
        if len(plot.runs) > 1:
            sys.stderr.write("{0}\n".format(run))
        
        # Get values
        xMetric.initialize(run, plot.args)
        yMetric.initialize(run, plot.args)
        xValues = getData(xMetric)
        yValues = getData(yMetric)
        
        # Get biases
        if plot.args.bias:
            driven = yValues
            passive = getData(yMetric, True)
            stdev = numpy.std(driven.values())
            yBiases = {key: (value - passive[key]) / stdev for key, value in driven.iteritems() if key in passive}
        
        # Convert to time-based
        if isinstance(xMetric, metrics_mod.TimeMetric):
            yValues = yMetric.toTimeBased(yValues)
            if plot.args.bias:
                yBiases = yMetric.toTimeBased(yBiases)
        
        # Zip data
        zippedRaw = zipData(xValues, yValues)
        zippedsRaw[runIndex] = zippedRaw
        if plot.args.bias:
            zippedBias = zipData(xValues, yBiases)
            zippedsBias[runIndex] = zippedBias
        
        # Plot raw data
        if plot.args.raw:
            kwargs = {"color": color, "alpha": RAW_ALPHA * alpha}
            axes.plot(zippedRaw[0], zippedRaw[1], **kwargs)
            if plot.args.bias:
                axes2.plot(zippedBias[0], zippedBias[1], **kwargs)
        
        # Plot smooth data
        if len(plot.runs) > 1 and plot.args.lowess:
            smoothRaw = smoothData(zippedRaw)[0]
            if plot.args.bias:
                smoothBias = smoothData(zippedBias)[0]
            kwargs = {"color": color, "alpha": alpha}
            lineRaw = axes.plot(smoothRaw[0], smoothRaw[1], **kwargs)[0]
            if plot.args.bias:
                lineBias = axes2.plot(smoothBias[0], smoothBias[1], **kwargs)[0]
    
    # Plot smooth data
    if len(plot.runs) > 1:
        sys.stderr.write("{0}\n".format(plot.args.runs))
    zippedRaw = flattenData(zippedsRaw)
    kwargs = {"color": color}
    smoothRaw, correlation = smoothData(zippedRaw, len(plot.runs) > 1)
    lineRaw = axes.plot(smoothRaw[0], smoothRaw[1], **kwargs)[0]
    lines.append(lineRaw)
    label = yMetric.getLabel()
    if plot.args.regress:
        if len(plot.yMetrics) > 1:
            label = "{0} ($r^2 = {1:.3f}$)".format(label, correlation ** 2)
        else:
            label = "$r^2 = {0:.3f}$".format(correlation ** 2)
    labels.append(label)
    if plot.args.bias:
        zippedBias = flattenData(zippedsBias)
        smoothBias = smoothData(zippedBias, True)[0]
        lineBias = axes2.plot(smoothBias[0], smoothBias[1], **kwargs)[0]
    
    # Plot histogram
    if plot.args.hist2d:
        xBins = xMetric.getBins()
        if xBins is None:
            xBins = getBins(zippedRaw[0], BIN_COUNT_RAW)
        yBinsRaw = yMetric.getBins()
        if yBinsRaw is None:
            yBinsRaw = getBins(zippedRaw[1], BIN_COUNT_RAW)
        kwargs = {"norm": Hist2dNormalize(), "alpha": HIST2D_ALPHA, "zorder": -1}
        axes.hist2d(zippedRaw[0], zippedRaw[1], bins = (xBins, yBinsRaw), **kwargs)
        if plot.args.bias:
            yBinsBias = getBins(zippedBias[1], BIN_COUNT_BIAS, True)
            axes2.hist2d(zippedBias[0], zippedBias[1], bins = (xBins, yBinsBias), **kwargs)

# Post-configure plot
axes1.set_xlim(plot.args.xmin, plot.args.xmax)
axes2.set_xlim(plot.args.xmin, plot.args.xmax)
axes1.set_ylim(plot.args.y1min, plot.args.y1max)
axes2.set_ylim(plot.args.y2min, plot.args.y2max)
if plot.args.bias:
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
if len(plot.yMetrics) > 1 or plot.args.regress:
    axes2.legend(lines, labels)
if plot.args.bias:
    fileName = "{0}-bias".format(plot.yMetrics[0].getKey())
else:
    yMetricsKey = "+".join(map(lambda yMetric: yMetric.getKey(), plot.yMetrics))
    fileName = "{0}-vs-{1}".format(yMetricsKey, plot.xMetric.getKey())
matplotlib.pyplot.tight_layout()
figure.savefig(fileName)
