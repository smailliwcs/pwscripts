import gzip
import os
import re
import utility

class Graph(object):
    class Type(utility.Enum):
        INPUT = "input"
        OUTPUT = "output"
        INTERNAL = "internal"
        PROCESSING = "processing"
        ALL = "all"
        
        @staticmethod
        def getNonInput():
            for type in Graph.Type.getAll():
                if type != Graph.Type.INPUT:
                    yield type
    
    header = re.compile(r"^synapses (?P<agent>\d+) maxweight=(?P<weightMax>[^ ]+) numsynapses=\d+ numneurons=(?P<size>\d+) numinputneurons=(?P<inputSize>\d+) numoutputneurons=(?P<outputSize>\d+)$")
    
    @staticmethod
    def read(run, agent, stage, type, passive = False):
        pathBase = os.path.join(run, "passive") if passive else run
        path = os.path.join(pathBase, "brain", "synapses", "synapses_{0}_{1}.txt.gz".format(agent, stage))
        if not os.path.isfile(path):
            return None
        with gzip.open(path) as f:
            match = Graph.header.match(f.readline())
            weightMax = float(match.group("weightMax"))
            size = int(match.group("size"))
            inputSize = int(match.group("inputSize"))
            outputSize = int(match.group("outputSize"))
            if type == Graph.Type.INPUT:
                nodes = range(inputSize)
            elif type == Graph.Type.OUTPUT:
                nodes = range(inputSize, inputSize + outputSize)
            elif type == Graph.Type.INTERNAL:
                nodes = range(inputSize + outputSize, size)
            elif type == Graph.Type.PROCESSING:
                nodes = range(inputSize, size)
            elif type == Graph.Type.ALL:
                nodes = range(size)
            else:
                assert False
            graph = Graph(len(nodes))
            for index in xrange(graph.size):
                node = nodes[index]
                if node < inputSize:
                    graph.types[index] = Graph.Type.INPUT
                elif node < inputSize + outputSize:
                    graph.types[index] = Graph.Type.OUTPUT
                else:
                    graph.types[index] = Graph.Type.INTERNAL
            while True:
                line = f.readline()
                if line == "":
                    break
                chunks = line.split()
                preNode = int(chunks[0])
                postNode = int(chunks[1])
                assert preNode != postNode
                if preNode not in nodes or postNode not in nodes:
                    continue
                preIndex = nodes.index(preNode)
                postIndex = nodes.index(postNode)
                weight = float(chunks[2]) / weightMax
                if graph.weights[preIndex][postIndex] is None:
                    graph.weights[preIndex][postIndex] = weight
                else:
                    graph.weights[preIndex][postIndex] += weight
        return graph
    
    def __init__(self, size):
        self.size = size
        self.types = [None] * size
        self.weights = [None] * size
        for node in xrange(size):
            self.weights[node] = [None] * size
    
    def getTypeCount(self, type):
        count = 0
        for nodeType in self.types:
            if nodeType == type:
                count += 1
            elif type == Graph.Type.PROCESSING and nodeType in (Graph.Type.OUTPUT, Graph.Type.INTERNAL):
                count += 1
        return count
    
    def getLinkCount(self):
        count = 0
        for preNode in xrange(self.size):
            for postNode in xrange(self.size):
                if self.weights[preNode][postNode] is not None:
                    count += 1
        return count
    
    def getSubgraph(self, nodes):
        size = len(nodes)
        graph = Graph(size)
        for index in xrange(size):
            node = nodes[index]
            graph.types[index] = self.types[node]
        for preIndex in xrange(size):
            preNode = nodes[preIndex]
            for postIndex in xrange(size):
                postNode = nodes[postIndex]
                graph.weights[preIndex][postIndex] = self.weights[preNode][postNode]
        return graph
    
    def getNeighborhood(self, node, include):
        nodes = []
        if include:
            nodes.append(node)
        for neighbor in xrange(self.size):
            if neighbor == node:
                continue
            if self.weights[neighbor][node] is not None or self.weights[node][neighbor] is not None:
                nodes.append(neighbor)
        return self.getSubgraph(nodes)
