from . import Diversity
from .base import PopulationMetric, parse_range_arg


class Selection(PopulationMetric):
    has_run_arg = False

    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument("actual", metavar="ACTUAL")
        parser.add_argument("neutral", metavar="NEUTRAL")
        parser.add_argument("genes", metavar="GENES", type=parse_range_arg)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.actual = Diversity(data=kwargs["actual"], genes=kwargs["genes"])
        self.neutral = Diversity(data=kwargs["neutral"], genes=kwargs["genes"])

    def _calculate(self):
        return (self.actual.get_data() / self.neutral.get_data() - 1).mean(axis=1)
