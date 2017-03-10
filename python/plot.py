import argparse
import math
import matplotlib
import matplotlib.patheffects
import matplotlib.pyplot
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
    matplotlib.rcParams["figure.figsize"] = (4.0, 3.0)
    matplotlib.rcParams["font.family"] = "serif"
    matplotlib.rcParams["font.serif"] = ["Times"]
    matplotlib.rcParams["font.size"] = 8.0
    matplotlib.rcParams["grid.alpha"] = 0.2
    matplotlib.rcParams["grid.linestyle"] = "-"
    matplotlib.rcParams["image.cmap"] = cmapName
    matplotlib.rcParams["legend.fontsize"] = 6.0
    matplotlib.rcParams["legend.framealpha"] = 0.5
    matplotlib.rcParams["savefig.dpi"] = 300
    matplotlib.rcParams["savefig.format"] = "pdf"
    matplotlib.rcParams["text.usetex"] = True
    matplotlib.rcParams["text.latex.preamble"] = [
        r"\usepackage{amsmath}",
        r"\usepackage[T1]{fontenc}",
        r"\usepackage{newtxtext}",
        r"\usepackage{newtxmath}"
    ]

def getValues(metric):
    try:
        return metric.read()
    except IOError:
        values = {}
        count = 0
        sys.stderr.write("Calculating: {0}...".format(metric.getLabel()))
        sys.stderr.flush()
        for key, value in metric.calculate():
            count += 1
            if count % 100 == 0:
                sys.stderr.write(".")
                sys.stderr.flush()
            values[key] = value
        sys.stderr.write("\n")
        metric.write(values)
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

def getBins(data, count = 100):
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
    yValues = getValues(yMetric)
    if isinstance(plot.xMetric, metrics_mod.TimeMetric):
        yValues = yMetric.getSeries(yValues)
    zipped = zipValues(xValues, yValues)
    if plot.histogram:
        xBins = plot.xMetric.getBins()
        if xBins is None:
            xBins = getBins(zipped[0])
        yBins = yMetric.getBins()
        if yBins is None:
            yBins = getBins(zipped[1])
        axes.hist2d(zipped[0], zipped[1], bins = [xBins, yBins], cmin = 1, norm = Hist2dNormalize())
    if plot.type == Plot.Type.LOWESS:
        frac = 1001 * len(zipped[0]) / float(utility.getFinalTimestep(plot.args.run)) ** 2
        data = statsmodels.nonparametric.smoothers_lowess.lowess(zipped[1], zipped[0], frac = frac)
        smoothed = [data[:, 0], data[:, 1]]
    elif plot.type == Plot.Type.REGRESSION:
        m, b, r = scipy.stats.linregress(zipped[0], zipped[1])[:3]
        xRange = [min(zipped[0]), max(zipped[0])]
        yRange = map(lambda x: m * x + b, xRange)
        smoothed = [xRange, yRange]
    else:
        assert False
    color = colors[plotIndex % len(colors)]
    if len(plot.yMetrics) == 1 and isinstance(yMetric, metrics_mod.TimeMetric):
        axes.plot(zipped[0], zipped[1], color = cmap(0.3))
    line = axes.plot(smoothed[0], smoothed[1], color = color)[0]
    line.set_path_effects([matplotlib.patheffects.withStroke(linewidth = 2.0, foreground = "1.0")])
    lines.append(line)
    labels.append(yMetric.getLabel())
    if plot.type == Plot.Type.REGRESSION:
        axes.legend([line], ["$r^2 = {0:.3f}$".format(r ** 2)])
    yMetric.customizeAxis(axes.yaxis)
plot.xMetric.customizeAxis(axes1.xaxis)
axes1.set_xlim(plot.args.xmin, plot.args.xmax)
axes1.set_ylim(plot.args.y1min, plot.args.y1max)
axes2.set_ylim(plot.args.y2min, plot.args.y2max)
axes1.set_xlabel(plot.xMetric.getLabel())
if len(plot.yMetrics) == 1 or plot.args.twinx:
    axes1.set_ylabel(plot.yMetrics[0].getLabel())
if len(plot.yMetrics) == 2 and plot.args.twinx:
    axes2.set_ylabel(plot.yMetrics[1].getLabel())
if len(plot.yMetrics) > 1:
    axes2.legend(lines, labels)
figure.tight_layout()
yMetricsKey = "+".join(map(lambda yMetric: yMetric.getKey(), plot.yMetrics))
figure.savefig("{0}-vs-{1}".format(yMetricsKey, plot.xMetric.getKey()))
