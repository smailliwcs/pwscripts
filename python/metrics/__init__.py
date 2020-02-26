import argparse
import sys
import textwrap

from .density import Density
from .efficiency import Efficiency
from .event_count import EventCount
from .food_consumption import FoodConsumption
from .food_energy import FoodEnergy
from .gene import Gene
from .lifespan import Lifespan
from .modularity import Modularity
from .neuron_count import NeuronCount
from .population import Population
from .synapse_count import SynapseCount
from .weight import Weight


def parse_args(args=None):
    metrics = {metric.__name__: metric for metric in (
        Density,
        Efficiency,
        EventCount,
        FoodConsumption,
        FoodEnergy,
        Gene,
        Lifespan,
        Modularity,
        NeuronCount,
        Population,
        SynapseCount,
        Weight
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
