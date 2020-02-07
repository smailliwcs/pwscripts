import polyworld as pw
from .base import IndividualMetric


class SynapseCount(IndividualMetric):
    def _get_value(self, agent):
        return pw.Brain.read(self.run, agent).synapse_count
