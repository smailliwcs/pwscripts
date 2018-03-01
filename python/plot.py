import argparse
import itertools
import math
import matplotlib
import matplotlib.gridspec
import matplotlib.patheffects
import matplotlib.pyplot
import metrics as metrics_mod
import numpy
import scipy.stats
import sys
import textwrap
import utility

TSTEP = 200
COLORS = [
    matplotlib.cm.Blues(0.9),
    matplotlib.cm.Oranges(0.45)
]
CMAP_NAME = "YlGnBu"
CMAP = matplotlib.cm.get_cmap(CMAP_NAME)
CMAP.set_bad("1.0")
ALPHA_RUNS = [0.1, 0.2]
ALPHA_HIST = 0.5
BIN_COUNT = 100
OFFSET_HIST = 0.1
STROKE = matplotlib.patheffects.withStroke(linewidth = 3.0, foreground = "1.0")
RASTERIZE = False

class HistNorm(matplotlib.colors.LogNorm):
    def __init__(self, offset = OFFSET_HIST, vmin = None, vmax = None, clip = True):
        super(HistNorm, self).__init__(vmin = vmin, vmax = vmax, clip = clip)
        self.offset = offset

    def __call__(self, value, clip = True):
        result = numpy.ma.masked_less_equal(value, 0, False)
        result = super(HistNorm, self).__call__(result, clip = clip)
        return self.offset + (1.0 - self.offset) * result

class ColorbarLocator(matplotlib.ticker.Locator):
    def __call__(self):
        bounds = self.axis.get_view_interval()
        start = int(math.floor(math.log10(bounds[0])))
        stop = int(math.ceil(math.log10(bounds[1])))
        ticks = [10.0 ** power for power in xrange(start, stop)]
        ticks.append(bounds[1])
        return ticks

class ColorbarFormatter(matplotlib.ticker.Formatter):
    @staticmethod
    def getDistance(tick1, tick2):
        return math.log10(tick2 / tick1)
    
    def __init__(self, formatSpec = "g"):
        self.formatSpec = formatSpec
    
    def __call__(self, tick, index):
        bounds = self.axis.get_view_interval()
        if tick < bounds[1]:
            distanceToMax = ColorbarFormatter.getDistance(tick, bounds[1])
            totalDistance = ColorbarFormatter.getDistance(bounds[0], bounds[1])
            if distanceToMax / totalDistance < 0.1:
                return ""
        return self.format(tick)
    
    def format(self, tick):
        return format(tick, self.formatSpec)

class Plot(object):
    @staticmethod
    def configure():
        matplotlib.rcParams["axes.autolimit_mode"] = "round_numbers"
        matplotlib.rcParams["axes.axisbelow"] = False
        matplotlib.rcParams["axes.grid"] = True
        matplotlib.rcParams["axes.xmargin"] = 0.0
        matplotlib.rcParams["axes.ymargin"] = 0.0
        matplotlib.rcParams["figure.figsize"] = (3.2, 2.8)
        matplotlib.rcParams["font.family"] = "serif"
        matplotlib.rcParams["font.serif"] = ["Times"]
        matplotlib.rcParams["font.size"] = 8.0
        matplotlib.rcParams["grid.alpha"] = 0.1
        matplotlib.rcParams["grid.color"] = "0.0"
        matplotlib.rcParams["image.cmap"] = CMAP_NAME
        matplotlib.rcParams["legend.edgecolor"] = "inherit"
        matplotlib.rcParams["legend.fancybox"] = False
        matplotlib.rcParams["legend.fontsize"] = 6.0
        matplotlib.rcParams["legend.framealpha"] = None
        matplotlib.rcParams["savefig.dpi"] = 300
        matplotlib.rcParams["savefig.format"] = "pdf"
        matplotlib.rcParams["text.usetex"] = True
    
    @staticmethod
    def getMetrics():
        metrics = []
        for arg in sys.argv:
            metric = metrics_mod.metrics.get(arg)
            if metric is not None:
                metrics.append(metric())
        return metrics
    
    @staticmethod
    def parseArgs(metrics):
        wrapper = textwrap.TextWrapper(subsequent_indent = "  ")
        epilog = wrapper.fill("available metrics: {0}".format(", ".join(sorted(metrics_mod.metrics.iterkeys()))))
        parser = argparse.ArgumentParser(add_help = False, epilog = epilog, formatter_class = argparse.RawDescriptionHelpFormatter)
        parser.add_argument("--line", action = "store_true")
        parser.add_argument("--hist", action = "store_true")
        parser.add_argument("--regress", action = "store_true")
        parser.add_argument("--passive", action = "store_true")
        parser.add_argument("--tmin", metavar = "TMIN", type = int)
        parser.add_argument("--tmax", metavar = "TMAX", type = int)
        parser.add_argument("--tstep", metavar = "TSTEP", type = int)
        parser.add_argument("--xmin", metavar = "XMIN", type = float)
        parser.add_argument("--xmax", metavar = "XMAX", type = float)
        parser.add_argument("--ymin", metavar = "YMIN", type = float)
        parser.add_argument("--ymax", metavar = "YMAX", type = float)
        parser.add_argument("--hmax", metavar = "HMAX", type = float)
        parser.add_argument("--htmin", metavar = "HTMIN", type = int, default = 1)
        parser.add_argument("--legend", metavar = "LOC", default = "upper left")
        parser.add_argument("runs", metavar = "RUNS")
        if len(metrics) != 2:
            parser.add_argument("xmetric", metavar = "XMETRIC")
            parser.add_argument("ymetric", metavar = "YMETRIC")
            parser.print_help()
            raise SystemExit
        for metric in metrics:
            parser.add_argument("metrics", metavar = metric.getName(), action = "append")
            metric.addArgs(parser)
        return parser.parse_args()
    
    def __init__(self):
        Plot.configure()
        self.metrics = Plot.getMetrics()
        self.args = Plot.parseArgs(self.metrics)
        self.runs = list(utility.getRuns(self.args.runs))
        assert len(self.runs) > 0
        self.xMetric = self.metrics[0]
        self.yMetric = self.metrics[1]
        if isinstance(self.xMetric, metrics_mod.AgentBasedMetric):
            assert isinstance(self.yMetric, metrics_mod.AgentBasedMetric)
        assert self.args.line or self.args.hist
        if self.args.regress:
            assert not self.args.line and self.args.hist
        if self.args.passive:
            assert self.args.line
            assert isinstance(self.xMetric, metrics_mod.Timestep)
        self.sig = self.args.passive and len(self.runs) > 1
        if self.args.tstep is None:
            if all(map(lambda metric: isinstance(metric, metrics_mod.TimeBasedMetric), self.metrics)):
                self.args.tstep = 0
            else:
                self.args.tstep = TSTEP

class Data:
    @staticmethod
    def get(plot, run, passive, metric):
        metric.initialize(run, passive, plot.args)
        try:
            return metric.read()
        except IOError:
            pass
        count = 0
        values = {}
        spinner = itertools.cycle(["|", "/", "-", "\\"])
        sys.stderr.write("{0}: {1} ... {2}".format(metric.run, metric.getName(), spinner.next()))
        sys.stderr.flush()
        for key, value in metric.calculate():
            count += 1
            if count % 10 == 0:
                sys.stderr.write("\b{0}".format(spinner.next()))
                sys.stderr.flush()
            values[key] = value
        sys.stderr.write("\bDONE\n")
        metric.write(values)
        return values
    
    @staticmethod
    def zip(dx, dy):
        result = [[], []]
        for key, x in sorted(dx.iteritems()):
            if math.isnan(x):
                continue
            for y in utility.iterate(dy.get(key)):
                if math.isnan(y):
                    continue
                result[0].append(x)
                result[1].append(y)
        return result
    
    @staticmethod
    def flatten(axys):
        result = [[], []]
        for axy in axys:
            for index in xrange(len(axy[0])):
                result[0].append(axy[0][index])
                result[1].append(axy[1][index])
        return result
    
    @staticmethod
    def bin(metric, ax, xmin, xmax):
        bins = metric.getBins()
        if bins is not None:
            return bins
        if xmin is None:
            xmin = min(ax)
        if xmax is None:
            xmax = max(ax)
        count = BIN_COUNT
        if metric.integral:
            xrng = float(xmax - xmin)
            if count > xrng:
                return numpy.arange(xmin, xmax + 1)
            else:
                step = int(round(xrng / count))
                count = int(math.ceil(xrng / step))
                fuzz = (count * step - xrng) / 2.0
                return numpy.linspace(xmin - fuzz, xmax + fuzz, count + 1)
        else:
            return numpy.linspace(xmin, xmax, count + 1)
    
    def __init__(self, plot, run, passive):
        self.dx = Data.get(plot, run, passive, plot.xMetric)
        self.dy = Data.get(plot, run, passive, plot.yMetric)
        tival = [plot.args.tmin, plot.args.tmax]
        if plot.args.line:
            self.dx_line = plot.xMetric.toTimeBased(self.dx, tival, plot.args.tstep)
            self.dy_line = plot.yMetric.toTimeBased(self.dy, tival, plot.args.tstep)
            self.axy_line = Data.zip(self.dx_line, self.dy_line)
        if plot.args.hist:
            if plot.args.tmin is None or plot.args.htmin > plot.args.tmin:
                tival[0] = plot.args.htmin
            if all(map(lambda metric: isinstance(metric, metrics_mod.AgentBasedMetric), plot.metrics)):
                self.dx_hist = plot.xMetric.getInterval(self.dx, tival)
                self.dy_hist = plot.yMetric.getInterval(self.dy, tival)
            else:
                self.dx_hist = plot.xMetric.toTimeBased(self.dx, tival)
                self.dy_hist = plot.yMetric.toTimeBased(self.dy, tival)
            self.axy_hist = Data.zip(self.dx_hist, self.dy_hist)

# Pre-configure plot
plot = Plot()
figure = matplotlib.pyplot.figure()
if plot.sig:
    size = figure.get_size_inches()
    size[1] *= 5.0 / 4.0
    figure.set_size_inches(size)
    grid = matplotlib.gridspec.GridSpec(4, 1)
    axes1 = figure.add_subplot(grid[0:-1, :])
    axes2 = figure.add_subplot(grid[-1, :])
else:
    axes1 = figure.gca()

# Iterate runs
driven = {}
passive = {}
for run in plot.runs:
    
    # Calculate data
    driven[run] = Data(plot, run, False)
    if plot.args.passive:
        passive[run] = Data(plot, run, True)
    
    # Plot line
    if plot.args.line:
        axy = driven[run].axy_line
        kwargs = {"rasterized": RASTERIZE, "color": COLORS[0], "alpha": ALPHA_RUNS[0], "zorder": -2}
        axes1.plot(axy[0], axy[1], **kwargs)
        if plot.args.passive:
            axy = passive[run].axy_line
            kwargs.update({"color": COLORS[1], "alpha": ALPHA_RUNS[1], "zorder": -3})
            axes1.plot(axy[0], axy[1], **kwargs)

# Plot line
if plot.args.line:
    axy = numpy.nanmean(map(lambda data: data.axy_line, driven.itervalues()), 0)
    kwargs = {"rasterized": RASTERIZE, "color": COLORS[0], "path_effects": [STROKE]}
    axes1.plot(axy[0], axy[1], label = "Driven", **kwargs)
    if plot.args.passive:
        axy = numpy.nanmean(map(lambda data: data.axy_line, passive.itervalues()), 0)
        kwargs.update({"color": COLORS[1], "zorder": -1})
        axes1.plot(axy[0], axy[1], label = "Passive", **kwargs)

# Plot histogram
if plot.args.hist:
    axy = Data.flatten(map(lambda data: data.axy_hist, driven.itervalues()))
    xbins = Data.bin(plot.xMetric, axy[0], plot.args.xmin, plot.args.xmax)
    ybins = Data.bin(plot.yMetric, axy[1], plot.args.ymin, plot.args.ymax)
    alpha = ALPHA_HIST if plot.args.line else 1.0
    image = axes1.hist2d(axy[0], axy[1], bins = [xbins, ybins], norm = HistNorm(vmax = plot.args.hmax), alpha = alpha, zorder = -4)[3]
    if not plot.sig:
        colorbar = figure.colorbar(image)
        colorbar.locator = ColorbarLocator()
        colorbar.formatter = ColorbarFormatter()
        colorbar.update_ticks()

# Plot regression
if plot.args.regress:
    slope, intercept, correlation = scipy.stats.linregress(axy[0], axy[1])[:3]
    ax = [min(axy[0]), max(axy[0])]
    ay = map(lambda x: slope * x + intercept, ax)
    kwargs = {"rasterized": RASTERIZE, "color": COLORS[0], "path_effects": [STROKE]}
    axes1.plot(ax, ay, label = "$r = {0:.3f}$".format(correlation), **kwargs)

# Plot significance
if plot.sig:
    axy = [[], []]
    ax = driven.itervalues().next().axy_line[0]
    ays_d = numpy.transpose(map(lambda data: data.axy_line[1], driven.itervalues()))
    ays_p = numpy.transpose(map(lambda data: data.axy_line[1], passive.itervalues()))
    for index in xrange(len(ax)):
        timestep = ax[index]
        sig = 1.0 - scipy.stats.ttest_rel(ays_d[index], ays_p[index])[1]
        if math.isnan(sig):
            sig = 0.0
        axy[0].append(timestep)
        axy[1].append(sig)
    axes2.plot(axy[0], axy[1], rasterized = RASTERIZE, color = COLORS[0])

# Post-configure plot
plot.xMetric.formatAxis(axes1.xaxis)
plot.yMetric.formatAxis(axes1.yaxis)
axes1.set_xlim(plot.args.xmin, plot.args.xmax)
axes1.set_ylim(plot.args.ymin, plot.args.ymax)
if plot.sig:
    axes1.tick_params(labelbottom = False)
    axes2.set_xlabel(plot.xMetric.getLabel())
    axes2.set_ylabel("Significance")
    axes2.set_ylim(0.75, 1.05)
    axes2.set_yticks([0.8, 0.95, 1.0])
else:
    axes1.set_xlabel(plot.xMetric.getLabel())
if plot.args.regress or plot.args.passive:
    axes1.legend(loc = plot.args.legend)
axes1.set_ylabel(plot.yMetric.getLabel())
matplotlib.pyplot.tight_layout()
figure.savefig("{0}-vs-{1}".format(plot.yMetric.getKey(), plot.xMetric.getKey()))
