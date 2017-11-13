import gzip
import os
import re
import utility

class NodeType(utility.Enum):
    INPUT = "input"
    OUTPUT = "output"
    INTERNAL = "internal"
    
    @staticmethod
    def getValue(node, inputCount, outputCount, size):
        if node < inputCount:
            return NodeType.INPUT
        elif node < inputCount + outputCount:
            return NodeType.OUTPUT
        elif node < size:
            return NodeType.INTERNAL
        else:
            raise ValueError

class GraphType(utility.Enum):
    INPUT = "input"
    OUTPUT = "output"
    INTERNAL = "internal"
    PROCESSING = "processing"
    ALL = "all"
    
    @staticmethod
    def getNonInputValues():
        for value in GraphType.getValues():
            if value != GraphType.INPUT:
                yield value
    
    @staticmethod
    def getNodes(value, size, inputCount, outputCount):
        if value == GraphType.INPUT:
            return xrange(inputCount)
        elif value == GraphType.OUTPUT:
            return xrange(inputCount, inputCount + outputCount)
        elif value == GraphType.INTERNAL:
            return xrange(inputCount + outputCount, size)
        elif value == GraphType.PROCESSING:
            return xrange(inputCount, size)
        elif value == GraphType.ALL:
            return xrange(size)
        else:
            raise ValueError

class Graph(object):
    HEADER_PATTERN = re.compile(" ".join((
        r"^synapses",
        r"(?P<agent>\d+)",
        r"maxweight=(?P<maxweight>[^ ]+)",
        r"numsynapses=\d+",
        r"numneurons=(?P<numneurons>\d+)",
        r"numinputneurons=(?P<numinputneurons>\d+)",
        r"numoutputneurons=(?P<numoutputneurons>\d+)$")))
    
    @staticmethod
    def read(run, agent, stage, graphType):
        path = os.path.join(run, "brain", "synapses", "synapses_{0}_{1}.txt.gz".format(agent, stage))
        if not os.path.isfile(path):
            return None
        with gzip.open(path) as f:
            headerMatch = Graph.HEADER_PATTERN.match(f.readline())
            weightMax = float(headerMatch.group("maxweight"))
            size = int(headerMatch.group("numneurons"))
            inputCount = int(headerMatch.group("numinputneurons"))
            outputCount = int(headerMatch.group("numoutputneurons"))
            nodes = list(GraphType.getNodes(graphType, size, inputCount, outputCount))
            graph = Graph(len(nodes))
            for index in xrange(graph.size):
                graph.nodeTypes[index] = NodeType.getValue(nodes[index], inputCount, outputCount, size)
            for line in f:
                chunks = line.split()
                nodeOut = int(chunks[0])
                nodeIn = int(chunks[1])
                assert nodeOut != nodeIn
                if nodeOut not in nodes or nodeIn not in nodes:
                    continue
                indexOut = nodes.index(nodeOut)
                indexIn = nodes.index(nodeIn)
                weight = float(chunks[2]) / weightMax
                graph.weights[indexOut][indexIn] = utility.coalesce(graph.weights[indexOut][indexIn], 0.0) + weight
        return graph
    
    def __init__(self, size):
        self.size = size
        self.nodeTypes = [None] * size
        self.weights = [None] * size
        for node in xrange(size):
            self.weights[node] = [None] * size
    
    def hasLink(self, nodeOut, nodeIn):
        return utility.coalesce(self.weights[nodeOut][nodeIn], 0.0) != 0.0
    
    def getLinkCount(self):
        count = 0
        for nodeOut in xrange(self.size):
            for nodeIn in xrange(self.size):
                if self.hasLink(nodeOut, nodeIn):
                    count += 1
        return count
    
    def getSubgraph(self, nodes):
        size = len(nodes)
        graph = Graph(size)
        for index in xrange(size):
            node = nodes[index]
            graph.nodeTypes[index] = self.nodeTypes[node]
        for indexOut in xrange(size):
            nodeOut = nodes[indexOut]
            for indexIn in xrange(size):
                nodeIn = nodes[indexIn]
                graph.weights[indexOut][indexIn] = self.weights[nodeOut][nodeIn]
        return graph
    
    def getNeighborhood(self, node, include):
        nodes = []
        for neighbor in xrange(self.size):
            if (neighbor == node and include) or self.hasLink(neighbor, node) or self.hasLink(node, neighbor):
                nodes.append(neighbor)
        return self.getSubgraph(nodes)
