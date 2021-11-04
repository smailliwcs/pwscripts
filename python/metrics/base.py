import abc
import argparse
import math
import re

import numpy as np
import pandas as pd

import polyworld as pw


class Range:
    @staticmethod
    def parse(text):
        def convert(value):
            if value == "":
                return None
            return int(value)

        values = text.split("..")
        if len(values) != 2:
            raise ValueError
        return Range(convert(values[0]), convert(values[1]))

    def __init__(self, min_, max_):
        self.min = min_
        self.max = max_

    def __contains__(self, value):
        return (self.min is None or value >= self.min) and (self.max is None or value <= self.max)

    def __iter__(self):
        return range(self.min, self.max + 1).__iter__()

    def is_finite(self):
        return self.min is not None and self.max is not None


def parse_run_arg(arg):
    if not pw.run_exists(arg):
        raise argparse.ArgumentTypeError(f"invalid run: '{arg}'")
    return arg


def parse_range_arg(arg):
    try:
        return Range.parse(arg)
    except Exception as ex:
        raise argparse.ArgumentTypeError(f"invalid range: '{arg}'") from ex


def parse_regex_arg(arg):
    try:
        return re.compile(arg)
    except re.error as ex:
        raise argparse.ArgumentTypeError(f"invalid regex: '{arg}'") from ex


class Metric(abc.ABC):
    has_run_arg = True
    index_name = None
    aggregator = np.nanmean

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument("metric", metavar=cls.__name__)
        if cls.has_run_arg:
            parser.add_argument("run", metavar="RUN", type=parse_run_arg)

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
    def read(cls, file, **kwargs):
        default_kwargs = {
            "sep": " ",
            "index_col": 0,
            "squeeze": True,
            "comment": "#"
        }
        return pd.read_csv(file, **{**default_kwargs, **kwargs})

    def __init__(self, **kwargs):
        self.arguments = kwargs
        if self.has_run_arg:
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
