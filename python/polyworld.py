import collections
import enum
import gzip
import os

import datalib


class Stage(enum.Enum):
    INCEPTION = "incept"
    BIRTH = "birth"
    DEATH = "death"


class Event:
    class Type(enum.Enum):
        BIRTH = "BIRTH"
        CREATION = "CREATION"
        VIRTUAL = "VIRTUAL"
        DEATH = "DEATH"

    @staticmethod
    def read(run):
        with read_file(os.path.join(run, "BirthsDeaths.log")) as f:
            f.readline()
            for line in f:
                chunks = line.split()
                time = int(chunks[0])
                type_ = Event.Type(chunks[1])
                agent = int(chunks[2])
                parents = None
                if type_ == Event.Type.BIRTH or type_ == Event.Type.VIRTUAL:
                    parents = {int(chunks[3]), int(chunks[4])}
                yield Event(time, type_, agent, parents)

    def __init__(self, time, type_, agent, parents=None):
        self.time = time
        self.type = type_
        self.agent = agent
        self.parents = parents


GZIP_EXTENSION = ".gz"


def file_exists(path):
    return os.path.exists(path) or os.path.exists(path + GZIP_EXTENSION)


def read_file(path):
    if os.path.exists(path):
        return open(path)
    gzip_path = path + GZIP_EXTENSION
    if os.path.exists(gzip_path):
        return gzip.open(gzip_path, "rt")
    raise FileNotFoundError


def read_data(path, table_name):
    return datalib.parse(path, (table_name,), True)[table_name]


def run_exists(path):
    return os.path.exists(os.path.join(path, "endStep.txt"))


def get_agent_count(run):
    return datalib.parse_digest(os.path.join(run, "lifespans.txt"))["tables"]["LifeSpans"]["nrows"]


def get_initial_agent_count(run):
    data = read_data(os.path.join(run, "lifespans.txt"), "LifeSpans")
    return sum(1 for row in data.rows() if row["BirthReason"] == "SIMINIT")


def get_final_time(run):
    with open(os.path.join(run, "endStep.txt")) as f:
        return int(f.readline())


def get_populations(run):
    agents = set(range(1, get_initial_agent_count(run) + 1))
    events = collections.defaultdict(list)
    for event in Event.read(run):
        events[event.time].append(event)
    for time in range(0, get_final_time(run) + 1):
        for event in events[time]:
            if event.type == Event.Type.BIRTH or event.type == Event.Type.CREATION:
                agents.add(event.agent)
            elif event.type == Event.Type.DEATH:
                agents.remove(event.agent)
        yield time, agents
