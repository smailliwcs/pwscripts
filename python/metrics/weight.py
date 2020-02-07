import statistics

import polyworld as pw
from .base import IndividualMetric


class Weight(IndividualMetric):
    @classmethod
    def add_arguments(cls, parser):
        super().add_arguments(parser)
        parser.add_argument("--absolute", action="store_true")
        parser.add_argument("stage", metavar="STAGE", choices=tuple(stage.value for stage in pw.Stage))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.absolute = kwargs["absolute"]
        self.stage = pw.Stage(kwargs["stage"])

    def write_arguments(self, file):
        file.write(f"# ABSOLUTE = {self.absolute}\n")
        file.write(f"# STAGE = {self.stage.value}\n")

    def _get_value(self, agent):
        try:
            brain = pw.Brain.read(self.run, agent, self.stage)
        except FileNotFoundError:
            return None
        if brain.synapse_count == 0:
            return 0.0
        weights = brain.weights
        if self.absolute:
            weights = abs(weights)
        return statistics.mean(weights.values())
