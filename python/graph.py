import gzip
import os
import re
import utility

class NodeType(utility.Enum):
    INPUT = "input"
    OUTPUT = "output"
    INTERNAL = "internal"

class Graph(object):
    class Type(utility.Enum):
        INPUT = "input"
        OUTPUT = "output"
        INTERNAL = "internal"
        PROCESSING = "processing"
        ALL = "all"
        
        @staticmethod
        def getNonInputValues():
            for type in Graph.Type.getValues():
                if type != Graph.Type.INPUT:
                    yield type
    
    headerPattern = re.compile(
        r"^synapses " +
        r"(?P<agent>\d+) " +
        r"maxweight=(?P<maxweight>[^ ]+) " +
        r"numsynapses=\d+ " +
        r"numneurons=(?P<numneurons>\d+) " +
        r"numinputneurons=(?P<numinputneurons>\d+) " +
        r"numoutputneurons=(?P<numoutputneurons>\d+)$")
    
    @staticmethod
    def read(run, agent, stage, type, passive = False):
        if passive:
            pathBase = os.path.join(run, "passive")
        else:
            pathBase = run
        path = os.path.join(pathBase, "brain", "synapses", "synapses_{0}_{1}.txt.gz".format(agent, stage))
        if not os.path.isfile(path):
            return None
        with gzip.open(path) as f:
            headerMatch = Graph.headerPattern.match(f.readline())
            weightMax = float(headerMatch.group("maxweight"))
            size = int(headerMatch.group("numneurons"))
            inputCount = int(headerMatch.group("numinputneurons"))
            outputCount = int(headerMatch.group("numoutputneurons"))
            if type == Graph.Type.INPUT:
                nodes = range(inputCount)
            elif type == Graph.Type.OUTPUT:
                nodes = range(inputCount, inputCount + outputCount)
            elif type == Graph.Type.INTERNAL:
                nodes = range(inputCount + outputCount, size)
            elif type == Graph.Type.PROCESSING:
                nodes = range(inputCount, size)
            elif type == Graph.Type.ALL:
                nodes = range(size)
            else:
                assert False
            graph = Graph(len(nodes))
            for index in xrange(graph.size):
                node = nodes[index]
                if node < inputCount:
                    nodeType = NodeType.INPUT
                elif node < inputCount + outputCount:
                    nodeType = NodeType.OUTPUT
                else:
                    nodeType = NodeType.INTERNAL
                graph.nodeTypes[index] = nodeType
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
                if graph.weights[indexOut][indexIn] is None:
                    graph.weights[indexOut][indexIn] = weight
                else:
                    graph.weights[indexOut][indexIn] += weight
        return graph
    
    def __init__(self, size):
        self.size = size
        self.nodeTypes = [None] * size
        self.weights = [None] * size
        for node in xrange(size):
            self.weights[node] = [None] * size
    
    def getLinkCount(self):
        count = 0
        for nodeOut in xrange(self.size):
            for nodeIn in xrange(self.size):
                if self.weights[nodeOut][nodeIn] is not None:
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
            isNeighbor = False
            if neighbor == node:
                if include:
                    isNeighbor = True
            elif self.weights[neighbor][node] is not None or self.weights[node][neighbor] is not None:
                isNeighbor = True
            if isNeighbor:
                nodes.append(neighbor)
        return self.getSubgraph(nodes)
