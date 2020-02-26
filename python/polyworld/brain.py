import enum
import re

from graph import WeightGraph
from . import paths
from . import utility
from .stage import Stage
from .synapse import Synapse


class Brain:
    class Layer(enum.Enum):
        ALL = "all"
        INPUT = "input"
        PROCESSING = "processing"
        OUTPUT = "output"
        INTERNAL = "internal"

    class Dimensions:
        REGEX = re.compile(
            r"^synapses (?P<agent>\d+) "
            r"maxweight=(?P<weight_max>[^ ]+) "
            r"numsynapses=(?P<synapse_count>\d+) "
            r"numneurons=(?P<neuron_count>\d+) "
            r"numinputneurons=(?P<input_neuron_count>\d+) "
            r"numoutputneurons=(?P<output_neuron_count>\d+)$")

        @classmethod
        def parse(cls, header, agent):
            match = cls.REGEX.match(header)
            assert int(match.group("agent")) == agent
            neuron_count = int(match.group("neuron_count"))
            input_neuron_count = int(match.group("input_neuron_count"))
            output_neuron_count = int(match.group("output_neuron_count"))
            weight_max = float(match.group("weight_max"))
            return cls(neuron_count, input_neuron_count, output_neuron_count, weight_max)

        @classmethod
        def read(cls, run, agent, stage=Stage.BIRTH):
            with utility.open(paths.synapses(run, agent, stage)) as f:
                return cls.parse(f.readline(), agent)

        def __init__(self, neuron_count, input_neuron_count, output_neuron_count, weight_max):
            self.neuron_count = neuron_count
            self.input_neuron_count = input_neuron_count
            self.output_neuron_count = output_neuron_count
            self.weight_max = weight_max

        def get_neurons(self, layer):
            if layer == Brain.Layer.ALL:
                return range(self.neuron_count)
            if layer == Brain.Layer.INPUT:
                return range(self.input_neuron_count)
            if layer == Brain.Layer.PROCESSING:
                return range(self.input_neuron_count, self.neuron_count)
            if layer == Brain.Layer.OUTPUT:
                return range(self.input_neuron_count, self.input_neuron_count + self.output_neuron_count)
            if layer == Brain.Layer.INTERNAL:
                return range(self.input_neuron_count + self.output_neuron_count, self.neuron_count)
            raise ValueError

    @classmethod
    def read(cls, run, agent, stage=Stage.BIRTH):
        with utility.open(paths.synapses(run, agent, stage)) as f:
            dimensions = cls.Dimensions.parse(f.readline(), agent)
            input_neurons = dimensions.get_neurons(Brain.Layer.INPUT)
            brain = cls(dimensions)
            for line in f:
                synapse = Synapse.parse(line)
                assert synapse.post_neuron != synapse.pre_neuron
                assert synapse.post_neuron not in input_neurons
                brain.weights[synapse.pre_neuron, synapse.post_neuron] += synapse.weight / dimensions.weight_max
            return brain

    def __init__(self, dimensions):
        self.dimensions = dimensions
        self.weights = WeightGraph(range(dimensions.neuron_count))

    @property
    def neuron_count(self):
        return self.dimensions.neuron_count

    @property
    def synapse_count(self):
        return self.weights.edge_count

    @property
    def synapse_count_max(self):
        return self.dimensions.neuron_count * (self.dimensions.neuron_count - self.dimensions.input_neuron_count - 1)
