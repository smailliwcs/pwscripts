import algorithms
import collections
import graph as graph_mod
import gzip
import math
import matplotlib
import numpy
import os
import sys
import utility

NAN = float("nan")

class Stage(utility.Enum):
    INCEPT = "incept"
    BIRTH = "birth"
    DEATH = "death"

class Metric(object):
    integral = False
    
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
    
    def initialize(self, run, passive = False, args = None, start = None):
        self.run = utility.getRun(run, passive)
        if args is not None:
            self.readArgs(args)
        self.start = start
    
    def getKey(self):
        raise NotImplementedError
    
    def getLabel(self):
        raise NotImplementedError
    
    def getDataFileName(self):
        return self.getKey() + ".txt"
    
    def getDataPath(self):
        return os.path.join(self.run, "data", self.getDataFileName())
    
    def readLines(self):
        with open(self.getDataPath()) as f:
            for line in f:
                if line.startswith("#"):
                    continue
                yield line
    
    def read(self):
        values = {}
        for line in self.readLines():
            key, value = line.split()
            values[int(key)] = float(value)
        return values
    
    def write(self, values):
        path = self.getDataPath()
        utility.makeDirectories(os.path.dirname(path))
        with open(path, "w") as f:
            for key, value in values.iteritems():
                f.write("{0} {1}\n".format(key, value))
    
    def calculate(self):
        raise NotImplementedError
    
    def getRange(self, values, tmin, tmax):
        raise NotImplementedError
    
    def toTimeBased(self, values, mean, tmin = None, tmax = None):
        raise NotImplementedError
    
    def getBins(self):
        pass
    
    def formatAxis(self, axis):
        pass

class TimeBasedMetric(Metric):
    def getRange(self, values, trange):
        result = {}
        for timestep, value in values.iteritems():
            if utility.contains(trange, timestep):
                result[timestep] = value
        return result
    
    def toTimeBased(self, values, mean, trange):
        return self.getRange(values, trange)

class AgentBasedMetric(Metric):
    def read(self):
        values = dict.fromkeys(utility.getAgents(self.run), NAN)
        values.update(super(AgentBasedMetric, self).read())
        return values
    
    def getTimesteps(self):
        metric = BirthTimestep()
        metric.initialize(self.run, start = self.start)
        return metric.read()
    
    def getRange(self, values, trange):
        result = {}
        for agent, timestep in self.getTimesteps().iteritems():
            if utility.contains(trange, timestep):
                result[agent] = values[agent]
        return result
    
    def toTimeBased(self, values, mean, trange):
        if mean:
            result = {}
            for timestep, agents in utility.getPopulations(self.run):
                if utility.contains(trange, timestep):
                    result[timestep] = numpy.nanmean(map(lambda agent: values[agent], agents))
            return result
        else:
            result = collections.defaultdict(list)
            for agent, timestep in self.getTimesteps().iteritems():
                if utility.contains(trange, timestep):
                    value = values[agent]
                    if value is not NAN:
                        result[timestep].append(value)
            return result

class LifespanMetric(AgentBasedMetric):
    integral = True
    
    def getValue(self, row):
        raise NotImplementedError
    
    def read(self):
        values = {}
        path = os.path.join(self.run, "lifespans.txt")
        for row in utility.getDataTable(path, "LifeSpans").rows():
            values[row["Agent"]] = self.getValue(row)
        return values

class OffspringMetric(AgentBasedMetric):
    def getCounts(self):
        values = collections.defaultdict(int)
        for event in utility.Event.read(self.run):
            if event.eventType != utility.EventType.BIRTH:
                continue
            values[event.parent1] += 1
            values[event.parent2] += 1
        return values

class StagedAgentBasedMetric(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
    
    def readArgs(self, args):
        self.stage = self.readArg(args, "stage")

class WeightMetric(AgentBasedMetric):
    class Type(utility.Enum):
        EXCITATORY = "excitatory"
        INHIBITORY = "inhibitory"
        ABSOLUTE = "absolute"
    
    def addArgs(self, parser):
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.GraphType.getNonInputValues()))
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
            return weight if weight > 0.0 else None
        elif self.weightType == WeightMetric.Type.INHIBITORY:
            return -weight if weight < 0.0 else None
        elif self.weightType == WeightMetric.Type.ABSOLUTE:
            return abs(weight) if weight != 0.0 else None
        else:
            assert False
    
    def getGraphs(self):
        for agent in utility.getAgents(self.run, self.start):
            graph = graph_mod.Graph.read(self.run, agent, self.stage, self.graphType)
            yield agent, graph
    
    def getSynapses(self, graph):
        for nodeOut in xrange(graph.size):
            for nodeIn in xrange(graph.size):
                weight = self.getWeight(graph, nodeOut, nodeIn)
                if weight is not None:
                    yield nodeOut, nodeIn, weight

class AgentEnergy(AgentBasedMetric):
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
            return "Total agent energy"
        else:
            return "Agent energy {0}".format(self.type)
    
    def getLifespans(self):
        metric = Lifespan()
        metric.initialize(self.run, start = self.start)
        return metric.read()
    
    def calculate(self):
        lifespans = self.getLifespans()
        for agent in utility.getAgents(self.run, self.start):
            lifespan = lifespans[agent]
            if lifespan == 0:
                value = NAN
            else:
                path = os.path.join(self.run, "energy", self.type, "agent_{0}.txt".format(agent))
                table = utility.getDataTable(path, "AgentEnergy{0}".format(self.type.capitalize()))
                value = sum(map(lambda row: row["Energy"], table.rows())) / lifespan
            yield agent, value

class BirthTimestep(LifespanMetric):
    def getKey(self):
        return "birth"
    
    def getLabel(self):
        return "Birth timestep"
    
    def getValue(self, row):
        return row["BirthStep"]

class Complexity(AgentBasedMetric):
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
        return "Complexity"
    
    def read(self):
        values = dict.fromkeys(utility.getAgents(self.run), NAN)
        for line in self.readLines():
            if self.polyworld:
                agent, value = line.split()
                value = float(value)
                if value == 0.0:
                    continue
                value *= math.log(2.0)
            elif self.jidt:
                agent, flag, value = line.split()
                if flag != "C":
                    continue
                value = float(value)
            else:
                assert False
            values[int(agent)] = value
        return values

class Consistency(TimeBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "group-size", metavar = "GROUP_SIZE", type = int, choices = tuple(xrange(8)))
    
    def readArgs(self, args):
        self.groupSize = self.readArg(args, "group-size")
    
    def getKey(self):
        return "consistency-{0}".format(self.groupSize)
    
    def getLabel(self):
        return "Consistency"

class DeathTimestep(LifespanMetric):
    def getKey(self):
        return "death"
    
    def getLabel(self):
        return "Death timestep"
    
    def getValue(self, row):
        return row["DeathStep"]

class Density(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.GraphType.getNonInputValues()))
    
    def readArgs(self, args):
        self.graphType = self.readArg(args, "graph-type")
    
    def getKey(self):
        return "density-{0}".format(self.graphType)
    
    def getLabel(self):
        return "Synaptic density"
    
    def calculate(self):
        for agent in utility.getAgents(self.run, self.start):
            graph = graph_mod.Graph.read(self.run, agent, Stage.INCEPT, self.graphType)
            if self.graphType == graph_mod.GraphType.ALL:
                countMax = graph.size * (graph.size - graph.nodeTypes.count(graph_mod.NodeType.INPUT) - 1)
            else:
                countMax = graph.size * (graph.size - 1)
            value = float(graph.getLinkCount()) / countMax if countMax > 0 else 0.0
            yield agent, value

class Efficiency(AgentBasedMetric):
    class Type(utility.Enum):
        LOCAL = "local"
        GLOBAL = "global"
    
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE", choices = tuple(Efficiency.Type.getValues()))
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.GraphType.getValues()))
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
        self.stage = self.readArg(args, "stage")
        self.graphType = self.readArg(args, "graph-type")
    
    def getKey(self):
        return "efficiency-{0}-{1}-{2}".format(self.type, self.stage, self.graphType)
    
    def getLabel(self):
        return "{0} efficiency".format(self.type.capitalize())
    
    def calculate(self):
        for agent in utility.getAgents(self.run, self.start):
            graph = graph_mod.Graph.read(self.run, agent, self.stage, self.graphType)
            if graph is None:
                yield agent, NAN
                continue
            if self.type == Efficiency.Type.LOCAL:
                values = []
                for node in xrange(graph.size):
                    neighborhood = graph.getNeighborhood(node, False)
                    values.append(algorithms.Efficiency.calculate(neighborhood.weights))
                value = sum(values) / graph.size if graph.size > 0 else 0.0
            elif self.type == Efficiency.Type.GLOBAL:
                value = algorithms.Efficiency.calculate(graph.weights)
            else:
                assert False
            yield agent, value

class Entropy(StagedAgentBasedMetric):
    def getKey(self):
        return "entropy-{0}".format(self.stage)
    
    def getLabel(self):
        return "Entropy"

class Expansion(StagedAgentBasedMetric):
    def getKey(self):
        return "expansion-{0}".format(self.stage)
    
    def getLabel(self):
        return "Phase space expansion"

class FoodDistance(AgentBasedMetric):
    def getKey(self):
        return "food-distance"
    
    def getLabel(self):
        return "Food distance"
    
    def calculate(self):
        for agent in utility.getAgents(self.run):
            path = os.path.join(self.run, "food", "distance", "agent_{0}.txt".format(agent))
            rows = utility.getDataTable(path, "FoodDistance").rows()
            if len(rows) == 0:
                value = NAN
            else:
                value = sum(map(lambda row: row["Distance"], rows)) / len(rows)
            yield agent, value

class FoodEnergy(TimeBasedMetric):
    def getKey(self):
        return "food-energy"
    
    def getLabel(self):
        return "Food energy"
    
    def read(self):
        values = {}
        path = os.path.join(self.run, "food", "energy.txt")
        for row in utility.getDataTable(path, "FoodEnergy").rows():
            values[row["Timestep"]] = row["Energy"]
        return values

class Gene(AgentBasedMetric):
    integral = True
    
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
    
    def calculate(self):
        for agent in utility.getAgents(self.run, self.start):
            path = os.path.join(self.run, "genome", "agents", "genome_{0}.txt.gz".format(agent))
            with gzip.open(path) as f:
                for index in xrange(self.index):
                    f.readline()
                yield agent, int(f.readline())
    
    def getBins(self):
        return numpy.linspace(0, 256, 65)
    
    def formatAxis(self, axis):
        axis.set_view_interval(0, 256, True)
        axis.set_major_locator(matplotlib.ticker.MultipleLocator(64))

class InfoModification(StagedAgentBasedMetric):
    class Type(utility.Enum):
        TRIVIAL = "trivial"
        NONTRIVIAL = "nontrivial"
        TOTAL = "total"
    
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE", choices = tuple(InfoModification.Type.getValues()))
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
        self.stage = self.readArg(args, "stage")
    
    def getKey(self):
        return "info-modification-{0}-{1}".format(self.type, self.stage)
    
    def getDataFileName(self):
        return "info-dynamics-{0}.txt".format(self.stage)
    
    def getLabel(self):
        return "{0} information modification".format(self.type.capitalize())
    
    def read(self):
        values = dict.fromkeys(utility.getAgents(self.run), NAN)
        for line in self.readLines():
            agent, flag, value = line.split(None, 2)
            if flag == "M":
                trivialValue, nontrivialValue = map(float, value.split())
                if self.type == InfoModification.Type.TRIVIAL:
                    value = trivialValue
                elif self.type == InfoModification.Type.NONTRIVIAL:
                    value = nontrivialValue
                elif self.type == InfoModification.Type.TOTAL:
                    value = trivialValue + nontrivialValue
                else:
                    assert False
                values[int(agent)] = value
        return values
    
    def formatAxis(self, axis):
        if self.type == InfoModification.Type.NONTRIVIAL:
            interval = axis.get_view_interval()
            axis.set_view_interval(interval[1], interval[0], True)

class InfoStorage(StagedAgentBasedMetric):
    def getKey(self):
        return "info-storage-{0}".format(self.stage)
    
    def getDataFileName(self):
        return "info-dynamics-{0}.txt".format(self.stage)
    
    def getLabel(self):
        return "Information storage"
    
    def read(self):
        values = dict.fromkeys(utility.getAgents(self.run), NAN)
        for line in self.readLines():
            agent, flag, value = line.split(None, 2)
            if flag == "S":
                values[int(agent)] = float(value)
        return values

class InfoTransfer(StagedAgentBasedMetric):
    def getKey(self):
        return "info-transfer-{0}".format(self.stage)
    
    def getDataFileName(self):
        return "info-dynamics-{0}.txt".format(self.stage)
    
    def getLabel(self):
        return "Information transfer"
    
    def read(self):
        values = dict.fromkeys(utility.getAgents(self.run), NAN)
        for line in self.readLines():
            agent, flag, value = line.split(None, 2)
            if flag == "T":
                values[int(agent)] = float(value)
        return values

class Integration(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE")
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
        assert self.type.find("jidt") >= 0
    
    def getKey(self):
        return "integration-{0}".format(self.type)
    
    def getDataFileName(self):
        return "complexity-{0}.txt".format(self.type)
    
    def getLabel(self):
        return "Integration"
    
    def read(self):
        values = dict.fromkeys(utility.getAgents(self.run), NAN)
        for line in self.readLines():
            agent, flag, value = line.split()
            if flag == "I":
                values[int(agent)] = float(value)
        return values

class LearningRate(AgentBasedMetric):
    def getKey(self):
        return "learning-rate"
    
    def getLabel(self):
        return "Learning rate"
    
    def calculate(self):
        for agent in utility.getAgents(self.run, self.start):
            path = os.path.join(self.run, "brain", "synapses", "synapses_{0}_{1}.txt.gz".format(agent, Stage.INCEPT))
            with gzip.open(path) as f:
                f.readline()
                values = []
                for line in f:
                    values.append(abs(float(line.split()[3])))
            value = sum(values) / len(values) if len(values) > 0 else 0.0
            yield agent, value

class Lifespan(LifespanMetric):
    def getKey(self):
        return "lifespan"
    
    def getLabel(self):
        return "Lifespan"
    
    def getValue(self, row):
        return row["DeathStep"] - row["BirthStep"]

class MeanTimestep(LifespanMetric):
    def getValue(self, row):
        return (row["BirthStep"] + row["DeathStep"]) / 2

class Modularity(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.GraphType.getValues()))
    
    def readArgs(self, args):
        self.stage = self.readArg(args, "stage")
        self.graphType = self.readArg(args, "graph-type")
    
    def getKey(self):
        return "modularity-{0}-{1}".format(self.stage, self.graphType)
    
    def getLabel(self):
        return "Modularity"
    
    def calculate(self):
        for agent in utility.getAgents(self.run, self.start):
            graph = graph_mod.Graph.read(self.run, agent, self.stage, self.graphType)
            if graph is None:
                yield agent, NAN
                continue
            yield agent, algorithms.Modularity.calculate(graph.weights)

class NeuronCount(AgentBasedMetric):
    integral = True
    
    def addArgs(self, parser):
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.GraphType.getValues()))
    
    def readArgs(self, args):
        self.graphType = self.readArg(args, "graph-type")
    
    def getKey(self):
        return "neuron-count-{0}".format(self.graphType)
    
    def getLabel(self):
        if self.graphType == graph_mod.GraphType.ALL:
            return "Neuron count"
        else:
            return "{0} neuron count".format(self.graphType.capitalize())
    
    def calculate(self):
        for agent in utility.getAgents(self.run, self.start):
            graph = graph_mod.Graph.read(self.run, agent, Stage.INCEPT, self.graphType)
            if graph is None:
                yield agent, NAN
                continue
            yield agent, graph.size

class OffspringCount(OffspringMetric):
    def getKey(self):
        return "offspring-count"
    
    def getLabel(self):
        return "Offspring count"
    
    def read(self):
        return self.getCounts()

class OffspringRate(OffspringMetric):
    def getKey(self):
        return "offspring-rate"
    
    def getLabel(self):
        return "Offspring rate"
    
    def getLifespans(self):
        metric = Lifespan()
        metric.initialize(self.run, start = self.start)
        return metric.read()
    
    def read(self):
        values = {}
        counts = self.getCounts()
        for agent, lifespan in self.getLifespans().iteritems():
            values[agent] = float(counts[agent]) / lifespan if lifespan > 0 else 0.0
        return values

class Population(TimeBasedMetric):
    integral = True
    
    def getKey(self):
        return "population"
    
    def getLabel(self):
        return "Population"
    
    def read(self):
        values = {}
        values[0] = utility.getInitialAgentCount(self.run)
        path = os.path.join(self.run, "population.txt")
        for row in utility.getDataTable(path, "Population").rows():
            values[row["T"]] = row["Population"]
        return values

class ProgenyRate(AgentBasedMetric):
    def getKey(self):
        return "progeny-rate"
    
    def getLabel(self):
        return "Progeny rate"
    
    def getBirths(self):
        metric = BirthTimestep()
        metric.initialize(self.run, start = self.start)
        return metric.read()
    
    def calculate(self):
        children = collections.defaultdict(list)
        for event in utility.Event.read(self.run):
            if event.eventType != utility.EventType.BIRTH:
                continue
            children[event.parent1].append(event.agent)
            children[event.parent2].append(event.agent)
        end = utility.getFinalTimestep(self.run)
        for agent, start in self.getBirths().iteritems():
            if start == end:
                value = 0.0
            else:
                unexpanded = set(children[agent])
                expanded = set()
                while len(unexpanded) > 0:
                    descendant = unexpanded.pop()
                    if descendant not in expanded:
                        unexpanded.update(children[descendant])
                        expanded.add(descendant)
                value = float(len(expanded)) / (end - start)
            yield agent, value

class SmallWorldness(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.GraphType.getValues()))
    
    def readArgs(self, args):
        self.stage = self.readArg(args, "stage")
        self.graphType = self.readArg(args, "graph-type")
    
    def getKey(self):
        return "small-worldness-{0}-{1}".format(self.stage, self.graphType)
    
    def getLabel(self):
        return "Small-worldness"
    
    def getEfficiencies(self, efficiencyType):
        metric = Efficiency()
        metric.type = efficiencyType
        metric.stage = self.stage
        metric.graphType = self.graphType
        metric.initialize(self.run, start = self.start)
        return metric.read()
    
    def read(self):
        values = {}
        localValues = self.getEfficiencies(Efficiency.Type.LOCAL)
        globalValues = self.getEfficiencies(Efficiency.Type.GLOBAL)
        for agent in utility.getAgents(self.run):
            localValue = localValues.get(agent)
            globalValue = globalValues.get(agent)
            if localValue is None or globalValue is None:
                value = NAN
            else:
                value = localValue * globalValue
            values[agent] = value
        return values

class Strength(WeightMetric):
    def getKey(self):
        return "strength-{0}-{1}-{2}".format(self.stage, self.graphType, self.weightType)
    
    def getLabel(self):
        return "{0} synaptic strength".format(self.weightType.capitalize())
    
    def calculate(self):
        for agent, graph in self.getGraphs():
            if graph is None:
                yield agent, NAN
                continue
            values = [0.0] * graph.size
            for nodeOut, nodeIn, weight in self.getSynapses(graph):
                values[nodeOut] += weight
                values[nodeIn] += weight
            value = sum(values) / graph.size if graph.size > 0 else 0.0
            yield agent, value

class SynapseCount(AgentBasedMetric):
    integral = True
    
    def addArgs(self, parser):
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.GraphType.getValues()))
    
    def readArgs(self, args):
        self.graphType = self.readArg(args, "graph-type")
    
    def getKey(self):
        return "synapse-count-{0}".format(self.graphType)
    
    def getLabel(self):
        return "Synapse count"
    
    def calculate(self):
        for agent in utility.getAgents(self.run, self.start):
            graph = graph_mod.Graph.read(self.run, agent, Stage.INCEPT, self.graphType)
            if graph is None:
                yield agent, NAN
                continue
            yield agent, graph.getLinkCount()

class Timestep(TimeBasedMetric):
    integral = True
    
    def getKey(self):
        return "time"
    
    def getLabel(self):
        return "Timestep"
    
    def read(self):
        values = {}
        for timestep in xrange(0, utility.getFinalTimestep(self.run) + 1):
            values[timestep] = timestep
        return values

class Weight(WeightMetric):
    def getKey(self):
        return "weight-{0}-{1}-{2}".format(self.stage, self.graphType, self.weightType)
    
    def getLabel(self):
        return "{0} synaptic weight".format(self.weightType.capitalize())
    
    def calculate(self):
        for agent, graph in self.getGraphs():
            if graph is None:
                yield agent, NAN
                continue
            values = []
            for nodeOut, nodeIn, weight in self.getSynapses(graph):
                values.append(weight)
            value = sum(values) / len(values) if len(values) > 0 else 0.0
            yield agent, value

def getMetrics():
    for name, value in globals().iteritems():
        if isinstance(value, type) and issubclass(value, Metric) and not name.endswith("Metric"):
            yield name, value

metrics = {}
metrics.update(getMetrics())
