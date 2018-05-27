import argparse
import itertools
import math
import matplotlib
import matplotlib.cm
import matplotlib.colors
import matplotlib.figure
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

ALPHA_RUN = (0.1, 0.2)
BIN_COUNT = 100
CMAP_NAME = "YlGnBu"
matplotlib.rc("image", cmap = CMAP_NAME)
CMAP = matplotlib.cm.get_cmap(CMAP_NAME)
CMAP.set_bad("1.0")
COLOR = (
    matplotlib.cm.Blues(0.9),
    matplotlib.cm.Oranges(0.45)
)
OFFSET_HIST = 0.1
SIZE = 3.25
SIZE_FACTOR = 0.8
STROKE = matplotlib.patheffects.withStroke(linewidth = 3.0, foreground = "1.0")
TSTEP = (10, 100)

class BareTexManager(matplotlib.texmanager.TexManager):
    def __init__(self):
        super(BareTexManager, self).__init__()
        self._font_preamble = ""

matplotlib.texmanager.TexManager = BareTexManager

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
        parser.add_argument("--xstep", metavar = "XSTEP", type = float)
        parser.add_argument("--xlabel", metavar = "XLABEL")
        parser.add_argument("--ymin", metavar = "YMIN", type = float)
        parser.add_argument("--ymax", metavar = "YMAX", type = float)
        parser.add_argument("--ystep", metavar = "YSTEP", type = float)
        parser.add_argument("--ylabel", metavar = "YLABEL")
        parser.add_argument("--htmin", metavar = "HTMIN", type = int, default = 0)
        parser.add_argument("--hmax", metavar = "HMAX", type = float)
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--logx", action = "store_true")
        group.add_argument("--logy", action = "store_true")
        group.add_argument("--logxy", action = "store_true")
        parser.add_argument("--diag", action = "store_true")
        parser.add_argument("--bins", metavar = "BINS", type = int, default = BIN_COUNT)
        parser.add_argument("--size", metavar = "SIZE", type = float, default = SIZE)
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
            if plot.args.tmin is None or plot.args.htmin > plot.args.tmin:
                interval[0] = plot.args.htmin
            if all(map(lambda metric: isinstance(metric, metrics_mod.AgentBasedMetric), plot.metrics)):
                dx_hist = plot.xMetric.constrain(dx, interval)
                dy_hist = plot.yMetric.constrain(dy, interval)
            else:
                dx_hist = plot.xMetric.toTimeBased(dx, interval)
                dy_hist = plot.yMetric.toTimeBased(dy, interval)
            self.hist = Data.zip(dx_hist, dy_hist)

def plotLine(axes, axy, kwargs):
    axes.plot(axy[0], axy[1], **kwargs)

def getGridKwargs():
    props = ("alpha", "color", "linestyle", "linewidth")
    return dict(map(lambda prop: (prop, matplotlib.rcParams["grid.{0}".format(prop)]), props))

def nudge(text, x, y):
    text.set_transform(text.get_transform() + matplotlib.transforms.Affine2D().translate(x, y))

if __name__ == "__main__":
    
    # Pre-configure plot
    plot = Plot()
    figure = matplotlib.pyplot.figure()
    if plot.sig:
        figure.set_size_inches(plot.args.size, plot.args.size)
        grid = matplotlib.gridspec.GridSpec(4, 1)
        axes1 = figure.add_subplot(grid[0:-1, :])
        axes2 = figure.add_subplot(grid[-1, :])
    else:
        figure.set_size_inches(plot.args.size, SIZE_FACTOR * plot.args.size)
        axes1 = figure.gca()
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
                "alpha": ALPHA_RUN[index],
                "color": COLOR[index],
                "zorder": -2 - index
            }
            plotLine(axes1, driven[run].line, kwargs(0))
            if plot.args.passive:
                plotLine(axes1, passive[run].line, kwargs(1))
    
    # Plot line
    if plot.args.line:
        kwargs = lambda index: {
            "color": COLOR[index],
            "label": ("Driven", "Passive")[index],
            "path_effects": [STROKE],
            "zorder": -index
        }
        axy = numpy.mean(map(lambda data: data.line, driven.itervalues()), axis = 0)
        plotLine(axes1, axy, kwargs(0))
        if plot.args.passive:
            axy = numpy.mean(map(lambda data: data.line, passive.itervalues()), axis = 0)
            plotLine(axes1, axy, kwargs(1))
    
    # Plot histogram
    if plot.args.hist:
        axy = Data.flatten(map(lambda data: data.hist, driven.itervalues()))
        xbins = Data.bin(plot.xMetric, axy[0], plot.args.xmin, plot.args.xmax, plot.args.bins)
        ybins = Data.bin(plot.yMetric, axy[1], plot.args.ymin, plot.args.ymax, plot.args.bins)
        image = axes1.hist2d(axy[0], axy[1], bins = (xbins, ybins), norm = HistNorm(vmax = plot.args.hmax), zorder = -4)[3]
        if not plot.sig:
            colorbar = figure.colorbar(image)
            colorbar.locator = ColorbarLocator()
            colorbar.formatter = ColorbarFormatter()
            colorbar.update_ticks()
    
    # Plot regression
    if plot.args.regress:
        m, b, r = scipy.stats.linregress(axy)[:3]
        ax = (min(axy[0]), max(axy[0]))
        ay = map(lambda x: m * x + b, ax)
        kwargs = {
            "color": COLOR[0],
            "label": "$r = {0:.3f}$".format(r),
            "path_effects": (STROKE,),
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
            p = scipy.stats.ttest_rel(ay["driven"][index], ay["passive"][index])[1]
            if math.isnan(p):
                p = 1.0
            axy[0].append(timestep)
            axy[1].append(1.0 - p)
        axes2.plot(axy[0], axy[1], color = COLOR[0])
    
    # Post-configure plot
    axes1.set_xlim(plot.args.xmin, plot.args.xmax)
    if plot.args.xstep is not None:
        axes1.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(plot.args.xstep))
    axes1.set_ylim(plot.args.ymin, plot.args.ymax)
    if plot.args.ystep is not None:
        axes1.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(plot.args.ystep))
    xlabel = plot.xMetric.getLabel() if plot.args.xlabel is None else plot.args.xlabel
    ylabel = plot.yMetric.getLabel() if plot.args.ylabel is None else plot.args.ylabel
    if plot.sig:
        axes1.tick_params(labelbottom = False)
        axes2.set_xlabel(xlabel)
        axes2.set_xlim(plot.args.xmin, plot.args.xmax)
        if plot.args.xstep is not None:
            axes2.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(plot.args.xstep))
        axes2.set_ylabel("Significance")
        axes2.set_ylim(0.75, 1.05)
        ticks = axes2.set_yticks((0.8, 0.95, 1.0))
        if plot.args.size < 4.0:
            nudge(ticks[1].label, 0.0, -1.0)
            nudge(ticks[2].label, 0.0, 1.0)
    else:
        axes1.set_xlabel(xlabel)
    if plot.args.regress or plot.args.passive:
        axes1.legend(loc = plot.args.legend)
    axes1.set_ylabel(ylabel)
    if plot.args.diag:
        axes1.plot([0.0, 1.0], [0.0, 1.0], transform = axes1.transAxes, **getGridKwargs())
    figure.savefig("{0}-vs-{1}".format(plot.yMetric.getKey(), plot.xMetric.getKey()))
