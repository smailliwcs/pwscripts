from .base import IndividualMetric, Metric, PopulationMetric
from .efficiency import Efficiency
from .modularity import Modularity


def parse_args(args=None):
    import argparse
    import sys
    import textwrap

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
    metric_name = next((arg for arg in args if arg in metrics), None)
    if metric_name is None:
        parser.add_argument("run", metavar="RUN")
        parser.add_argument("metric", metavar="METRIC")
        parser.add_argument("option", metavar="OPTION", nargs="*")
        parser.parse_args(args)
        return None
    metric = metrics[metric_name]
    metric.add_arguments(parser)
    return metric(**vars(parser.parse_args(args)))
