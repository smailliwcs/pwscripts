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

def getBin(timestep, tstep):
    index = timestep / tstep
    if timestep % tstep > 0:
        index += 1
    return index * tstep

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
        path = self.getDataPath()
        fn = gzip.open if path.endswith(".gz") else open
        with fn(path) as f:
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
    
    def getInterval(self, values, tival):
        raise NotImplementedError
    
    def toTimeBased(self, values, tival, tstep = 0):
        raise NotImplementedError
    
    def aggregate(self, values):
        return numpy.nanmean(values)
    
    def getBins(self):
        pass
    
    def formatAxis(self, axis):
        pass

class TimeBasedMetric(Metric):
    def getInterval(self, values, tival):
        result = {}
        for timestep, value in values.iteritems():
            if utility.contains(tival, timestep):
                result[timestep] = value
        return result
    
    def toTimeBased(self, values, tival, tstep = 0):
        if tstep == 0:
            return self.getInterval(values, tival)
        else:
            result = collections.defaultdict(list)
            for timestep, value in values.iteritems():
                if utility.contains(tival, timestep):
                    result[getBin(timestep, tstep)].append(value)
            return {timestep: self.aggregate(vals) for timestep, vals in result.iteritems()}

class AgentBasedMetric(Metric):
    def read(self):
        values = dict.fromkeys(utility.getAgents(self.run), NAN)
        values.update(super(AgentBasedMetric, self).read())
        return values
    
    def getTimesteps(self):
        metric = BirthTimestep()
        metric.initialize(self.run, start = self.start)
        return metric.read()
    
    def getInterval(self, values, tival):
        result = {}
        for agent, timestep in self.getTimesteps().iteritems():
            if utility.contains(tival, timestep):
                result[agent] = values[agent]
        return result
    
    def toTimeBased(self, values, tival, tstep = 0):
        result = collections.defaultdict(list)
        for agent, timestep in self.getTimesteps().iteritems():
            if utility.contains(tival, timestep):
                value = values[agent]
                if value is not NAN:
                    if tstep == 0:
                        result[timestep].append(value)
                    else:
                        result[getBin(timestep, tstep)].append(value)
        if tstep == 0:
            return result
        else:
            return {timestep: self.aggregate(vals) for timestep, vals in result.iteritems()}

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

class Activity(TimeBasedMetric):
    class Type(utility.Enum):
        MEAN = "mean"
        NEW = "new"
    
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE", choices = tuple(Activity.Type.getValues()))
        self.addArg(parser, "amin", metavar = "AMIN", nargs = "?", type = float)
        self.addArg(parser, "amax", metavar = "AMAX", nargs = "?", type = float)
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
        self.amin = self.readArg(args, "amin")
        self.amax = self.readArg(args, "amax")
        if self.type == Activity.Type.NEW:
            assert self.amin is not None and self.amax is not None
    
    def getKey(self):
        return "activity-{0}".format(self.type)
    
    def getDataFileName(self):
        return "activity.txt.gz"
    
    def getLabel(self):
        if self.type == Activity.Type.MEAN:
            return "Mean cumulative evolutionary activity"
        elif self.type == Activity.Type.NEW:
            return "New evolutionary activity"
        else:
            assert False
    
    def getDiversities(self):
        metric = Diversity()
        metric.initialize(self.run)
        return metric.read()
    
    def read(self):
        activities = collections.defaultdict(int)
        for line in self.readLines():
            timestep, activity, count = line.split()
            activity = int(activity)
            if self.type == Activity.Type.NEW:
                if activity < self.amin or activity > self.amax:
                    continue
            activities[int(timestep)] += activity * int(count)
        values = {}
        for timestep, diversity in self.getDiversities().iteritems():
            values[timestep] = float(activities[timestep]) / diversity
        return values

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
    def getKey(self):
        return "consistency"
    
    def getLabel(self):
        return "Consistency"

class DeathTimestep(LifespanMetric):
    def getKey(self):
        return "death"
    
    def getLabel(self):
        return "Death timestep"
    
    def getValue(self, row):
        return row["DeathStep"]

class Degree(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "graph-type", metavar = "GRAPH_TYPE", choices = tuple(graph_mod.GraphType.getNonInputValues()))
    
    def readArgs(self, args):
        self.graphType = self.readArg(args, "graph-type")
    
    def getKey(self):
        return "degree-{0}".format(self.graphType)
    
    def getLabel(self):
        return "Synaptic degree"
    
    def calculate(self):
        for agent in utility.getAgents(self.run, self.start):
            graph = graph_mod.Graph.read(self.run, agent, Stage.INCEPT, self.graphType)
            value = 2.0 * graph.getLinkCount() / graph.size if graph.size > 0 else 0.0
            yield agent, value

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

class Diversity(TimeBasedMetric):
    integral = True
    
    def getKey(self):
        return "diversity"
    
    def getLabel(self):
        return "Diversity"

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

class Entropy(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
    
    def readArgs(self, args):
        self.stage = self.readArg(args, "stage")
    
    def getKey(self):
        return "entropy-{0}".format(self.stage)
    
    def getLabel(self):
        return "Differential entropy"

class Expansion(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
    
    def readArgs(self, args):
        self.stage = self.readArg(args, "stage")
    
    def getKey(self):
        return "expansion-{0}".format(self.stage)
    
    def getLabel(self):
        return "Phase space expansion"

class FoodConsumption(TimeBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE")
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
    
    def getKey(self):
        return "{0}-consumption".format(self.type.lower())
    
    def getLabel(self):
        return "{0} consumption".format(self.type)
    
    def read(self):
        values = collections.defaultdict(float)
        path = os.path.join(self.run, "energy", "consumption.txt")
        for row in utility.getDataTable(path, "FoodConsumption").rows():
            if row["FoodType"] == self.type:
                values[row["Timestep"]] += row["EnergyRaw"]
        return values

class FoodConsumptionRate(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE")
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
    
    def getKey(self):
        return "{0}-consumption-rate".format(self.type.lower())
    
    def getLabel(self):
        return "{0} consumption rate".format(self.type)
    
    def getLifespans(self):
        metric = Lifespan()
        metric.initialize(self.run, start = self.start)
        return metric.read()
    
    def calculate(self):
        values = collections.defaultdict(float)
        path = os.path.join(self.run, "energy", "consumption.txt")
        for row in utility.getDataTable(path, "FoodConsumption").rows():
            if row["FoodType"] == self.type:
                values[row["Agent"]] += row["EnergyRaw"]
        for agent, lifespan in self.getLifespans().iteritems():
            yield agent, float(values[agent]) / lifespan if lifespan > 0 else 0.0

class FoodEnergy(TimeBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE")
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
    
    def getKey(self):
        return "{0}-energy".format(self.type.lower())
    
    def getLabel(self):
        return "{0} energy".format(self.type)
    
    def read(self):
        values = {}
        path = os.path.join(self.run, "energy", "food.txt")
        for row in utility.getDataTable(path, "FoodEnergy").rows():
            values[row["Timestep"]] = row[self.type]
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
            for index in xrange(self.index):
                f.readline()
            line = f.readline()
            if line != "":
                title = line.split(" :: ")[0]
        replacements = {
            "_": "\\_",
            ">": "\\textgreater",
            "InternalNeurGroup ": ""
        }
        for old, new in replacements.iteritems():
            title = title.replace(old, new)
        return "\\texttt{{{0}}} gene".format(title)
    
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

class InfoModification(AgentBasedMetric):
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

class InfoStorage(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
    
    def readArgs(self, args):
        self.stage = self.readArg(args, "stage")
    
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

class InfoTransfer(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "source", metavar = "SOURCE")
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
    
    def readArgs(self, args):
        self.source = self.readArg(args, "source")
        self.stage = self.readArg(args, "stage")
    
    def getKey(self):
        return "info-transfer-{0}-{1}".format(self.source.lower(), self.stage)
    
    def getDataFileName(self):
        return "info-dynamics-{0}.txt".format(self.stage)
    
    def getLabel(self):
        if self.source == "Total":
            return "Total information transfer"
        else:
            return "\\texttt{{{0}}} information transfer".format(self.source)
    
    def read(self):
        values = dict.fromkeys(utility.getAgents(self.run), NAN)
        for line in self.readLines():
            agent, flag, value = line.split(None, 2)
            if flag == "T":
                source, value = value.split()
                if source == self.source:
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
    integral = True
    
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
    
    def getTimesteps(self):
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
        for agent, start in self.getTimesteps().iteritems():
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
    
    def aggregate(self, values):
        return max(values)

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
