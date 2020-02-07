import enum
import statistics

import polyworld as pw
from .base import IndividualMetric


def get_efficiency(lengths):
    if lengths.vertex_count <= 1:
        return 0.0
    return statistics.mean(1 / distance for (i, j), distance in lengths.get_distances() if j != i)


def get_global_efficiency(lengths):
    return get_efficiency(lengths)


def get_local_efficiency(lengths):
    if lengths.vertex_count == 0:
        return 0.0
    return statistics.mean(get_efficiency(lengths.get_neighborhood(vertex)) for vertex in lengths.vertices())


class Efficiency(IndividualMetric):
    class Scope(enum.Enum):
        LOCAL = "local"
        GLOBAL = "global"

    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument("scope", metavar="SCOPE", choices=tuple(scope.value for scope in Efficiency.Scope))
        parser.add_argument("stage", metavar="STAGE", choices=tuple(stage.value for stage in pw.Stage))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scope = Efficiency.Scope(kwargs["scope"])
        self.stage = pw.Stage(kwargs["stage"])

    def write_arguments(self, file):
        file.write(f"# SCOPE = {self.scope.value}\n")
        file.write(f"# STAGE = {self.stage.value}\n")

    def _get_value(self, agent):
        try:
            brain = pw.Brain.read(self.run, agent, self.stage)
        except FileNotFoundError:
            return None
        lengths = brain.weights.get_lengths()
        if self.scope == Efficiency.Scope.LOCAL:
            return get_local_efficiency(lengths)
        if self.scope == Efficiency.Scope.GLOBAL:
            return get_global_efficiency(lengths)
        raise ValueError
