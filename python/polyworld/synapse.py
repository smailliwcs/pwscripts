class Synapse:
    @classmethod
    def parse(cls, line):
        chunks = line.split()
        pre_neuron = int(chunks[0])
        post_neuron = int(chunks[1])
        weight = float(chunks[2])
        learning_rate = float(chunks[3])
        return cls(pre_neuron, post_neuron, weight, learning_rate)

    def __init__(self, pre_neuron, post_neuron, weight, learning_rate):
        self.pre_neuron = pre_neuron
        self.post_neuron = post_neuron
        self.weight = weight
        self.learning_rate = learning_rate
