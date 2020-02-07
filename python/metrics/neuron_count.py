import polyworld as pw
from .base import IndividualMetric


class NeuronCount(IndividualMetric):
    def _get_value(self, agent):
        return pw.Brain.Dimensions.read(self.run, agent).neuron_count
