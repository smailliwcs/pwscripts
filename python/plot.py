import argparse
import itertools
import math
import matplotlib
import matplotlib.cm
import matplotlib.colors
import matplotlib.gridspec
import matplotlib.patheffects
import matplotlib.pyplot
import matplotlib.texmanager
import matplotlib.ticker
import matplotlib.transforms
import metrics as metrics_mod
import numpy
import scipy.stats
import sys
import textwrap
import utility

ALPHA = (0.15, 0.3)
CMAP = matplotlib.cm.get_cmap(matplotlib.rcParams["image.cmap"])
CMAP.set_bad("w")
FIGSIZE = matplotlib.rcParams["figure.figsize"]
FIGSIZE_RATIO = 0.8
FONT_SIZE = matplotlib.rcParams["font.size"]
LINEWIDTH = matplotlib.rcParams["lines.linewidth"]
PAD = {
    "pad": 0.5,
    "h_pad": 0.0,
    "w_pad": 0.0
}
STROKE = matplotlib.patheffects.withStroke(linewidth = LINEWIDTH * 2.0, foreground = "w")
TSTEP = (10, 100)

class BareTexManager(matplotlib.texmanager.TexManager):
    def __init__(self):
        super(BareTexManager, self).__init__()
        self._font_preamble = ""

matplotlib.texmanager.TexManager = BareTexManager

class HistNorm(matplotlib.colors.LogNorm):
    def __init__(self, vmin = None, vmax = None, base_vmax = None):
        super(HistNorm, self).__init__(vmin = vmin, vmax = vmax)
        self.base = matplotlib.colors.LogNorm(vmin = 1, vmax = base_vmax)

    def __call__(self, value, **kwargs):
        super(HistNorm, self).__call__(value)
        result = numpy.ma.masked_less_equal(value, 0, False)
        return self.base.__call__(result)

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
        parser.add_argument("--wilcoxon", action = "store_true")
        parser.add_argument("--tmin", metavar = "TMIN", type = int)
        parser.add_argument("--tmax", metavar = "TMAX", type = int)
        parser.add_argument("--tstep", metavar = "TSTEP", type = int)
        parser.add_argument("--xmin", metavar = "XMIN", type = float)
        parser.add_argument("--xmax", metavar = "XMAX", type = float)
        parser.add_argument("--xstep", metavar = "XSTEP", type = float)
        parser.add_argument("--xtick", metavar = "XTICK", type = int, nargs = "+")
        parser.add_argument("--xscale", metavar = "XSCALE", type = int)
        parser.add_argument("--xlabel", metavar = "XLABEL")
        parser.add_argument("--ymin", metavar = "YMIN", type = float)
        parser.add_argument("--ymax", metavar = "YMAX", type = float)
        parser.add_argument("--ystep", metavar = "YSTEP", type = float)
        parser.add_argument("--ytick", metavar = "YTICK", type = int, nargs = "+")
        parser.add_argument("--yscale", metavar = "YSCALE", type = int)
        parser.add_argument("--ylabel", metavar = "YLABEL")
        parser.add_argument("--hvmax", metavar = "HVMAX", type = int)
        parser.add_argument("--hthreshold", metavar = "HTHRESHOLD", type = int, default = 10)
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--logx", action = "store_true")
        group.add_argument("--logy", action = "store_true")
        group.add_argument("--logxy", action = "store_true")
        parser.add_argument("--bins", metavar = "BINS", type = int, default = 100)
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
        self.metrics = Plot.getMetrics()
        self.args = Plot.parseArgs(self.metrics)
        self.runs = list(utility.getRuns(self.args.runs))
        assert len(self.runs) > 0
        self.xMetric = self.metrics[0]
        self.yMetric = self.metrics[1]
        assert self.args.line or self.args.hist
        if self.args.regress:
            assert not self.args.line and self.args.hist
        if self.args.passive:
            assert self.args.line
            assert isinstance(self.xMetric, metrics_mod.Timestep)
        self.sig = self.args.passive and len(self.runs) > 1
        if self.args.tstep is None:
            if all(map(lambda metric: isinstance(metric, metrics_mod.TimeBasedMetric), self.metrics)):
                self.args.tstep = TSTEP[0]
            else:
                self.args.tstep = TSTEP[1]
        if self.args.xscale is None:
            self.args.xscale = 3 if isinstance(self.xMetric, metrics_mod.Timestep) else 0
        if self.args.yscale is None:
            self.args.yscale = 3 if isinstance(self.yMetric, metrics_mod.Timestep) else 0

class Data:
    @staticmethod
    def get(metric, run, passive, args):
        metric.initialize(run, passive, args)
        try:
            return metric.read()
        except IOError:
            pass
        count = 0
        values = {}
        spinner = itertools.cycle(("|", "/", "-", "\\"))
        sys.stderr.write("{0} ... {1}".format(metric.getName(), spinner.next()))
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
    def bin(metric, ax, xmin, xmax, count):
        bins = metric.getBins()
        if bins is not None:
            return bins
        if xmin is None:
            xmin = min(ax)
        if xmax is None:
            xmax = max(ax)
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
        sys.stderr.write("{0}\n".format(utility.getRun(run, passive)))
        dx = Data.get(plot.xMetric, run, passive, plot.args)
        dy = Data.get(plot.yMetric, run, passive, plot.args)
        interval = [plot.args.tmin, plot.args.tmax]
        if plot.args.line:
            dx_line = plot.xMetric.toSeries(dx, interval, plot.args.tstep)
            dy_line = plot.yMetric.toSeries(dy, interval, plot.args.tstep)
            self.line = Data.zip(dx_line, dy_line)
        if plot.args.hist and not passive:
            if all(map(lambda metric: isinstance(metric, metrics_mod.AgentBasedMetric), plot.metrics)):
                dx_hist = plot.xMetric.constrain(dx, interval)
                dy_hist = plot.yMetric.constrain(dy, interval)
            else:
                dx_hist = plot.xMetric.toTimeBased(dx, interval)
                dy_hist = plot.yMetric.toTimeBased(dy, interval)
            self.hist = Data.zip(dx_hist, dy_hist)

def getAxes(subplots):
    figure = matplotlib.pyplot.figure()
    size = list(FIGSIZE)
    if not subplots:
        size[1] = size[0] * FIGSIZE_RATIO
    figure.set_size_inches(*size)
    result = [figure]
    if subplots:
        grid = matplotlib.gridspec.GridSpec(4, 1)
        result.append(figure.add_subplot(grid[0:-1, :]))
        result.append(figure.add_subplot(grid[-1, :]))
    else:
        result.append(figure.gca())
    return result

def getBbox(axes):
    return axes.get_window_extent().transformed(axes.figure.dpi_scale_trans.inverted())

def plotLine(axes, axy, kwargs):
    axes.plot(axy[0], axy[1], **kwargs)

def setLimits(axis, min, max):
    limits = axis.get_data_interval()
    if min is not None:
        limits[0] = min
    if max is not None:
        limits[1] = max
    axis.set_data_interval(limits[0], limits[1], ignore = True)

def scaleAxis(axis, scale):
    if scale == 0:
        return
    axis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda tick, position: tick / 10.0 ** scale))
    axis.labelpad -= FONT_SIZE * 0.25

def scaleLabel(label, scale):
    if scale == 0:
        return label
    return "{0} / ($10^{{{1}}}$)".format(label, scale)

if __name__ == "__main__":
    
    # Pre-configure plot
    plot = Plot()
    if plot.sig:
        figure, axes1, axes2 = getAxes(True)
    else:
        figure, axes1 = getAxes(False)
    if plot.args.logx:
        axes1.semilogx()
    elif plot.args.logy:
        axes1.semilogy()
    elif plot.args.logxy:
        axes1.loglog()
    
    # Iterate runs
    driven = {}
    passive = {}
    for run in plot.runs:
        
        # Calculate data
        driven[run] = Data(plot, run, False)
        if plot.args.passive:
            passive[run] = Data(plot, run, True)
        
        # Plot line
        if plot.args.line and not plot.args.hist:
            kwargs = lambda index: {
                "alpha": ALPHA[index],
                "color": "C{}".format(index),
                "linewidth": LINEWIDTH * 0.5,
                "zorder": -2 - index
            }
            plotLine(axes1, driven[run].line, kwargs(0))
            if plot.args.passive:
                plotLine(axes1, passive[run].line, kwargs(1))
    
    # Plot line
    if plot.args.line:
        kwargs = lambda index: {
            "color": "C{}".format(index),
            "label": ("Driven", "Passive")[index],
            "path_effects": [STROKE],
            "zorder": -index
        }
        axy = plot.yMetric.aggregate(map(lambda data: data.line, driven.itervalues()), axis = 0)
        plotLine(axes1, axy, kwargs(0))
        if plot.args.passive:
            axy = plot.yMetric.aggregate(map(lambda data: data.line, passive.itervalues()), axis = 0)
            plotLine(axes1, axy, kwargs(1))
    
    # Plot histogram
    if plot.args.hist:
        axy = Data.flatten(map(lambda data: data.hist, driven.itervalues()))
        xbins = Data.bin(plot.xMetric, axy[0], plot.args.xmin, plot.args.xmax, plot.args.bins)
        ybins = Data.bin(plot.yMetric, axy[1], plot.args.ymin, plot.args.ymax, plot.args.bins)
        norm = HistNorm(base_vmax = plot.args.hvmax)
        hist, _, _, image = axes1.hist2d(axy[0], axy[1], bins = (xbins, ybins), norm = norm, zorder = -4)
        indices = numpy.where(hist >= plot.args.hthreshold)
        sys.stderr.write("x: [{0}, {1}]\n".format(xbins[min(indices[0])], xbins[max(indices[0]) + 1]))
        sys.stderr.write("y: [{0}, {1}]\n".format(ybins[min(indices[1])], ybins[max(indices[1]) + 1]))
        if not plot.sig:
            colorbar = figure.colorbar(image, fraction = 0.125, pad = 0.0)
            colorbar.set_label("Agent count", verticalalignment = "bottom", rotation = 270.0)
            colorbar.locator = ColorbarLocator()
            colorbar.formatter = ColorbarFormatter()
            colorbar.update_ticks()
    
    # Plot regression
    if plot.args.regress:
        m, b, r = scipy.stats.linregress(axy)[:3]
        ax = [min(axy[0]), max(axy[0])]
        if plot.args.xmin is not None:
            ax[0] = plot.args.xmin
        if plot.args.xmax is not None:
            ax[1] = plot.args.xmax
        ay = map(lambda x: m * x + b, ax)
        kwargs = {
            "color": "C0",
            "label": "$r = {0:.3f}$".format(r),
            "path_effects": [STROKE],
        }
        axes1.plot(ax, ay, **kwargs)
    
    # Plot significance
    if plot.sig:
        ax = driven.itervalues().next().line[0]
        ay = {
            "driven": numpy.transpose(map(lambda data: data.line[1], driven.itervalues())),
            "passive": numpy.transpose(map(lambda data: data.line[1], passive.itervalues()))
        }
        axy = [[], []]
        for index in xrange(len(ax)):
            timestep = ax[index]
            aytd = ay["driven"][index]
            aytp = ay["passive"][index]
            if plot.args.wilcoxon:
                p = scipy.stats.wilcoxon(aytd, aytp, zero_method = "pratt")[1]
            else:
                p = scipy.stats.ttest_rel(aytd, aytp)[1]
            if math.isnan(p):
                p = 1.0
            axy[0].append(timestep)
            axy[1].append(1.0 - p)
        axes2.plot(axy[0], axy[1], color = "C0")
    
    # Post-configure plot
    setLimits(axes1.xaxis, plot.args.xmin, plot.args.xmax)
    setLimits(axes1.yaxis, plot.args.ymin, plot.args.ymax)
    axes1.autoscale()
    if plot.args.xstep is not None:
        axes1.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(plot.args.xstep))
    if plot.args.xtick is not None:
        axes1.set_xticks(numpy.append(axes1.get_xticks(), plot.args.xtick))
    if plot.args.ystep is not None:
        axes1.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(plot.args.ystep))
    if plot.args.ytick is not None:
        axes1.set_yticks(numpy.append(axes1.get_yticks(), plot.args.ytick))
    xlabel = utility.coalesce(plot.args.xlabel, plot.xMetric.getLabel())
    ylabel = utility.coalesce(plot.args.ylabel, plot.yMetric.getLabel())
    scaleAxis(axes1.xaxis, plot.args.xscale)
    xlabel = scaleLabel(xlabel, plot.args.xscale)
    scaleAxis(axes1.yaxis, plot.args.yscale)
    ylabel = scaleLabel(ylabel, plot.args.yscale)
    if plot.sig:
        axes1.tick_params(axis = "x", bottom = False, labelbottom = False)
        setLimits(axes2.xaxis, plot.args.xmin, plot.args.xmax)
        axes2.autoscale()
        axes2.set_xlabel(xlabel)
        if plot.args.xstep is not None:
            axes2.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(plot.args.xstep))
        if plot.args.xtick is not None:
            axes2.set_xticks(numpy.append(axes2.get_xticks(), plot.args.xtick))
        scaleAxis(axes2.xaxis, plot.args.xscale)
        axes2.set_ylabel("Significance")
        ymargin = 0.02
        axes2.set_ylim(0.8 - ymargin, 1.0 + ymargin)
        ticks = axes2.set_yticks((0.8, 0.95, 1.0))
    else:
        axes1.set_xlabel(xlabel)
    if plot.args.regress or plot.args.passive:
        axes1.legend(loc = plot.args.legend)
    axes1.set_ylabel(ylabel)
    figure.set_tight_layout(PAD)
    figure.savefig("{0}-vs-{1}".format(plot.yMetric.getKey(), plot.xMetric.getKey()))
