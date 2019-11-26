import enum
import os
import re

import polyworld as pw
from graph import WeightGraph


class Brain:
    class Layer(enum.Enum):
        ALL = "all"
        INPUT = "input"
        PROCESSING = "processing"
        OUTPUT = "output"
        INTERNAL = "internal"

    class Dimensions:
        _HEADER_PATTERN = re.compile(
            r"^synapses \d+ "
            r"maxweight=(?P<weight_max>[^ ]+) "
            r"numsynapses=(?P<synapse_count>\d+) "
            r"numneurons=(?P<neuron_count>\d+) "
            r"numinputneurons=(?P<input_neuron_count>\d+) "
            r"numoutputneurons=(?P<output_neuron_count>\d+)$")

        @staticmethod
        def match(header):
            match = Brain.Dimensions._HEADER_PATTERN.match(header)
            return Brain.Dimensions(**match.groupdict())

        @staticmethod
        def read(run, agent, stage=pw.Stage.BIRTH):
            with pw.read_file(Brain._get_path(run, agent, stage)) as f:
                return Brain.Dimensions.match(f.readline())

        def __init__(self, **kwargs):
            self.weight_max = float(kwargs["weight_max"])
            self.synapse_count = int(kwargs["synapse_count"])
            self.neuron_count = int(kwargs["neuron_count"])
            self.input_neuron_count = int(kwargs["input_neuron_count"])
            self.output_neuron_count = int(kwargs["output_neuron_count"])

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

    @staticmethod
    def _get_path(run, agent, stage):
        return os.path.join(run, "brain", "synapses", f"synapses_{agent}_{stage.value}.txt")

    @staticmethod
    def read(run, agent, stage):
        path = Brain._get_path(run, agent, stage)
        if not pw.file_exists(path):
            return None
        with pw.read_file(path) as f:
            dimensions = Brain.Dimensions.match(f.readline())
            brain = Brain(dimensions)
            input_neurons = dimensions.get_neurons(Brain.Layer.INPUT)
            for line in f:
                chunks = line.split()
                pre_neuron = int(chunks[0])
                post_neuron = int(chunks[1])
                assert post_neuron != pre_neuron
                assert post_neuron not in input_neurons
                weight = float(chunks[2]) / dimensions.weight_max
                brain.weights[pre_neuron, post_neuron] += weight
            return brain

    def __init__(self, dimensions):
        self.dimensions = dimensions
        self.weights = WeightGraph(range(self.dimensions.neuron_count))
