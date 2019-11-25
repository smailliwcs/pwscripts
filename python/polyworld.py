import enum
import gzip
import os

import datalib


class Stage(enum.Enum):
    INCEPTION = "incept"
    BIRTH = "birth"
    DEATH = "death"


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


def run_exists(path):
    return os.path.exists(os.path.join(path, "endStep.txt"))


def get_agent_count(run):
    return datalib.parse_digest(os.path.join(run, "lifespans.txt"))["tables"]["LifeSpans"]["nrows"]


def get_agents(run):
    return range(1, get_agent_count(run) + 1)
