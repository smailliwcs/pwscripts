import datalib
import os
import random

class Enum(object):
    @classmethod
    def getAll(cls):
        for attrName in dir(cls):
            if attrName.startswith("__"):
                continue
            attr = getattr(cls, attrName)
            if not callable(attr):
                yield attr
    
    def __init__(self):
        raise NotImplementedError

class Event(object):
    class Type(Enum):
        BIRTH = "BIRTH"
        DEATH = "DEATH"
    
    def __init__(self, line):
        chunks = line.split()
        self.timestep = int(chunks[0])
        self.type = chunks[1]
        self.agent = int(chunks[2])
        if self.type == Event.Type.BIRTH:
            self.parent1 = int(chunks[3])
            self.parent2 = int(chunks[4])

def getAgentCount(run):
    return datalib.parse_digest(os.path.join(run, "lifespans.txt"))["tables"]["LifeSpans"]["nrows"]

def getDataTable(path, tableName):
    return datalib.parse(path, [tableName], True)[tableName]

def getFinalTimestep(run):
    with open(os.path.join(run, "endStep.txt")) as f:
        return int(f.readline().strip())

def getInitialAgentCount(run):
    return int(getWorldfileParameter(run, "InitAgents"))

def getWorldfileParameter(run, parameterName):
    with open(os.path.join(run, "normalized.wf")) as f:
        for line in f:
            strippedLine = line.strip()
            if strippedLine.startswith("#"):
                continue
            chunks = strippedLine.split()
            if len(chunks) >= 2 and chunks[0] == parameterName:
                return chunks[1]

def isRun(path):
    return os.path.isfile(os.path.join(path, "endStep.txt"))

def iterateAgents(run):
    return xrange(1, getAgentCount(run) + 1)

def iterateEvents(run):
    with open(os.path.join(run, "BirthsDeaths.log")) as f:
        for timestep in iterateTimesteps(run):
            events = []
            while True:
                position = f.tell()
                line = f.readline()
                if line == "":
                    break
                if line.startswith("%"):
                    continue
                event = Event(line)
                if event.timestep == timestep:
                    events.append(event)
                else:
                    f.seek(position)
                    break
            yield timestep, events

def iterateInitialAgents(run):
    return xrange(1, getInitialAgentCount(run) + 1)

def iterateNonInitialAgents(run):
    return xrange(getInitialAgentCount(run) + 1, getAgentCount(run) + 1)

def iteratePopulations(run):
    agents = []
    for agent in iterateInitialAgents(run):
        agents.append(agent)
    yield 0, agents
    for timestep, events in iterateEvents(run):
        for event in events:
            if event.type == Event.Type.BIRTH:
                agents.append(event.agent)
            elif event.type == Event.Type.DEATH:
                agents.remove(event.agent)
            else:
                assert False
        yield timestep, agents

def iterateTimesteps(run):
    return xrange(1, getFinalTimestep(run) + 1)

def makeDirectories(path):
    if not os.path.isdir(path):
        os.makedirs(path, 0755)

def shuffled(seq):
    seqList = list(seq)
    random.shuffle(seqList)
    return seqList
