import argparse
import sys
import textwrap

from .efficiency import Efficiency
from .modularity import Modularity


def parse_args(args=None):
    metrics = {metric.__name__: metric for metric in (
        # Degree
        # Density
        Efficiency,
        # EventCount
        # FoodConsumption
        # FoodEnergy
        # Gene
        # LearningRate
        # Lifespan
        Modularity
        # NeuronCount
        # OffspringCount
        # Population
        # Strength
        # SynapseCount
        # Weight
    )}
    if args is None:
        args = sys.argv[1:]
    wrapper = textwrap.TextWrapper(subsequent_indent="  ")
    epilog = wrapper.fill("metrics: " + ", ".join(sorted(metrics)))
    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    metric_name = next(filter(metrics.__contains__, args), None)
    if metric_name is None:
        parser.add_argument("run", metavar="RUN")
        parser.add_argument("metric", metavar="METRIC")
        parser.add_argument("option", metavar="OPTION", nargs="*")
        parser.print_help(sys.stderr)
        raise SystemExit(1)
    metric = metrics[metric_name]
    metric.add_arguments(parser)
    return metric(**vars(parser.parse_args(args)))
