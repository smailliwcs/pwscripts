import statistics

import polyworld as pw
from .base import IndividualMetric, parse_regex_arg


class Gene(IndividualMetric):
    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument("regex", metavar="REGEX", type=parse_regex_arg)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.regex = kwargs["regex"]
        self.indices = None

    def _get_value(self, agent):
        with pw.open(pw.paths.genome(self.run, agent)) as f:
            return statistics.mean(int(line) for index, line in enumerate(f) if index in self.indices)

    def _calculate(self):
        self.indices = set()
        with pw.open(pw.paths.gene_indices(self.run)) as f:
            for index, line in enumerate(f):
                if self.regex.search(line):
                    self.indices.add(index)
        return super()._calculate()
