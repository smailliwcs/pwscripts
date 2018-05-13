import collections
import datalib
import os
import random

class Enum(object):
    @classmethod
    def getValues(cls):
        for name in dir(cls):
            if name.startswith("__"):
                continue
            value = getattr(cls, name)
            if not callable(value):
                yield value
    
    @classmethod
    def parse(cls, value):
        if value in cls.getValues():
            return value
        else:
            raise ValueError
    
    def __init__(self):
        raise NotImplementedError

class EventType(Enum):
    BIRTH = "BIRTH"
    DEATH = "DEATH"
    VIRTUAL = "VIRTUAL"

class Event(object):
    @staticmethod
    def read(run):
        with open(os.path.join(run, "BirthsDeaths.log")) as f:
            for line in f:
                if line.startswith("%"):
                    continue
                yield Event(line)
    
    def __init__(self, line):
        chunks = line.split()
        self.timestep = int(chunks[0])
        self.eventType = EventType.parse(chunks[1])
        self.agent = int(chunks[2])
        if self.eventType == EventType.BIRTH or self.eventType == EventType.VIRTUAL:
            self.parent1 = int(chunks[3])
            self.parent2 = int(chunks[4])

def contains(ival, value):
    if ival[0] is not None and value < ival[0]:
        return False
    elif ival[1] is not None and value > ival[1]:
        return False
    else:
        return True

def coalesce(*values):
    for value in values:
        if value is not None:
            return value
    return None

def iterate(values):
    if values is None:
        return
    if hasattr(values, "__iter__"):
        for value in values:
            yield value
    else:
        yield values

def shuffled(iterable):
    result = list(iterable)
    random.shuffle(result)
    return result

def getSubdirectories(path):
    for name in os.listdir(path):
        subpath = os.path.join(path, name)
        if os.path.isdir(subpath):
            yield subpath

def makeDirectories(path, mode = 0755):
    try:
        os.makedirs(path, mode)
    except OSError:
        if not os.path.isdir(path):
            raise

def isRun(path):
    return os.path.isfile(os.path.join(path, "endStep.txt"))

def getRuns(path):
    if isRun(path):
        yield path
    else:
        for subpath in getSubdirectories(path):
            if isRun(subpath):
                yield subpath

def getRun(run, passive):
    return run.replace("driven", "passive") if passive else run

def getKey(run):
    return os.path.basename(os.path.realpath(run))

def getParameter(run, name):
    with open(os.path.join(run, "normalized.wf")) as f:
        for line in f:
            if line.strip().startswith("#"):
                continue
            chunks = line.split()
            if len(chunks) >= 2 and chunks[0] == name:
                return chunks[1]

def getDataTable(path, name):
    return datalib.parse(path, [name], True)[name]

def getFinalTimestep(run):
    with open(os.path.join(run, "endStep.txt")) as f:
        return int(f.readline())

def getAgentCount(run):
    return datalib.parse_digest(os.path.join(run, "lifespans.txt"))["tables"]["LifeSpans"]["nrows"]

def getInitialAgentCount(run):
    return int(getParameter(run, "InitAgents"))

def getAgents(run, start = None):
    start = 1 if start is None else start
    assert start >= 1
    return xrange(start, getAgentCount(run) + 1)

def getPopulations(run):
    agents = range(1, getInitialAgentCount(run) + 1)
    events = collections.defaultdict(list)
    for event in Event.read(run):
        events[event.timestep].append(event)
    for timestep in xrange(getFinalTimestep(run) + 1):
        for event in events[timestep]:
            if event.eventType == EventType.BIRTH:
                agents.append(event.agent)
            elif event.eventType == EventType.DEATH:
                agents.remove(event.agent)
        yield timestep, agents
