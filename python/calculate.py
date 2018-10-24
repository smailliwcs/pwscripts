import argparse
import metrics as metrics_mod
import sys
import textwrap
import utility

def getMetric():
    for arg in sys.argv:
        metric = metrics_mod.metrics.get(arg)
        if metric is not None:
            return metric()
    return None

def parseArgs(metric):
    wrapper = textwrap.TextWrapper(subsequent_indent = "  ")
    epilog = wrapper.fill("available metrics: {0}".format(", ".join(sorted(metrics_mod.metrics.iterkeys()))))
    parser = argparse.ArgumentParser(add_help = False, epilog = epilog, formatter_class = argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--start", metavar = "START", type = int)
    parser.add_argument("run", metavar = "RUN")
    if metric is None:
        parser.add_argument("metric", metavar = "METRIC")
        parser.print_help()
        raise SystemExit
    parser.add_argument("metric", metavar = metric.getName())
    metric.addArgs(parser)
    return parser.parse_args()

metric = getMetric()
args = parseArgs(metric)
assert utility.isRun(args.run)
metric.initialize(args.run, args = args, start = args.start)
try:
    items = metric.calculate()
except NotImplementedError:
    items = metric.read().iteritems()
for key, value in items:
    sys.stdout.write("{0} {1}\n".format(key, value))
    sys.stdout.flush()
