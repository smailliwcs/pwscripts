import algorithms
import argparse
import collections
import graph as graph_mod
import gzip
import math
import numpy
import os
import sys
import utility

NAN = float("nan")

class OptionalStoreAction(argparse.Action):
    def __init__(self, type = None, **kwargs):
        super(OptionalStoreAction, self).__init__(**kwargs)
        self.__type = type
    
    def __call__(self, parser, namespace, values, option_string = None):
        if values == "None":
            values = None
        elif self.__type is not None:
            values = self.__type(values)
        setattr(namespace, self.dest, values)

def digitize(value, step):
    index = value / step
    if value % step > 0:
        index += 1
    return index * step

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
        self.passive = passive
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
                if line == "\n":
                    break
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
    
    def aggregate(self, values):
        return numpy.nanmean(values)
    
    def constrain(self, values, interval):
        raise NotImplementedError
    
    def toTimeBased(self, values, interval):
        raise NotImplementedError
    
    def toSeries(self, values, interval, step):
        raise NotImplementedError
    
    def getBins(self):
        pass

class TimeBasedMetric(Metric):
    def constrain(self, values, interval):
        result = {}
        for timestep, value in values.iteritems():
            if utility.contains(interval, timestep):
                result[timestep] = value
        return result
    
    def toTimeBased(self, values, interval):
        return self.constrain(values, interval)
    
    def toSeries(self, values, interval, step):
        result = collections.defaultdict(list)
        for timestep, value in values.iteritems():
            if utility.contains(interval, timestep):
                result[digitize(timestep, step)].append(value)
        return {timestep: self.aggregate(result[timestep]) for timestep in result}

class AgentBasedMetric(Metric):
    def read(self):
        values = dict.fromkeys(utility.getAgents(self.run), NAN)
        values.update(super(AgentBasedMetric, self).read())
        return values
    
    def getTimesteps(self):
        metric = BirthTimestep()
        metric.initialize(self.run, start = self.start)
        return metric.read()
    
    def constrain(self, values, interval):
        result = {}
        for agent, timestep in self.getTimesteps().iteritems():
            if utility.contains(interval, timestep):
                value = values[agent]
                if math.isnan(value) or math.isinf(value):
                    continue
                result[agent] = value
        return result
    
    def toTimeBased(self, values, interval):
        result = collections.defaultdict(list)
        for agent, timestep in self.getTimesteps().iteritems():
            if utility.contains(interval, timestep):
                value = values[agent]
                if math.isnan(value):
                    continue
                result[timestep].append(value)
        return result
    
    def toSeries(self, values, interval, step):
        result = collections.defaultdict(list)
        for timestep, agents in utility.getPopulations(self.run):
            if utility.contains(interval, timestep):
                result[digitize(timestep, step)].extend(map(lambda agent: values[agent], agents))
        return {timestep: self.aggregate(result[timestep]) for timestep in result}

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
        self.type = utility.EventType.VIRTUAL if self.passive else utility.EventType.BIRTH
        values = collections.defaultdict(int)
        for event in utility.Event.read(self.run):
            if event.eventType != self.type:
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
    
    def read(self):
        weightMax = float(utility.getParameter(self.run, "MaxSynapseWeight"))
        values = {}
        for line in self.readLines():
            key, value = line.split()
            values[int(key)] = float(value) * weightMax
        return values

class Adaptivity(AgentBasedMetric):
    class Type(utility.Enum):
        SURVIVAL = "survival"
        FORAGING = "foraging"
        REPRODUCTIVE = "reproductive"
    
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE", choices = tuple(Adaptivity.Type.getValues()))
        self.addArg(parser, "condition", metavar = "CONDITION", action = OptionalStoreAction)
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
        self.condition = self.readArg(args, "condition")
    
    def getKey(self):
        if self.condition is None:
            return "adaptivity-{0}".format(self.type)
        else:
            return "adaptivity-{0}-{1}".format(self.type, self.condition)
    
    def getDataFileName(self):
        if self.condition is None:
            return "adaptivity.txt"
        else:
            return "adaptivity-{0}.txt".format(self.condition)
    
    def getLabel(self):
        return "{0} adaptivity".format(self.type.title())
    
    def read(self):
        values = collections.defaultdict(list)
        for line in self.readLines():
            chunks = line.split()
            agent = int(chunks[0])
            lifespan = float(chunks[1])
            if self.type == Adaptivity.Type.SURVIVAL:
                value = lifespan
            elif self.type == Adaptivity.Type.FORAGING:
                value = float(chunks[2]) / lifespan
            elif self.type == Adaptivity.Type.REPRODUCTIVE:
                value = float(chunks[3]) / lifespan
            else:
                assert False
            values[agent].append(value)
        return {agent: numpy.mean(values[agent]) for agent in utility.getAgents(self.run)}

class BirthCount(TimeBasedMetric):
    integral = True
    
    def getKey(self):
        return "birth-count"
    
    def getLabel(self):
        return "Birth rate"
    
    def read(self):
        self.type = utility.EventType.VIRTUAL if self.passive else utility.EventType.BIRTH
        values = dict.fromkeys(xrange(utility.getFinalTimestep(self.run) + 1), 0)
        for event in utility.Event.read(self.run):
            if event.eventType == self.type:
                values[event.timestep] += 1
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
            graph = graph_mod.Graph.read(self.run, agent, Stage.BIRTH, self.graphType)
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
            graph = graph_mod.Graph.read(self.run, agent, Stage.BIRTH, self.graphType)
            if self.graphType == graph_mod.GraphType.ALL:
                countMax = graph.size * (graph.size - graph.nodeTypes.count(graph_mod.NodeType.INPUT) - 1)
            else:
                countMax = graph.size * (graph.size - 1)
            value = float(graph.getLinkCount()) / countMax if countMax > 0 else 0.0
            yield agent, value

class Diversity(TimeBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "group_size", metavar = "GROUP_SIZE", type = int, choices = tuple(xrange(8)))
    
    def readArgs(self, args):
        self.groupSize = self.readArg(args, "group_size")
    
    def getKey(self):
        return "diversity-{0}".format(self.groupSize)
    
    def getLabel(self):
        return "Genetic diversity"
    
    def getDataFileName(self):
        return self.getKey() + ".txt.gz"
    
    def readAll(self):
        for line in self.readLines():
            chunks = line.split()
            yield int(chunks[0]), map(float, chunks[1:])
    
    def read(self):
        values = {}
        for timestep, geneValues in self.readAll():
            values[timestep] = sum(geneValues) / len(geneValues)
        return values

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
        return "Entropy"
    
    def aggregate(self, values):
        return numpy.nanmedian(values)

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
        self.addArg(parser, "type", metavar = "TYPE", action = OptionalStoreAction)
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
    
    def getType(self):
        return "Food" if self.type is None else self.type
    
    def getKey(self):
        return "{0}-consumption".format(self.getType().lower())
    
    def getLabel(self):
        return "{0} consumption rate".format(self.getType())
    
    def calculate(self):
        values = collections.defaultdict(float)
        path = os.path.join(self.run, "energy", "consumption.txt")
        for row in utility.getDataTable(path, "FoodConsumption").rows():
            if self.type is None or row["FoodType"] == self.type:
                values[row["Timestep"]] += row["EnergyRaw"]
        for timestep in xrange(1, utility.getFinalTimestep(self.run) + 1):
            yield timestep, values[timestep]

class FoodConsumptionRate(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE", action = OptionalStoreAction)
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
    
    def getType(self):
        return "Food" if self.type is None else self.type
    
    def getKey(self):
        return "{0}-consumption-rate".format(self.getType().lower())
    
    def getLabel(self):
        return "{0} consumption rate".format(self.getType())
    
    def getLifespans(self):
        metric = Lifespan()
        metric.initialize(self.run, start = self.start)
        return metric.read()
    
    def calculate(self):
        values = collections.defaultdict(float)
        path = os.path.join(self.run, "energy", "consumption.txt")
        for row in utility.getDataTable(path, "FoodConsumption").rows():
            if self.type is None or row["FoodType"] == self.type:
                values[row["Agent"]] += row["EnergyRaw"]
        for agent, lifespan in self.getLifespans().iteritems():
            yield agent, float(values[agent]) / lifespan if lifespan > 0 else 0.0

class FoodEnergy(TimeBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE", action = OptionalStoreAction)
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
    
    def getType(self):
        return "Food" if self.type is None else self.type
    
    def getKey(self):
        return "{0}-energy".format(self.getType().lower())
    
    def getLabel(self):
        return "{0} energy".format(self.getType())
    
    def read(self):
        values = {}
        path = os.path.join(self.run, "energy", "food.txt")
        table = utility.getDataTable(path, "FoodEnergy")
        columnName = table.columns()[1].name if self.type is None else self.type
        for row in utility.getDataTable(path, "FoodEnergy").rows():
            values[row["Timestep"]] = row[columnName]
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
        return "{0} gene".format(utility.getGeneTitles(self.run, True)[self.index])
    
    def calculate(self):
        for agent in utility.getAgents(self.run, self.start):
            path = os.path.join(self.run, "genome", "agents", "genome_{0}.txt.gz".format(agent))
            with gzip.open(path) as f:
                for index in xrange(self.index):
                    f.readline()
                yield agent, int(f.readline())
    
    def getBins(self):
        return numpy.linspace(0, 256, 65)

class InfoModification(AgentBasedMetric):
    class Type(utility.Enum):
        TRIVIAL = "Trivial"
        NONTRIVIAL = "Nontrivial"
        TOTAL = "Total"
    
    @staticmethod
    def getTypeLabel(type):
        if type == InfoModification.Type.TRIVIAL:
            return "Positive"
        elif type == InfoModification.Type.NONTRIVIAL:
            return "Negative"
        elif type == InfoModification.Type.TOTAL:
            return ""
        else:
            assert False
    
    def addArgs(self, parser):
        self.addArg(parser, "type", metavar = "TYPE", choices = tuple(InfoModification.Type.getValues()))
        self.addArg(parser, "embedding", metavar = "EMBEDDING", type = int)
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
    
    def readArgs(self, args):
        self.type = self.readArg(args, "type")
        self.embedding = self.readArg(args, "embedding")
        self.stage = self.readArg(args, "stage")
    
    def getKey(self):
        return "info-modification-{0}-{1}-{2}".format(self.type.lower(), self.embedding, self.stage)
    
    def getDataFileName(self):
        return "info-dynamics-{0}-{1}.txt".format(self.embedding, self.stage)
    
    def getLabel(self):
        return "{0} separable information".format(InfoModification.getTypeLabel(self.type)).strip().capitalize()
    
    def read(self):
        values = dict.fromkeys(utility.getAgents(self.run), NAN)
        for line in self.readLines():
            agent, flag, chunks = line.split(None, 2)
            if flag == "M":
                type, count, value = chunks.split()
                if type == self.type:
                    count = int(count)
                    value = float(value)
                    if self.type == InfoModification.Type.NONTRIVIAL:
                        value = -value
                    values[int(agent)] = 0.0 if count == 0 else value / count
        return values

class InfoStorage(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "embedding", metavar = "EMBEDDING", type = int)
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
    
    def readArgs(self, args):
        self.embedding = self.readArg(args, "embedding")
        self.stage = self.readArg(args, "stage")
    
    def getKey(self):
        return "info-storage-{0}-{1}".format(self.embedding, self.stage)
    
    def getDataFileName(self):
        return "info-dynamics-{0}-{1}.txt".format(self.embedding, self.stage)
    
    def getLabel(self):
        return "Active information storage"
    
    def read(self):
        values = dict.fromkeys(utility.getAgents(self.run), NAN)
        for line in self.readLines():
            agent, flag, chunks = line.split(None, 2)
            if flag == "S":
                count, value = chunks.split()
                count = int(count)
                values[int(agent)] = 0.0 if count == 0 else float(value) / count
        return values

class InfoTransferApparent(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "embedding", metavar = "EMBEDDING", type = int)
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
    
    def readArgs(self, args):
        self.embedding = self.readArg(args, "embedding")
        self.stage = self.readArg(args, "stage")
    
    def getKey(self):
        return "info-transfer-apparent-{0}-{1}".format(self.embedding, self.stage)
    
    def getDataFileName(self):
        return "info-dynamics-{0}-{1}.txt".format(self.embedding, self.stage)
    
    def getLabel(self):
        return "Apparent transfer entropy"
    
    def read(self):
        values = dict.fromkeys(utility.getAgents(self.run), NAN)
        for line in self.readLines():
            agent, flag, chunks = line.split(None, 2)
            if flag == "T":
                source, count, value = chunks.split()
                if source == "Total":
                    count = int(count)
                    values[int(agent)] = 0.0 if count == 0 else float(value) / count
        return values

class InfoTransferCollective(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "embedding", metavar = "EMBEDDING", type = int)
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
    
    def readArgs(self, args):
        self.embedding = self.readArg(args, "embedding")
        self.stage = self.readArg(args, "stage")
    
    def getKey(self):
        return "info-transfer-collective-{0}-{1}".format(self.embedding, self.stage)
    
    def getLabel(self):
        return "Collective transfer entropy"
    
    def read(self):
        values = dict.fromkeys(utility.getAgents(self.run), NAN)
        for line in self.readLines():
            agent, count, value = line.split()
            count = int(count)
            values[int(agent)] = 0.0 if count == 0 else float(value) / count
        return values

class InfoTransferComplete(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "embedding", metavar = "EMBEDDING", type = int)
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
    
    def readArgs(self, args):
        self.embedding = self.readArg(args, "embedding")
        self.stage = self.readArg(args, "stage")
    
    def getKey(self):
        return "info-transfer-complete-{0}-{1}".format(self.embedding, self.stage)
    
    def getLabel(self):
        return "Complete transfer entropy"
    
    def read(self):
        values = dict.fromkeys(utility.getAgents(self.run), NAN)
        for line in self.readLines():
            agent, count, value = line.split()
            count = int(count)
            values[int(agent)] = 0.0 if count == 0 else float(value) / count
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
            path = os.path.join(self.run, "brain", "synapses", "synapses_{0}_{1}.txt.gz".format(agent, Stage.BIRTH))
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
            graph = graph_mod.Graph.read(self.run, agent, Stage.BIRTH, self.graphType)
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

class Onset(AgentBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "stage", metavar = "STAGE", choices = tuple(Stage.getValues()))
        self.addArg(parser, "threshold", metavar = "THRESHOLD", type = int)
    
    def readArgs(self, args):
        self.stage = self.readArg(args, "stage")
        self.threshold = self.readArg(args, "threshold")
    
    def getKey(self):
        return "onset-{0}-{1}".format(self.stage, self.threshold)
    
    def getLabel(self):
        return "Onset of criticality"
    
    def aggregate(self, values):
        return numpy.nanmedian(values)

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

class Selection(TimeBasedMetric):
    def addArgs(self, parser):
        self.addArg(parser, "group_size", metavar = "GROUP_SIZE", type = int, choices = tuple(xrange(8)))
        self.addArg(parser, "index_min", metavar = "INDEX_MIN", type = int, action = OptionalStoreAction)
        self.addArg(parser, "index_max", metavar = "INDEX_MAX", type = int, action = OptionalStoreAction)
    
    def readArgs(self, args):
        self.groupSize = self.readArg(args, "group_size")
        self.indexMin = self.readArg(args, "index_min")
        self.indexMax = self.readArg(args, "index_max")
        if self.indexMin is not None:
            assert self.indexMax is not None
    
    def getKey(self):
        if self.indexMin is None:
            return "selection-{0}".format(self.groupSize)
        else:
            return "selection-{0}-{1}-{2}".format(self.groupSize, self.indexMin, self.indexMax)
    
    def getLabel(self):
        return "Evolutionary selection"
    
    def getDiversities(self, passive):
        metric = Diversity()
        metric.groupSize = self.groupSize
        metric.initialize(self.run, passive)
        return metric.readAll()
    
    def calculate(self):
        indexMin = 0 if self.indexMin is None else self.indexMin
        indexMax = utility.getGeneCount(self.run) - 1 if self.indexMax is None else self.indexMax
        driven = self.getDiversities(False)
        passive = self.getDiversities(True)
        for timestep in xrange(utility.getFinalTimestep(self.run) + 1):
            drivenTimestep, drivenValues = next(driven)
            passiveTimestep, passiveValues = next(passive)
            assert drivenTimestep == timestep
            assert passiveTimestep == timestep
            values = []
            for index in xrange(indexMin, indexMax + 1):
                drivenValue = drivenValues[index]
                passiveValue = passiveValues[index]
                values.append(NAN if passiveValue == 0.0 else drivenValue / passiveValue - 1.0)
            yield timestep, numpy.nanmean(values)

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
            values[agent] = localValue * globalValue
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
            graph = graph_mod.Graph.read(self.run, agent, Stage.BIRTH, self.graphType)
            yield agent, graph.getLinkCount()

class Timestep(TimeBasedMetric):
    integral = True
    
    def getKey(self):
        return "time"
    
    def getLabel(self):
        return "Timestep"
    
    def read(self):
        values = {}
        for timestep in xrange(utility.getFinalTimestep(self.run) + 1):
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
