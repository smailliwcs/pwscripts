import collections
import enum

from . import paths
from . import utility


class Event:
    class Type(enum.Enum):
        BIRTH = "BIRTH"
        CREATION = "CREATION"
        VIRTUAL = "VIRTUAL"
        DEATH = "DEATH"

        def adds_agent(self):
            return self in {self.BIRTH, self.CREATION}

        def removes_agent(self):
            return self is self.DEATH

        def has_parents(self):
            return self in {self.BIRTH, self.VIRTUAL}

    @classmethod
    def parse(cls, line):
        chunks = line.split()
        time = int(chunks[0])
        type_ = Event.Type(chunks[1])
        agent = int(chunks[2])
        parents = None
        if type_.has_parents():
            parents = {
                int(chunks[3]),
                int(chunks[4])
            }
        return cls(time, type_, agent, parents)

    @classmethod
    def read(cls, run):
        with utility.open(paths.events(run)) as f:
            f.readline()
            for line in f:
                yield cls.parse(line)

    def __init__(self, time, type_, agent, parents):
        self.time = time
        self.type = type_
        self.agent = agent
        self.parents = parents


def get_events(run):
    events = collections.defaultdict(list)
    for event in Event.read(run):
        events[event.time].append(event)
    return events


def get_populations(run):
    agents = set(utility.get_initial_agents(run))
    events = get_events(run)
    for time in utility.get_times(run):
        for event in events[time]:
            if event.type.adds_agent():
                agents.add(event.agent)
            if event.type.removes_agent():
                agents.remove(event.agent)
        yield time, agents
