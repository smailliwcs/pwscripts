import algorithms
import collections
import graph as graph_mod
import gzip
import math
import matplotlib
import numpy
import os
import utility

class Stage(utility.Enum):
    INCEPT = "incept"
    BIRTH = "birth"
    DEATH = "death"

class Metric(object):
    integral = False
    
    @classmethod
    def getBins(cls):
        pass
    
    @classmethod
    def customizeAxis(cls, axis):
        pass
    
    def getFullArgName(self, argName):
        return "{0}_{1}{2}".format(argName, type(self).__name__, hash(self))
    
    def addArg(self, parser, argName, **kwargs):
        parser.add_argument(self.getFullArgName(argName), **kwargs)
    
    def addArgs(self, parser):
        pass
    
    def readArg(self, args, argName):
        return getattr(args, self.getFullArgName(argName))
    
    def readArgs(self, args):
        pass
    
    def initialize(self, run, args = None):
        self.run = run
        if args is not None:
            self.readArgs(args)
    
    def getKey(self):
        raise NotImplementedError
    
    def getLabel(self):
        raise NotImplementedError
    
    def getFileName(self, extension):
        return self.getKey() + extension
    
    def getDataFileName(self):
        return self.getFileName(".txt")
    
    def getDataPath(self, passive = False):
        pathBase = os.path.join(self.run, "passive") if passive else self.run
        return os.path.join(pathBase, "data", self.getDataFileName())
    
    def readLines(self, passive = False):
        with open(self.getDataPath(passive)) as f:
            for line in f:
                if line.startswith("#"):
                    continue
                yield line
    
    def read(self, passive = False):
        values = {}
        for line in self.readLines(passive):
            key, value = line.split()
            key = int(key)
            if self.integral:
                value = int(value)
            else:
                value = float(value)
            values[key] = value
        return values
    
    def write(self, values, passive = False):
        path = self.getDataPath(passive)
        utility.makeDirectories(os.path.dirname(path))
        with open(path, "w") as f:
            for x, y in values.iteritems():
                f.write("{0} {1}\n".format(x, y))
    
    def calculate(self, passive = False):
        raise NotImplementedError
    
    def getPoints(self, values):
        raise NotImplementedError

class AgentMetric(Metric):
    def getSeries(self, values):
        timestepMetric = MeanTimestep()
        timestepMetric.initialize(self.run)
        series = collections.defaultdict(list)
        for agent, timestep in timestepMetric.read().iteritems():
            if agent in values:
                series[timestep].append(values[agent])
        return series

class StagedAgentMetric(AgentMetric):
    def addArgs(self, parser):
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getAll()))
    
    def readArgs(self, args):
        self.stage = self.readArg(args, "stage")

class TimeMetric(Metric):
    def getSeries(self, values):
        return values

class AgentEnergy(AgentMetric):
    class Type(utility.Enum):
        IN = "in"
        OUT = "out"
        TOTAL = "total"
    
    def __init__(self):
        super(AgentEnergy, self).__init__()
        self.lifespanMetric = Lifespan()
    
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE", choices = tuple(AgentEnergy.Type.getAll()))
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
    
    def initialize(self, run, args = None):
        super(AgentEnergy, self).initialize(run, args)
        self.lifespanMetric.initialize(run)
    
    def getKey(self):
        return "agent-energy-{0}".format(self.type)
    
    def getLabel(self):
        if self.type == AgentEnergy.Type.TOTAL:
            return "Agent energy"
        else:
            return "Energy {0}".format(self.type)
    
    def calculate(self, passive = False):
        assert not passive
        lifespans = self.lifespanMetric.read()
        for agent in utility.iterateAgents(self.run):
            lifespan = lifespans[agent]
            if lifespans == 0:
                yield agent, 0.0
            else:
                path = os.path.join(self.run, "energy", self.type, "agent_{0}.txt".format(agent))
                tableName = "AgentEnergy{0}".format(self.type.capitalize())
                valueSum = 0.0
                for row in utility.getDataTable(path, tableName).rows():
                    valueSum += row["Energy"]
                yield agent, valueSum / lifespan

class Complexity(AgentMetric):
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE")
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
        self.polyworld = False
        self.jidt = False
        if self.type.find("pw") >= 0:
            self.polyworld = True
        elif self.type.find("jidt") >= 0:
            self.jidt = True
        else:
            assert False
    
    def getKey(self):
        return "complexity-{0}".format(self.type)
    
    def getLabel(self):
        return "Complexity ({0})".format(self.type)
    
    def read(self, passive = False):
        values = {}
        for line in self.readLines(passive):
            if self.polyworld:
                agent, value = line.split()
                value = float(value)
                if value != 0.0:
                    values[int(agent)] = value * math.log(2)
            elif self.jidt:
                agent, flag, value = line.split()
                if flag == "C":
                    values[int(agent)] = float(value)
            else:
                assert False
        return values

class Consistency(TimeMetric):
    def addArgs(self, parser):
        self.addArg(parser, "group-size", metavar = "GROUP_SIZE", type = int, choices = range(8))
    
    def readArgs(self, args):
        self.groupSize = self.readArg(args, "group-size")
    
    def getKey(self):
        return "consistency-{0}".format(self.groupSize)
    
    def getLabel(self):
        if self.groupSize == 0:
            return "Consistency"
        else:
            return "Consistency ({0}-bit groups)".format(self.groupSize)

class Density(AgentMetric):
    def addArgs(self, parser):
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.Graph.Type.getNonInput()))
    
    def readArgs(self, args):
        self.graphType = self.readArg(args, "graph-type")
    
    def getKey(self):
        return "density-{0}".format(self.graphType)
    
    def getLabel(self):
        if self.graphType == graph_mod.Graph.Type.ALL:
            return "Density"
        else:
            return "{0} density".format(self.graphType.capitalize())
    
    def calculate(self, passive = False):
        for agent in utility.iterateAgents(self.run):
            graph = graph_mod.Graph.read(self.run, agent, Stage.INCEPT, self.graphType, passive)
            if self.graphType == graph_mod.Graph.Type.ALL:
                countMax = graph.size * (graph.size - graph.getTypeCount(graph_mod.Graph.Type.INPUT) - 1)
            else:
                countMax = graph.size * (graph.size - 1)
            if countMax != 0:
                yield agent, float(graph.getLinkCount()) / countMax

class Efficiency(AgentMetric):
    class Type(utility.Enum):
        LOCAL = "local"
        GLOBAL = "global"
    
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE", choices = tuple(Efficiency.Type.getAll()))
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getAll()))
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.Graph.Type.getAll()))
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
        self.stage = self.readArg(args, "stage")
        self.graphType = self.readArg(args, "graph-type")
    
    def getKey(self):
        return "efficiency-{0}-{1}-{2}".format(self.type, self.stage, self.graphType)
    
    def getLabel(self):
        if self.graphType == graph_mod.Graph.Type.ALL:
            return "{0} efficiency".format(self.type.capitalize())
        else:
            return "{0} {1} efficiency".format(self.graphType.capitalize(), self.type)
    
    def calculate(self, passive = False):
        for agent in utility.iterateAgents(self.run):
            graph = graph_mod.Graph.read(self.run, agent, self.stage, self.graphType, passive)
            if graph is None or graph.size == 0:
                continue
            if self.type == Efficiency.Type.LOCAL:
                valueSum = 0.0
                for node in xrange(graph.size):
                    neighborhood = graph.getNeighborhood(node, False)
                    distances = algorithms.Distance.calculate(neighborhood.weights)
                    valueSum += algorithms.Efficiency.calculate(distances)
                    value = valueSum / graph.size
            elif self.type == Efficiency.Type.GLOBAL:
                distances = algorithms.Distance.calculate(graph.weights)
                value = algorithms.Efficiency.calculate(distances)
            else:
                assert False
            yield agent, value

class Entropy(StagedAgentMetric):
    def getKey(self):
        return "entropy-{0}".format(self.stage)
    
    def getLabel(self):
        return "Entropy"

class FoodDistance(TimeMetric):
    def getKey(self):
        return "food-distance"
    
    def getLabel(self):
        return "Food distance"
    
    def read(self, passive = False):
        assert not passive
        distanceMax = math.sqrt(2) * float(utility.getWorldfileParameter(self.run, "WorldSize"))
        values = {}
        path = os.path.join(self.run, "food", "distance.txt")
        for row in utility.getDataTable(path, "FoodDistance").rows():
            values[row["Timestep"]] = row["Distance"] / distanceMax
        return values
    
class FoodEnergy(TimeMetric):
    def getKey(self):
        return "food-energy"
    
    def getLabel(self):
        return "Food energy"
    
    def read(self, passive = False):
        assert not passive
        values = {}
        path = os.path.join(self.run, "food", "energy.txt")
        for row in utility.getDataTable(path, "FoodEnergy").rows():
            values[row["Timestep"]] = row["Energy"]
        return values

class Gene(AgentMetric):
    integral = True
    
    @classmethod
    def getBins(cls):
        return numpy.linspace(0, 256, 65)
    
    @classmethod
    def customizeAxis(cls, axis):
        axis.set_major_locator(matplotlib.ticker.MultipleLocator(64))
    
    def addArgs(self, parser):
        self.addArg(parser, "index", metavar = "INDEX", type = int)
    
    def readArgs(self, args):
        self.index = self.readArg(args, "index")
    
    def getKey(self):
        return "gene-{0}".format(self.index)
    
    def getLabel(self):
        path = os.path.join(self.run, "genome", "meta", "genetitle.txt")
        with open(path) as f:
            found = True
            for index in xrange(self.index):
                if f.readline() == "":
                    found = False
                    break
            if found:
                label = f.readline().split(" :: ")[0]
        path = os.path.join(self.run, "genome", "meta", "geneindex.txt")
        with open(path) as f:
            for index in xrange(self.index):
                f.readline()
            label = f.readline().split()[1]
        return label.replace("_", "\\_")
    
    def calculate(self, passive = False):
        for agent in utility.iterateAgents(self.run):
            pathBase = os.path.join(self.run, "passive") if passive else self.run
            path = os.path.join(pathBase, "genome", "agents", "genome_{0}.txt.gz".format(agent))
            with gzip.open(path) as f:
                for index in xrange(self.index):
                    f.readline()
                yield agent, int(f.readline())

class InfoModification(StagedAgentMetric):
    def getKey(self):
        return "info-modification-{0}".format(self.stage)
    
    def getLabel(self):
        return "Information modification"

class InfoTransfer(StagedAgentMetric):
    def getKey(self):
        return "info-transfer-{0}".format(self.stage)
    
    def getLabel(self):
        return "Information transfer"

class InfoStorage(StagedAgentMetric):
    def getKey(self):
        return "info-storage-{0}".format(self.stage)
    
    def getLabel(self):
        return "Information storage"

class Integration(AgentMetric):
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE")
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
        assert self.type.find("jidt") >= 0
    
    def getKey(self):
        return "integration-{0}".format(self.type)
    
    def getDataFileName(self):
        return "complexity-{0}.txt".format(self.type)
    
    def getLabel():
        return "Integration ({0})".format(self.type)
    
    def read(self, passive = False):
        values = {}
        for line in self.readLines(passive):
            agent, flag, value = line.split()
            if flag == "I":
                values[int(agent)] = float(value)
        return values

class LearningRate(AgentMetric):
    def getKey(self):
        return "learning-rate"
    
    def getLabel(self):
        return "Learning rate"
    
    def calculate(self, passive = False):
        for agent in utility.iterateAgents(self.run):
            pathBase = os.path.join(self.run, "passive") if passive else self.run
            path = os.path.join(pathBase, "brain", "synapses", "synapses_{0}_{1}.txt.gz".format(agent, Stage.INCEPT))
            with gzip.open(path) as f:
                f.readline()
                valueSum = 0.0
                count = 0
                for line in f:
                    valueSum += abs(float(line.split()[3]))
                    count += 1
            if count != 0:
                yield agent, valueSum / count

class LifespanMetric(AgentMetric):
    integral = True
    
    def __init__(self):
        super(LifespanMetric, self).__init__()
        self.initial = True
        self.truncated = True
    
    def getValue(self, row):
        raise NotImplementedError
    
    def read(self, passive = False):
        assert not passive
        values = {}
        path = os.path.join(self.run, "lifespans.txt")
        for row in utility.getDataTable(path, "LifeSpans").rows():
            if not self.initial and row["BirthReason"] == "SIMINIT":
                continue
            elif not self.truncated and row["DeathReason"] == "SIMEND":
                continue
            values[row["Agent"]] = self.getValue(row)
        return values

class BirthTimestep(LifespanMetric):
    def getKey(self):
        return "birth"
    
    def getLabel(self):
        return "Birth timestep"
    
    def getValue(self, row):
        return row["BirthStep"]

class DeathTimestep(LifespanMetric):
    def getKey(self):
        return "death"
    
    def getLabel(self):
        return "Death timestep"
    
    def getValue(self, row):
        return row["DeathStep"]

class Lifespan(LifespanMetric):
    def addArgs(self, parser):
        self.addArg(parser, "truncated", metavar = "TRUNCATED", type = int, choices = range(2))
    
    def readArgs(self, args):
        self.truncated = bool(self.readArg(args, "truncated"))
    
    def getKey(self):
        if self.truncated:
            return "lifespan-truncated"
        else:
            return "lifespan"
    
    def getLabel(self):
        if self.truncated:
            return "Lifespan (truncated)"
        else:
            return "Lifespan"
    
    def getValue(self, row):
        return row["DeathStep"] - row["BirthStep"]

class MeanTimestep(LifespanMetric):
    def getKey(self):
        return "agent-time"
    
    def getLabel(self):
        return "Mean timestep"
    
    def getValue(self, row):
        return (row["BirthStep"] + row["DeathStep"]) / 2

class Modularity(AgentMetric):
    def addArgs(self, parser):
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getAll()))
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.Graph.Type.getAll()))
    
    def readArgs(self, args):
        self.stage = self.readArg(args, "stage")
        self.graphType = self.readArg(args, "graph-type")
    
    def getKey(self):
        return "modularity-{0}-{1}".format(self.stage, self.graphType)
    
    def getLabel(self):
        if self.graphType == graph_mod.Graph.Type.ALL:
            return "Modularity"
        else:
            return "{0} modularity".format(self.graphType.capitalize())
    
    def calculate(self, passive = False):
        for agent in utility.iterateAgents(self.run):
            graph = graph_mod.Graph.read(self.run, agent, self.stage, self.graphType, passive)
            if graph is None or graph.size == 0:
                continue
            yield agent, algorithms.Modularity.calculate(graph.weights)

class NeuronCount(AgentMetric):
    integral = True
    
    def addArgs(self, parser):
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.Graph.Type.getAll()))
    
    def readArgs(self, args):
        self.graphType = self.readArg(args, "graph-type")
    
    def getKey(self):
        return "neuron-count-{0}".format(self.graphType)
    
    def getLabel(self):
        if self.graphType == graph_mod.Graph.Type.ALL:
            return "Neuron count"
        else:
            return "{0} neuron count".format(self.graphType.capitalize())
    
    def calculate(self, passive = False):
        for agent in utility.iterateAgents(self.run):
            graph = graph_mod.Graph.read(self.run, agent, Stage.INCEPT, self.graphType, passive)
            if graph is None:
                continue
            yield agent, graph.size

class OffspringRate(AgentMetric):
    def __init__(self):
        super(OffspringRate, self).__init__()
        self.lifespanMetric = Lifespan()
    
    def initialize(self, run, args = None):
        super(OffspringRate, self).initialize(run, args)
        self.lifespanMetric.initialize(run)
    
    def getKey(self):
        return "offspring-rate"
    
    def getLabel(self):
        return "Offspring rate"
    
    def calculate(self, passive = False):
        assert not passive
        counts = collections.defaultdict(int)
        for timestep, events in utility.iterateEvents(self.run):
            for event in events:
                if event.type != utility.Event.Type.BIRTH:
                    continue
                counts[event.parent1] += 1
                counts[event.parent2] += 1
        for agent, lifespan in self.lifespanMetric.read().iteritems():
            if lifespan == 0:
                continue
            yield agent, float(counts[agent]) / lifespan

class PhaseSpaceExpansion(StagedAgentMetric):
    def getKey(self):
        return "expansion-{0}".format(self.stage)
    
    def getLabel(self):
        return "Phase space expansion"

class Population(TimeMetric):
    integral = True
    
    def getKey(self):
        return "population"
    
    def getLabel(self):
        return "Population"
    
    def read(self, passive = False):
        assert not passive
        values = {}
        values[0] = utility.getInitialAgentCount(self.run)
        path = os.path.join(self.run, "population.txt")
        for row in utility.getDataTable(path, "Population").rows():
            values[row["T"]] = row["Population"]
        return values

class SmallWorldness(AgentMetric):
    def __init__(self):
        super(SmallWorldness, self).__init__()
        self.localEfficiencyMetric = Efficiency()
        self.localEfficiencyMetric.type = Efficiency.Type.LOCAL
        self.globalEfficiencyMetric = Efficiency()
        self.globalEfficiencyMetric.type = Efficiency.Type.GLOBAL
    
    def addArgs(self, parser):
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getAll()))
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.Graph.Type.getAll()))
    
    def readArgs(self, args):
        self.stage = self.readArg(args, "stage")
        self.graphType = self.readArg(args, "graph-type")
    
    def initialize(self, run, args):
        super(SmallWorldness, self).initialize(run, args)
        self.localEfficiencyMetric.initialize(run)
        self.localEfficiencyMetric.stage = self.stage
        self.localEfficiencyMetric.graphType = self.graphType
        self.globalEfficiencyMetric.initialize(run)
        self.globalEfficiencyMetric.stage = self.stage
        self.globalEfficiencyMetric.graphType = self.graphType
    
    def getKey(self):
        return "small-worldness-{0}-{1}".format(self.stage, self.graphType)
    
    def getLabel(self):
        if self.graphType == graph_mod.Graph.Type.ALL:
            return "Small-worldness"
        else:
            return "{0} small-worldness".format(self.graphType.capitalize())
    
    def read(self, passive = False):
        localEfficiencies = self.localEfficiencyMetric.read(passive)
        globalEfficiencies = self.globalEfficiencyMetric.read(passive)
        values = {}
        for agent in utility.iterateAgents(self.run):
            if agent in localEfficiencies and agent in globalEfficiencies:
                values[agent] = localEfficiencies[agent] * globalEfficiencies[agent]
        return values

class Timestep(TimeMetric):
    integral = True
    
    def getKey(self):
        return "time"
    
    def getLabel(self):
        return "Timestep"
    
    def read(self, passive = False):
        values = {}
        values[0] = 0
        for timestep in utility.iterateTimesteps(self.run):
            values[timestep] = timestep
        return values

class WeightMetric(AgentMetric):
    class Type(utility.Enum):
        EXCITATORY = "excitatory"
        INHIBITORY = "inhibitory"
        ABSOLUTE = "absolute"
    
    def addArgs(self, parser):
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getAll()))
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.Graph.Type.getNonInput()))
        self.addArg(parser, "weight-type", metavar = "WEIGHT_TYPE", choices = tuple(WeightMetric.Type.getAll()))
    
    def readArgs(self, args):
        self.stage = self.readArg(args, "stage")
        self.graphType = self.readArg(args, "graph-type")
        self.weightType = self.readArg(args, "weight-type")
    
    def getWeight(self, graph, preNode, postNode):
        weight = graph.weights[preNode][postNode]
        if weight is None:
            return None
        if self.weightType == WeightMetric.Type.EXCITATORY:
            if weight > 0.0:
                return weight
        elif self.weightType == WeightMetric.Type.INHIBITORY:
            if weight < 0.0:
                return -weight
        elif self.weightType == WeightMetric.Type.ABSOLUTE:
            if weight != 0.0:
                return abs(weight)
        else:
            assert False
        return None
    
    def iterateGraphs(self, passive = False):
        for agent in utility.iterateAgents(self.run):
            graph = graph_mod.Graph.read(self.run, agent, self.stage, self.graphType, passive)
            if graph is None:
                continue
            yield agent, graph
    
    def iterateSynapses(self, graph):
        for preNode in xrange(graph.size):
            for postNode in xrange(graph.size):
                weight = self.getWeight(graph, preNode, postNode)
                if weight is not None:
                    yield preNode, postNode, weight

class Strength(WeightMetric):
    def getKey(self):
        return "strength-{0}-{1}-{2}".format(self.stage, self.graphType, self.weightType)
    
    def getLabel(self):
        if self.graphType == graph_mod.Graph.Type.ALL:
            return "Strength ({0})".format(self.weightType)
        else:
            return "{0} strength ({1})".format(self.graphType.capitalize(), self.weightType)
    
    def calculate(self, passive = False):
        for agent, graph in self.iterateGraphs(passive):
            if graph.size == 0:
                continue
            values = [0.0] * graph.size
            for preNode, postNode, weight in self.iterateSynapses(graph):
                values[preNode] += weight
                values[postNode] += weight
            yield agent, sum(values) / graph.size

class Weight(WeightMetric):
    def getKey(self):
        return "weight-{0}-{1}-{2}".format(self.stage, self.graphType, self.weightType)
    
    def getLabel(self):
        if self.graphType == graph_mod.Graph.Type.ALL:
            return "Synaptic weight ({0})".format(self.weightType)
        else:
            return "{0} synaptic weight ({1})".format(self.graphType.capitalize(), self.weightType)
    
    def calculate(self, passive = False):
        for agent, graph in self.iterateGraphs(passive):
            valueSum = 0.0
            count = 0
            for preNode, postNode, weight in self.iterateSynapses(graph):
                valueSum += weight
                count += 1
            if count > 0:
                yield agent, valueSum / count

def iterateMetrics():
    for attrName, attr in globals().iteritems():
        if isinstance(attr, type) and issubclass(attr, Metric) and not attrName.endswith("Metric"):
            yield attr
