import abc
import argparse
import math
import re

import numpy as np
import pandas as pd

import polyworld as pw


def parse_run_arg(arg):
    if not pw.run_exists(arg):
        raise argparse.ArgumentTypeError(f"not a Polyworld run: '{arg}'")
    return arg


def parse_regex_arg(arg):
    try:
        return re.compile(arg)
    except re.error as err:
        raise argparse.ArgumentTypeError(err.msg)


class Metric(abc.ABC):
    index_label = None
    value_label = "value"

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("run", metavar="RUN", type=parse_run_arg)
        parser.add_argument("metric", metavar=cls.__name__)

    @classmethod
    def read(cls, file):
        return pd.read_csv(file, sep=" ", index_col=0, squeeze=True, comment="#")

    def __init__(self, **kwargs):
        self.arguments = kwargs
        self.run = kwargs["run"]

    @abc.abstractmethod
    def _calculate(self):
        raise NotImplementedError

    def calculate(self):
        values = pd.Series(dict(self._calculate()), name=self.value_label)
        values.index.name = self.index_label
        return values

    def _write_arguments(self, file):
        pass

    def write(self, file, values):
        self._write_arguments(file)
        values.to_csv(file, sep=" ", na_rep=str(math.nan), header=True)


class PopulationMetric(Metric, abc.ABC):
    index_label = "time"


class IndividualMetric(Metric, abc.ABC):
    index_label = "agent"

    @abc.abstractmethod
    def _get_value(self, agent):
        raise NotImplementedError

    def _calculate(self):
        for agent in pw.get_agents(self.run):
            yield agent, self._get_value(agent)


class Aggregator(PopulationMetric):
    class ValueBuffer:
        def __init__(self, values):
            self.values = values
            self.buffer = {}

        def add(self, agent):
            self.buffer[agent] = self.values.get(agent, math.nan)

        def remove(self, agent):
            del self.buffer[agent]

        def to_array(self):
            return np.array(tuple(self.buffer.values()))

    def __init__(self, run, values, function=np.nanmean):
        super().__init__(run=run)
        self.values = values
        self.function = function

    def _calculate(self):
        buffer = self.ValueBuffer(self.values)
        for agent in pw.get_initial_agents(self.run):
            buffer.add(agent)
        events = pw.get_events(self.run)
        for time in pw.get_times(self.run):
            for event in events[time]:
                if event.type.adds_agent():
                    buffer.add(event.agent)
                if event.type.removes_agent():
                    buffer.remove(event.agent)
            yield time, self.function(buffer.to_array())
