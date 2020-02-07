import polyworld as pw
from .base import IndividualMetric


class Density(IndividualMetric):
    def _get_value(self, agent):
        brain = pw.Brain.read(self.run, agent)
        return brain.synapse_count / brain.synapse_count_max
