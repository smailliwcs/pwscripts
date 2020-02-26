import gzip
import os

import datalib

from . import paths


def open_file(path):
    if os.path.exists(path):
        return open(path)
    gzip_path = f"{path}.gz"
    if os.path.exists(gzip_path):
        return gzip.open(gzip_path, "rt")
    raise FileNotFoundError


def parse_data(path, table_name):
    return datalib.parse(path, (table_name,), True)[table_name]


def run_exists(path):
    return os.path.exists(paths.end_time(path))


def get_initial_agent_count(run):
    data = parse_data(paths.lifespans(run), "LifeSpans")
    return sum(1 for row in data.rows() if row["BirthReason"] == "SIMINIT")


def get_initial_agents(run):
    return range(1, get_initial_agent_count(run) + 1)


def get_agent_count(run):
    return datalib.parse_digest(paths.lifespans(run))["tables"]["LifeSpans"]["nrows"]


def get_agents(run):
    return range(1, get_agent_count(run) + 1)


def get_end_time(run):
    with open(paths.end_time(run)) as f:
        return int(f.readline())


def get_times(run):
    return range(0, get_end_time(run) + 1)
