import argparse
import sys
import textwrap

from ._efficiency import Efficiency
from ._modularity import Modularity

metrics = {metric.__name__: metric for metric in [
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
    # PopulationAggregate
    # Strength
    # SynapseCount
    # Weight
]}


def parse_args(args=None):
    if args is None:
        args = sys.argv[1:]
    wrapper = textwrap.TextWrapper(subsequent_indent="  ")
    epilog = wrapper.fill("metrics: " + ", ".join(sorted(metrics)))
    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    metric_name = next((arg for arg in args if arg in metrics), None)
    if metric_name is None:
        parser.add_argument("run", metavar="RUN")
        parser.add_argument("metric", metavar="METRIC")
        parser.add_argument("option", metavar="OPTION", nargs="*")
        parser.print_help()
        raise SystemExit(1)
    metric = metrics[metric_name]
    metric.add_arguments(parser)
    return metric(**vars(parser.parse_args(args)))
