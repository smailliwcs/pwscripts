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
    def formatAxis(cls, axis):
        pass
    
    def getName(self):
        return type(self).__name__
    
    def getArgName(self, name):
        return "{0}_{1}{2}".format(name, self.getName(), hash(self))
    
    def addArg(self, parser, name, **kwargs):
        parser.add_argument(self.getArgName(name), **kwargs)
    
    def addArgs(self, parser):
        pass
    
    def readArg(self, args, name):
        return getattr(args, self.getArgName(name))
    
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
        if passive:
            pathBase = os.path.join(self.run, "passive")
        else:
            pathBase = self.run
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
            for key, value in values.iteritems():
                f.write("{0} {1}\n".format(key, value))
    
    def calculate(self, passive = False):
        raise NotImplementedError
    
    def toTimeBased(self, values):
        raise NotImplementedError

class TimeMetric(Metric):
    def toTimeBased(self, values):
        return values

class AgentMetric(Metric):
    def getTimesteps(self):
        metric = MeanTimestep()
        metric.initialize(self.run)
        return metric.read()
    
    def toTimeBased(self, values):
        result = collections.defaultdict(list)
        for agent, timestep in self.getTimesteps().iteritems():
            if agent in values:
                result[timestep].append(values[agent])
        return result

class StagedAgentMetric(AgentMetric):
    def addArgs(self, parser):
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
    
    def readArgs(self, args):
        self.stage = self.readArg(args, "stage")

class AgentEnergy(AgentMetric):
    class Type(utility.Enum):
        IN = "in"
        OUT = "out"
        TOTAL = "total"
    
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE", choices = tuple(AgentEnergy.Type.getValues()))
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
    
    def getKey(self):
        return "agent-energy-{0}".format(self.type)
    
    def getLabel(self):
        if self.type == AgentEnergy.Type.TOTAL:
            return "Agent energy"
        else:
            return "Agent energy {0}".format(self.type)
    
    def getLifespans(self):
        metric = Lifespan()
        metric.truncated = False
        metric.initialize(self.run)
        return metric.read()
    
    def calculate(self, passive = False):
        assert not passive
        lifespans = self.getLifespans()
        for agent in utility.getAgents(self.run):
            if agent not in lifespans:
                continue
            lifespan = lifespans[agent]
            if lifespan == 0:
                value = 0.0
            else:
                path = os.path.join(self.run, "energy", self.type, "agent_{0}.txt".format(agent))
                table = utility.getDataTable(path, "AgentEnergy{0}".format(self.type.capitalize()))
                value = sum(map(lambda row: row["Energy"], table.rows())) / lifespan
            yield agent, value

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
        self.addArg(parser, "group-size", metavar = "GROUP_SIZE", type = int, choices = tuple(xrange(8)))
    
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
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.Graph.Type.getNonInputValues()))
    
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
        for agent in utility.getAgents(self.run):
            graph = graph_mod.Graph.read(self.run, agent, Stage.INCEPT, self.graphType, passive)
            if self.graphType == graph_mod.Graph.Type.ALL:
                countMax = graph.size * (graph.size - graph.nodeTypes.count(graph_mod.NodeType.INPUT) - 1)
            else:
                countMax = graph.size * (graph.size - 1)
            if countMax == 0:
                value = 0.0
            else:
                value = float(graph.getLinkCount()) / countMax
            yield agent, value

class Efficiency(AgentMetric):
    class Type(utility.Enum):
        LOCAL = "local"
        GLOBAL = "global"
    
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE", choices = tuple(Efficiency.Type.getValues()))
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.Graph.Type.getValues()))
    
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
        for agent in utility.getAgents(self.run):
            graph = graph_mod.Graph.read(self.run, agent, self.stage, self.graphType, passive)
            if graph is None:
                continue
            if self.type == Efficiency.Type.LOCAL:
                if graph.size == 0:
                    value = 0.0
                else:
                    values = []
                    for node in xrange(graph.size):
                        neighborhood = graph.getNeighborhood(node, False)
                        distances = algorithms.Distance.calculate(neighborhood.weights)
                        values.append(algorithms.Efficiency.calculate(distances))
                    value = sum(values) / graph.size
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

class FoodDistance(AgentMetric):
    def getKey(self):
        return "food-distance"
    
    def getLabel(self):
        return "Food distance"
    
    def read(self, passive = False):
        assert not passive
        values = {}
        for agent in utility.getAgents(self.run):
            path = os.path.join(self.run, "food", "distance", "agent_{0}.txt".format(agent))
            rows = utility.getDataTable(path, "FoodDistance").rows()
            if len(rows) > 0:
                values[agent] = sum(map(lambda row: row["Distance"], rows)) / len(rows)
        return values
    
class FoodEnergy(TimeMetric):
    @classmethod
    def formatAxis(cls, axis):
        axis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda tick, position: format(tick / 1e3, "g")))
    
    def getKey(self):
        return "food-energy"
    
    def getLabel(self):
        return r"Food energy ($\times 10^3$)"
    
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
    def formatAxis(cls, axis):
        axis.set_major_locator(matplotlib.ticker.MultipleLocator(64))
    
    def addArgs(self, parser):
        self.addArg(parser, "index", metavar = "INDEX", type = int)
    
    def readArgs(self, args):
        self.index = self.readArg(args, "index")
    
    def getKey(self):
        return "gene-{0}".format(self.index)
    
    def getLabel(self):
        path = os.path.join(self.run, "genome", "meta", "geneindex.txt")
        with open(path) as f:
            for index in xrange(self.index):
                f.readline()
            title = f.readline().split()[1]
        path = os.path.join(self.run, "genome", "meta", "genetitle.txt")
        with open(path) as f:
            found = True
            for index in xrange(self.index):
                if f.readline() == "":
                    found = False
                    break
            if found:
                title = f.readline().split(" :: ")[0]
        return "{0} gene".format(title.replace("_", "\\_"))
    
    def calculate(self, passive = False):
        if passive:
            pathBase = os.path.join(self.run, "passive")
        else:
            pathBase = self.run
        for agent in utility.getAgents(self.run):
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
        if passive:
            pathBase = os.path.join(self.run, "passive")
        else:
            pathBase = self.run
        for agent in utility.getAgents(self.run):
            path = os.path.join(pathBase, "brain", "synapses", "synapses_{0}_{1}.txt.gz".format(agent, Stage.INCEPT))
            with gzip.open(path) as f:
                f.readline()
                values = []
                for line in f:
                    values.append(abs(float(line.split()[3])))
            if len(values) == 0:
                value = 0.0
            else:
                value = sum(values) / len(values)
            yield agent, value

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

class MeanTimestep(LifespanMetric):
    def getValue(self, row):
        return (row["BirthStep"] + row["DeathStep"]) / 2

class Lifespan(LifespanMetric):
    def addArgs(self, parser):
        self.addArg(parser, "truncated", metavar = "TRUNCATED", type = int, choices = (0, 1))
    
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

class Modularity(AgentMetric):
    def addArgs(self, parser):
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.Graph.Type.getValues()))
    
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
        for agent in utility.getAgents(self.run):
            graph = graph_mod.Graph.read(self.run, agent, self.stage, self.graphType, passive)
            if graph is None:
                continue
            yield agent, algorithms.Modularity.calculate(graph.weights)

class NeuronCount(AgentMetric):
    integral = True
    
    def addArgs(self, parser):
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.Graph.Type.getValues()))
    
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
        for agent in utility.getAgents(self.run):
            graph = graph_mod.Graph.read(self.run, agent, Stage.INCEPT, self.graphType, passive)
            if graph is None:
                continue
            yield agent, graph.size

class OffspringRate(AgentMetric):
    def getKey(self):
        return "offspring-rate"
    
    def getLabel(self):
        return "Offspring rate"
    
    def getLifespans(self):
        metric = Lifespan()
        metric.initial = False
        metric.initialize(self.run)
        return metric.read()
    
    def calculate(self, passive = False):
        assert not passive
        counts = collections.defaultdict(int)
        for event in utility.Event.read(self.run):
            if event.type != utility.Event.Type.BIRTH:
                continue
            counts[event.parent1] += 1
            counts[event.parent2] += 1
        for agent, lifespan in self.getLifespans().iteritems():
            if lifespan == 0:
                value = 0.0
            else:
                value = float(counts[agent]) / lifespan
            yield agent, value

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

class ProgenyRate(AgentMetric):
    def getKey(self):
        return "progeny-rate"
    
    def getLabel(self):
        return "Progeny rate"
    
    def getBirths(self):
        metric = BirthTimestep()
        metric.initialize(self.run)
        return metric.read()
    
    def calculate(self, passive = False):
        assert not passive
        children = collections.defaultdict(list)
        for event in utility.Event.read(self.run):
            if event.type != utility.Event.Type.BIRTH:
                continue
            children[event.parent1].append(event.agent)
            children[event.parent2].append(event.agent)
        end = utility.getFinalTimestep(self.run)
        for agent, birth in self.getBirths().iteritems():
            if birth == end:
                continue
            unexpanded = set(children[agent])
            expanded = set()
            while len(unexpanded) > 0:
                descendant = unexpanded.pop()
                if descendant not in expanded:
                    unexpanded.update(children[descendant])
                    expanded.add(descendant)
            yield agent, float(len(expanded)) / (end - birth)

class SmallWorldness(AgentMetric):
    def addArgs(self, parser):
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.Graph.Type.getValues()))
    
    def readArgs(self, args):
        self.stage = self.readArg(args, "stage")
        self.graphType = self.readArg(args, "graph-type")
    
    def getKey(self):
        return "small-worldness-{0}-{1}".format(self.stage, self.graphType)
    
    def getLabel(self):
        if self.graphType == graph_mod.Graph.Type.ALL:
            return "Small-worldness"
        else:
            return "{0} small-worldness".format(self.graphType.capitalize())
    
    def getEfficiencies(self, type, passive = False):
        metric = Efficiency()
        metric.type = type
        metric.stage = self.stage
        metric.graphType = self.graphType
        metric.initialize(self.run)
        return metric.read(passive)
    
    def read(self, passive = False):
        efficienciesLocal = self.getEfficiencies(Efficiency.Type.LOCAL, passive)
        efficienciesGlobal = self.getEfficiencies(Efficiency.Type.GLOBAL, passive)
        values = {}
        for agent in utility.getAgents(self.run):
            efficiencyLocal = efficienciesLocal.get(agent)
            efficiencyGlobal = efficienciesGlobal.get(agent)
            if efficiencyLocal is not None and efficiencyGlobal is not None:
                values[agent] = efficiencyLocal * efficiencyGlobal
        return values

class Timestep(TimeMetric):
    integral = True
    
    def getKey(self):
        return "time"
    
    def getLabel(self):
        return "Timestep"
    
    def read(self, passive = False):
        return {timestep: timestep for timestep in xrange(0, utility.getFinalTimestep(self.run) + 1)}

class WeightMetric(AgentMetric):
    class Type(utility.Enum):
        EXCITATORY = "excitatory"
        INHIBITORY = "inhibitory"
        ABSOLUTE = "absolute"
    
    def addArgs(self, parser):
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.Graph.Type.getNonInputValues()))
        self.addArg(parser, "weight-type", metavar = "WEIGHT_TYPE", choices = tuple(WeightMetric.Type.getValues()))
    
    def readArgs(self, args):
        self.stage = self.readArg(args, "stage")
        self.graphType = self.readArg(args, "graph-type")
        self.weightType = self.readArg(args, "weight-type")
    
    def getWeight(self, graph, nodeOut, nodeIn):
        weight = graph.weights[nodeOut][nodeIn]
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
    
    def getGraphs(self, passive = False):
        for agent in utility.getAgents(self.run):
            graph = graph_mod.Graph.read(self.run, agent, self.stage, self.graphType, passive)
            if graph is None:
                continue
            yield agent, graph
    
    def getSynapses(self, graph):
        for nodeOut in xrange(graph.size):
            for nodeIn in xrange(graph.size):
                weight = self.getWeight(graph, nodeOut, nodeIn)
                if weight is not None:
                    yield nodeOut, nodeIn, weight

class Strength(WeightMetric):
    def getKey(self):
        return "strength-{0}-{1}-{2}".format(self.stage, self.graphType, self.weightType)
    
    def getLabel(self):
        if self.graphType == graph_mod.Graph.Type.ALL:
            return "Strength ({0})".format(self.weightType)
        else:
            return "{0} strength ({1})".format(self.graphType.capitalize(), self.weightType)
    
    def calculate(self, passive = False):
        for agent, graph in self.getGraphs(passive):
            if graph.size == 0:
                value = 0.0
            else:
                values = [0.0] * graph.size
                for nodeOut, nodeIn, weight in self.getSynapses(graph):
                    values[nodeOut] += weight
                    values[nodeIn] += weight
                value = sum(values) / graph.size
            yield agent, value

class Weight(WeightMetric):
    def getKey(self):
        return "weight-{0}-{1}-{2}".format(self.stage, self.graphType, self.weightType)
    
    def getLabel(self):
        if self.graphType == graph_mod.Graph.Type.ALL:
            return "Synaptic weight ({0})".format(self.weightType)
        else:
            return "{0} synaptic weight ({1})".format(self.graphType.capitalize(), self.weightType)
    
    def calculate(self, passive = False):
        for agent, graph in self.getGraphs(passive):
            values = []
            for nodeOut, nodeIn, weight in self.getSynapses(graph):
                values.append(weight)
            if len(values) == 0:
                value = 0.0
            else:
                value = sum(values) / len(values)
            yield agent, value

def getMetrics():
    for name, value in globals().iteritems():
        if isinstance(value, type) and issubclass(value, Metric) and not name.endswith("Metric"):
            yield name, value

metrics = {}
metrics.update(getMetrics())
