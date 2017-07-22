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

class Event(object):
    class Type(Enum):
        BIRTH = "BIRTH"
        DEATH = "DEATH"
    
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
        self.type = Event.Type.parse(chunks[1])
        self.agent = int(chunks[2])
        if self.type == Event.Type.BIRTH:
            self.parent1 = int(chunks[3])
            self.parent2 = int(chunks[4])

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

def getAgents(run):
    return xrange(1, getAgentCount(run) + 1)
