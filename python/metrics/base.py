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
    index_name = None
    aggregator = np.nanmean

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("run", metavar="RUN", type=parse_run_arg)
        parser.add_argument("metric", metavar=cls.__name__)

    @classmethod
    def to_series(cls, observations, index_name=None):
        if index_name is None:
            index_name = cls.index_name
        series = pd.Series(dict(observations), name="value")
        series.index.name = index_name
        return series

    @classmethod
    @abc.abstractmethod
    def _group(cls, run, series):
        raise NotImplementedError

    @classmethod
    def _aggregate(cls, run, series, function, step):
        buffer = []
        for time, values in cls._group(run, series):
            buffer.extend(values)
            if time % step == 0:
                yield time, function(buffer)
                buffer.clear()

    @classmethod
    def aggregate(cls, run, series, function=None, step=1):
        if function is None:
            function = cls.aggregator
        return cls.to_series(cls._aggregate(run, series, function, step), "time")

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
        return self.to_series(self._calculate())

    def _write_arguments(self, file):
        pass

    def write(self, file, series):
        self._write_arguments(file)
        series.to_csv(file, sep=" ", na_rep=str(math.nan), header=True)


class PopulationMetric(Metric, abc.ABC):
    index_name = "time"

    @classmethod
    def _group(cls, run, series):
        for time in pw.get_times(run):
            yield time, (series.get(time, math.nan),)


class IndividualMetric(Metric, abc.ABC):
    index_name = "agent"

    @classmethod
    def _group(cls, run, series):
        values = {}
        for agent in pw.get_initial_agents(run):
            values[agent] = series.get(agent, math.nan)
        events = pw.get_events(run)
        for time in pw.get_times(run):
            for event in events[time]:
                if event.type.adds_agent():
                    values[event.agent] = series.get(event.agent, math.nan)
                if event.type.removes_agent():
                    del values[event.agent]
            yield time, values.values()

    @abc.abstractmethod
    def _get_value(self, agent):
        raise NotImplementedError

    def _calculate(self):
        for agent in pw.get_agents(self.run):
            yield agent, self._get_value(agent)
