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

COLORS = [
    "#1764ab",
    "#fc9c9c"
]
ALPHA_RUN = 0.2
ALPHA_HIST = 0.8
BIN_COUNT = 100
OFFSET_HIST = 0.0
STROKE = matplotlib.patheffects.withStroke(linewidth = 2.0, foreground = "1.0")

class HistNorm(matplotlib.colors.LogNorm):
    def __init__(self, offset = OFFSET_HIST, vmin = None, vmax = None, clip = False):
        super(HistNorm, self).__init__(vmin = vmin, vmax = vmax, clip = clip)
        self.offset = offset

    def __call__(self, value, clip = None):
        result = super(HistNorm, self).__call__(value, clip = clip)
        result = numpy.ma.masked_less_equal(result, 0, False)
        return self.offset + (1.0 - self.offset) * result

class Plot(object):
    @staticmethod
    def configure():
        matplotlib.rcParams["axes.grid"] = True
        matplotlib.rcParams["figure.figsize"] = (3.5, 3.0)
        matplotlib.rcParams["font.family"] = "serif"
        matplotlib.rcParams["font.serif"] = ["Times"]
        matplotlib.rcParams["font.size"] = 8.0
        matplotlib.rcParams["grid.alpha"] = 0.2
        matplotlib.rcParams["grid.linestyle"] = "-"
        matplotlib.rcParams["image.cmap"] = "YlGnBu"
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
        parser.add_argument("--passive", action = "store_true")
        parser.add_argument("--tmin", metavar = "TMIN", type = int)
        parser.add_argument("--tmax", metavar = "TMAX", type = int)
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
        if self.args.passive:
            assert isinstance(self.xMetric, metrics_mod.Timestep)
        self.sig = self.args.passive and len(self.runs) > 1

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
            if count % 100 == 0:
                sys.stderr.write("\b{0}".format(spinner.next()))
                sys.stderr.flush()
            values[key] = value
        sys.stderr.write("\bDONE\n")
        metric.write(values)
        return values
    
    @staticmethod
    def zip(dx, dy):
        result = [[], []]
        for key, x in dx.iteritems():
            for y in utility.iterate(dy.get(key)):
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
    def bin(metric, ax):
        bins = metric.getBins()
        if bins is not None:
            return bins
        xmin = min(ax)
        xmax = max(ax)
        count = BIN_COUNT
        if metric.integral:
            xrng = xmax - xmin
            if count > xrng:
                return numpy.arange(xmin, xmax + 1)
            else:
                step = int(round(float(xrng) / count))
                count = int(math.ceil(float(xrng) / step))
                fuzz = 0.5 * (count * step - xrng)
                return numpy.linspace(xmin - fuzz, xmax + fuzz, count + 1)
        else:
            return numpy.linspace(xmin, xmax, count + 1)
    
    def __init__(self, plot, run, passive):
        self.dx = Data.get(plot, run, passive, plot.xMetric)
        self.dy = Data.get(plot, run, passive, plot.yMetric)
        trange = {"tmin": plot.args.tmin, "tmax": plot.args.tmax}
        if plot.args.line:
            self.dx_line = plot.xMetric.toTimeBased(self.dx, True, **trange)
            self.dy_line = plot.yMetric.toTimeBased(self.dy, True, **trange)
            self.axy_line = Data.zip(self.dx_line, self.dy_line)
        if plot.args.hist:
            if isinstance(plot.xMetric, metrics_mod.AgentBasedMetric) and isinstance(plot.yMetric, metrics_mod.AgentBasedMetric):
                self.dx_hist = plot.xMetric.getRange(self.dx, **trange)
                self.dy_hist = plot.yMetric.getRange(self.dy, **trange)
            else:
                self.dx_hist = plot.xMetric.toTimeBased(self.dx, False, **trange)
                self.dy_hist = plot.yMetric.toTimeBased(self.dy, False, **trange)
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
        kwargs = {"color": COLORS[0], "alpha": ALPHA_RUN, "zorder": -2}
        axes1.plot(axy[0], axy[1], **kwargs)
        if plot.args.passive:
            axy = passive[run].axy_line
            kwargs.update({"color": COLORS[1], "zorder": -3})
            axes1.plot(axy[0], axy[1], **kwargs)

# Plot line
lines = []
if plot.args.line:
    axy = numpy.nanmean(map(lambda data: data.axy_line, driven.itervalues()), 0)
    kwargs = {"color": COLORS[0], "path_effects": [STROKE]}
    lines.append(axes1.plot(axy[0], axy[1], **kwargs)[0])
    if plot.args.passive:
        axy = numpy.nanmean(map(lambda data: data.axy_line, passive.itervalues()), 0)
        kwargs.update({"color": COLORS[1], "zorder": -1})
        lines.append(axes1.plot(axy[0], axy[1], **kwargs)[0])

# Plot histogram
if plot.args.hist:
    axy = Data.flatten(map(lambda data: data.axy_hist, driven.itervalues()))
    bins = [Data.bin(plot.xMetric, axy[0]), Data.bin(plot.yMetric, axy[1])]
    alpha = ALPHA_HIST if plot.args.line else 1.0
    axes1.hist2d(axy[0], axy[1], bins = bins, norm = HistNorm(), alpha = alpha, zorder = -4)

# Plot significance
if plot.sig:
    axy = [[], []]
    ax = driven.itervalues().next().axy_line[0]
    ays_d = numpy.transpose(map(lambda data: data.axy_line[1], driven.itervalues()))
    ays_p = numpy.transpose(map(lambda data: data.axy_line[1], passive.itervalues()))
    for index in xrange(len(ax)):
        axy[0].append(ax[index])
        axy[1].append(1.0 - scipy.stats.ttest_rel(ays_d[index], ays_p[index])[1])
    axes2.plot(axy[0], axy[1], color = COLORS[0])

# Post-configure plot
plot.xMetric.formatAxis(axes1.xaxis)
plot.yMetric.formatAxis(axes1.yaxis)
if plot.sig:
    axes1.tick_params(labelbottom = False)
    axes2.set_xlabel(plot.xMetric.getLabel())
    axes2.set_ylabel("Significance")
    axes2.set_ylim(0.75, 1.05)
    axes2.set_yticks([0.8, 0.95, 1.0])
else:
    axes1.set_xlabel(plot.xMetric.getLabel())
if plot.args.passive:
    axes1.legend(lines, ["Driven", "Passive"])
axes1.set_ylabel(plot.yMetric.getLabel())
matplotlib.pyplot.tight_layout()
figure.savefig("{0}-vs-{1}".format(plot.yMetric.getKey(), plot.xMetric.getKey()))
